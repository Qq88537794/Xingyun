"""
Agent工具系统
定义后端可执行的工具，用于文档操作
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """工具执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ToolCall:
    """工具调用记录"""
    id: str                        # 调用ID
    name: str                      # 工具名称
    arguments: Dict[str, Any]      # 调用参数
    status: ToolStatus = ToolStatus.PENDING
    result: Optional[Any] = None   # 执行结果
    error: Optional[str] = None    # 错误信息
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'arguments': self.arguments,
            'status': self.status.value,
            'result': self.result,
            'error': self.error
        }


@dataclass
class ToolDefinition:
    """
    工具定义 - 转换为LLM可理解的格式
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema格式
    
    def to_llm_format(self) -> Dict[str, Any]:
        """转换为LLM工具调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class BaseTool(ABC):
    """工具基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述 - 用于提示词"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """参数定义 - JSON Schema格式"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    def get_definition(self) -> ToolDefinition:
        """获取工具定义"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )


# ============== 文档操作工具 ==============

class ReadDocumentTool(BaseTool):
    """读取文档内容"""
    
    def __init__(self, document_provider: Callable[[str], Optional[str]]):
        """
        Args:
            document_provider: 获取文档内容的函数 (doc_id) -> content
        """
        self._get_document = document_provider
    
    @property
    def name(self) -> str:
        return "read_document"
    
    @property
    def description(self) -> str:
        return """读取指定文档的内容。使用此工具来查看文档全文或了解文档结构。
在修改文档之前，应该先读取文档内容。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "文档ID"
                }
            },
            "required": ["document_id"]
        }
    
    def execute(self, document_id: str, **kwargs) -> Dict[str, Any]:
        content = self._get_document(document_id)
        if content is None:
            return {"success": False, "error": f"文档不存在: {document_id}"}
        return {"success": True, "content": content, "length": len(content)}


class WriteDocumentTool(BaseTool):
    """覆盖写入文档（创建新文档或完全替换）"""
    
    def __init__(self, document_writer: Callable[[str, str], bool]):
        """
        Args:
            document_writer: 写入文档的函数 (doc_id, content) -> success
        """
        self._write_document = document_writer
    
    @property
    def name(self) -> str:
        return "write_document"
    
    @property
    def description(self) -> str:
        return """完全覆盖或创建文档。仅在需要创建新文档或完全重写时使用。
对于局部修改，应使用 edit_document 工具。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "文档ID（新建时可为空）"
                },
                "content": {
                    "type": "string",
                    "description": "完整的文档内容"
                }
            },
            "required": ["content"]
        }
    
    def execute(self, content: str, document_id: str = None, **kwargs) -> Dict[str, Any]:
        success = self._write_document(document_id, content)
        if success:
            return {"success": True, "document_id": document_id, "message": "文档已保存"}
        return {"success": False, "error": "保存文档失败"}


class EditDocumentTool(BaseTool):
    """编辑文档的指定部分"""
    
    def __init__(
        self,
        document_provider: Callable[[str], Optional[str]],
        document_writer: Callable[[str, str], bool]
    ):
        self._get_document = document_provider
        self._write_document = document_writer
    
    @property
    def name(self) -> str:
        return "edit_document"
    
    @property
    def description(self) -> str:
        return """编辑文档的指定部分。支持以下操作：
- insert: 在指定位置插入内容
- replace: 替换指定范围的内容
- delete: 删除指定范围的内容

使用此工具进行精确的局部修改，而不是重写整个文档。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "文档ID"
                },
                "action": {
                    "type": "string",
                    "enum": ["insert", "replace", "delete"],
                    "description": "操作类型"
                },
                "position": {
                    "type": "integer",
                    "description": "操作起始位置（字符索引）"
                },
                "end_position": {
                    "type": "integer",
                    "description": "结束位置（用于replace和delete）"
                },
                "content": {
                    "type": "string",
                    "description": "要插入或替换的内容"
                }
            },
            "required": ["document_id", "action", "position"]
        }
    
    def execute(
        self,
        document_id: str,
        action: str,
        position: int,
        end_position: int = None,
        content: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        # 读取原文档
        original = self._get_document(document_id)
        if original is None:
            return {"success": False, "error": f"文档不存在: {document_id}"}
        
        # 执行编辑
        if action == "insert":
            new_content = original[:position] + content + original[position:]
        elif action == "replace":
            end = end_position or (position + len(content))
            new_content = original[:position] + content + original[end:]
        elif action == "delete":
            end = end_position or position
            new_content = original[:position] + original[end:]
        else:
            return {"success": False, "error": f"未知操作: {action}"}
        
        # 保存
        success = self._write_document(document_id, new_content)
        if success:
            return {
                "success": True,
                "action": action,
                "position": position,
                "message": f"已{action}内容"
            }
        return {"success": False, "error": "保存失败"}


class SearchDocumentTool(BaseTool):
    """在文档中搜索内容"""
    
    def __init__(self, document_provider: Callable[[str], Optional[str]]):
        self._get_document = document_provider
    
    @property
    def name(self) -> str:
        return "search_document"
    
    @property
    def description(self) -> str:
        return """在文档中搜索指定内容，返回匹配位置和上下文。
用于定位需要修改的内容位置。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "文档ID"
                },
                "query": {
                    "type": "string",
                    "description": "搜索内容"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回结果数",
                    "default": 5
                }
            },
            "required": ["document_id", "query"]
        }
    
    def execute(
        self,
        document_id: str,
        query: str,
        max_results: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        content = self._get_document(document_id)
        if content is None:
            return {"success": False, "error": f"文档不存在: {document_id}"}
        
        results = []
        start = 0
        while len(results) < max_results:
            pos = content.find(query, start)
            if pos == -1:
                break
            
            # 提取上下文（前后50字符）
            ctx_start = max(0, pos - 50)
            ctx_end = min(len(content), pos + len(query) + 50)
            context = content[ctx_start:ctx_end]
            
            results.append({
                "position": pos,
                "context": context,
                "match": query
            })
            start = pos + 1
        
        return {
            "success": True,
            "matches": len(results),
            "results": results
        }


class GenerateOutlineTool(BaseTool):
    """生成文档大纲"""
    
    @property
    def name(self) -> str:
        return "generate_outline"
    
    @property
    def description(self) -> str:
        return """根据主题和要求生成文档大纲结构。
返回大纲后，用户可以决定是否应用到文档。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "文档主题"
                },
                "requirements": {
                    "type": "string",
                    "description": "具体要求和约束"
                },
                "depth": {
                    "type": "integer",
                    "description": "大纲层级深度",
                    "default": 3
                }
            },
            "required": ["topic"]
        }
    
    def execute(self, topic: str, requirements: str = "", depth: int = 3, **kwargs) -> Dict[str, Any]:
        # 这个工具的实际执行需要调用LLM，这里返回一个标记
        # 实际的大纲生成在Agent循环中由LLM完成
        return {
            "success": True,
            "type": "outline_request",
            "topic": topic,
            "requirements": requirements,
            "depth": depth,
            "message": "请基于以上参数生成大纲"
        }


class ExpandContentTool(BaseTool):
    """扩写内容"""
    
    @property
    def name(self) -> str:
        return "expand_content"
    
    @property
    def description(self) -> str:
        return """扩展和丰富指定的内容段落。
可以指定扩展倍数和重点方向。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "需要扩展的内容"
                },
                "ratio": {
                    "type": "number",
                    "description": "扩展倍数（如2表示扩展到2倍长度）",
                    "default": 2
                },
                "focus": {
                    "type": "string",
                    "description": "扩展的重点方向"
                }
            },
            "required": ["content"]
        }
    
    def execute(self, content: str, ratio: float = 2, focus: str = "", **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "type": "expand_request",
            "content": content,
            "ratio": ratio,
            "focus": focus,
            "message": "请扩写以上内容"
        }


class SummarizeTool(BaseTool):
    """生成摘要"""
    
    @property
    def name(self) -> str:
        return "summarize"
    
    @property
    def description(self) -> str:
        return """为指定内容生成摘要。
可以指定摘要长度和侧重点。"""
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "需要摘要的内容"
                },
                "max_length": {
                    "type": "integer",
                    "description": "摘要最大字数",
                    "default": 200
                },
                "focus_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "重点关注的方面"
                }
            },
            "required": ["content"]
        }
    
    def execute(self, content: str, max_length: int = 200, focus_points: List[str] = None, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "type": "summarize_request",
            "content": content,
            "max_length": max_length,
            "focus_points": focus_points or [],
            "message": "请生成摘要"
        }


# ============== 工具注册表 ==============

class ToolRegistry:
    """
    工具注册表
    管理所有可用工具，转换为LLM格式
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
    
    def unregister(self, name: str):
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名"""
        return list(self._tools.keys())
    
    def get_definitions(self) -> List[ToolDefinition]:
        """获取所有工具定义"""
        return [tool.get_definition() for tool in self._tools.values()]
    
    def to_llm_tools(self) -> List[Dict[str, Any]]:
        """转换为LLM工具格式"""
        return [defn.to_llm_format() for defn in self.get_definitions()]
    
    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具"""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"工具不存在: {name}")
        return tool.execute(**arguments)
    
    def build_tools_prompt(self) -> str:
        """构建工具使用提示词"""
        lines = ["## 可用工具\n"]
        
        for tool in self._tools.values():
            lines.append(f"### {tool.name}")
            lines.append(tool.description)
            lines.append("")
        
        return "\n".join(lines)


def create_default_registry(
    document_provider: Callable[[str], Optional[str]],
    document_writer: Callable[[str, str], bool]
) -> ToolRegistry:
    """
    创建默认工具注册表
    
    Args:
        document_provider: 获取文档内容的函数
        document_writer: 写入文档的函数
    """
    registry = ToolRegistry()
    
    # 注册文档操作工具
    registry.register(ReadDocumentTool(document_provider))
    registry.register(WriteDocumentTool(document_writer))
    registry.register(EditDocumentTool(document_provider, document_writer))
    registry.register(SearchDocumentTool(document_provider))
    
    # 注册内容生成工具
    registry.register(GenerateOutlineTool())
    registry.register(ExpandContentTool())
    registry.register(SummarizeTool())
    
    return registry
