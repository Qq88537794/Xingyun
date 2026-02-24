"""
AI模块统一数据结构定义
定义AI请求和响应的POJO格式
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json


class OperationType(Enum):
    """文件操作类型"""
    NONE = "none"                      # 无操作，仅回复
    GENERATE_OUTLINE = "generate_outline"        # 生成大纲
    EXPAND_CONTENT = "expand_content"            # 扩写内容
    SUMMARIZE = "summarize"                      # 生成摘要
    STYLE_TRANSFER = "style_transfer"            # 风格迁移
    GRAMMAR_CHECK = "grammar_check"              # 语法检查
    INSERT_TEXT = "insert_text"                  # 插入文本
    REPLACE_TEXT = "replace_text"                # 替换文本（局部）
    REPLACE = "replace"                          # 全量替换（Agent模式）
    DELETE_TEXT = "delete_text"                  # 删除文本
    FORMAT_TEXT = "format_text"                  # 格式化文本


@dataclass
class FileOperation:
    """
    文件操作指令
    描述AI建议对文档执行的具体操作
    """
    operation_type: OperationType          # 操作类型
    target_file: Optional[str] = None      # 目标文件ID/路径
    content: str = ""                      # 操作内容（新内容/替换内容）
    position: Optional[Dict[str, Any]] = None  # 操作位置 {"start": 0, "end": 100} 或 {"line": 5}
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'operation_type': self.operation_type.value,
            'target_file': self.target_file,
            'content': self.content,
            'position': self.position,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileOperation':
        return cls(
            operation_type=OperationType(data.get('operation_type', 'none')),
            target_file=data.get('target_file'),
            content=data.get('content', ''),
            position=data.get('position'),
            metadata=data.get('metadata', {})
        )


@dataclass
class AIResponse:
    """
    AI统一响应格式
    包含说明内容和可选的文件操作
    """
    # 说明内容 - AI对用户的回复说明
    message: str
    
    # 文件操作列表 - AI建议的文档操作
    operations: List[FileOperation] = field(default_factory=list)
    
    # RAG来源 - 如果使用了知识库检索
    sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # 会话信息
    session_id: Optional[str] = None
    
    # Token使用统计
    tokens_used: int = 0
    
    # 是否需要用户确认操作
    requires_confirmation: bool = True
    
    # 是否已自动执行（auto_execute模式下为True）
    auto_executed: bool = False
    
    # 自动执行后的文档内容（仅在auto_execute=True时返回）
    executed_content: Optional[str] = None
    
    # 额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'message': self.message,
            'operations': [op.to_dict() for op in self.operations],
            'sources': self.sources,
            'session_id': self.session_id,
            'tokens_used': self.tokens_used,
            'requires_confirmation': self.requires_confirmation,
            'auto_executed': self.auto_executed,
            'metadata': self.metadata
        }
        
        # 只在自动执行时返回executed_content
        if self.auto_executed and self.executed_content is not None:
            result['executed_content'] = self.executed_content
        
        return result
    
    def has_operations(self) -> bool:
        """是否包含文件操作"""
        return len(self.operations) > 0 and any(
            op.operation_type != OperationType.NONE for op in self.operations
        )
    
    @classmethod
    def simple_reply(cls, message: str, session_id: str = None, tokens_used: int = 0) -> 'AIResponse':
        """创建简单回复（无操作）"""
        return cls(
            message=message,
            session_id=session_id,
            tokens_used=tokens_used,
            requires_confirmation=False
        )
    
    @classmethod
    def with_operation(
        cls, 
        message: str, 
        operation: FileOperation,
        session_id: str = None,
        tokens_used: int = 0
    ) -> 'AIResponse':
        """创建带单个操作的回复"""
        return cls(
            message=message,
            operations=[operation],
            session_id=session_id,
            tokens_used=tokens_used,
            requires_confirmation=True
        )


@dataclass
class AIRequest:
    """
    AI统一请求格式
    """
    # 用户输入
    message: str
    
    # 会话ID（用于多轮对话）
    session_id: Optional[str] = None
    
    # 项目ID（用于关联知识库）
    project_id: Optional[int] = None
    
    # 当前文档内容（用于文档操作）
    document_content: Optional[str] = None
    
    # 当前文档ID
    document_id: Optional[str] = None
    
    # 选中的文本（用于局部操作）
    selected_text: Optional[str] = None
    
    # 选中文本的位置
    selection_range: Optional[Dict[str, int]] = None  # {"start": 0, "end": 100}
    
    # 是否启用RAG（默认自动根据项目知识库决定）
    enable_rag: Optional[bool] = None
    
    # 是否启用Agent模式（工具调用循环）
    enable_agent: bool = False
    
    # 是否自动执行文档操作（无需用户确认）
    auto_execute: bool = False
    
    # 是否启用流式响应
    stream: bool = False
    
    # 额外参数
    options: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIRequest':
        return cls(
            message=data.get('message', ''),
            session_id=data.get('session_id'),
            project_id=data.get('project_id'),
            document_content=data.get('document_content'),
            document_id=data.get('document_id'),
            selected_text=data.get('selected_text'),
            selection_range=data.get('selection_range'),
            enable_rag=data.get('enable_rag'),
            enable_agent=data.get('enable_agent', False),
            auto_execute=data.get('auto_execute', False),
            stream=data.get('stream', False),
            options=data.get('options', {})
        )


# ============== 系统提示词模板 ==============

SYSTEM_PROMPT_TEMPLATE = """你是行云智能文档工作站的AI助手，专注于帮助用户进行文档创作和内容优化。

## 核心能力
- 回答问题，提供专业建议
- 生成文档大纲、扩写内容、生成摘要
- 风格迁移、语法检查

## 回复要求
直接用清晰的中文回答，不要使用JSON、代码块等技术格式。

## 大纲生成要求（非常重要）
生成大纲时必须简洁清晰，格式如下：

1. 主标题
1.1 子标题
1.2 子标题
2. 主标题
2.1 子标题
2.2 子标题

**要求：**
- 标题要简洁、概括性强，直接提炼核心要点
- 层级不要超过3层（如 1.1.1）
- 不要添加任何额外标记、注释或原文引用
- 准确归纳文档内容，避免过于细碎
- 每个标题应该能代表文档中的一个主要段落或章节

{% if has_knowledge_base %}
## 参考资料
{{rag_context}}
{% endif %}

{% if document_content %}
## 当前文档
{{document_content}}
{% if selected_text %}
选中文本：{{selected_text}}
{% endif %}
{% endif %}
"""


def build_system_prompt(
    has_knowledge_base: bool = False,
    rag_context: str = "",
    document_content: str = None,
    selected_text: str = None
) -> str:
    """构建系统提示词"""
    import re
    from .utils.document_compressor import compress_document_for_outline
    
    prompt = SYSTEM_PROMPT_TEMPLATE
    
    # 处理 has_knowledge_base 条件
    if has_knowledge_base:
        prompt = prompt.replace("{% if has_knowledge_base %}", "")
        prompt = prompt.replace("{{rag_context}}", rag_context or "")
        # 移除第一个 {% endif %}
        prompt = prompt.replace("{% endif %}", "", 1)
    else:
        # 移除整个 knowledge_base 块
        prompt = re.sub(r'\{% if has_knowledge_base %\}.*?\{% endif %\}', '', prompt, flags=re.DOTALL)
    
    # 处理 document_content 条件
    if document_content:
        prompt = prompt.replace("{% if document_content %}", "")
        
        # 使用智能压缩，支持更长文档
        # 对于超长文档，会提取标题和关键内容，保留完整结构
        compressed_content = compress_document_for_outline(document_content, max_length=12000)
        prompt = prompt.replace("{{document_content}}", compressed_content)
        
        # 处理 selected_text 条件
        if selected_text:
            prompt = prompt.replace("{% if selected_text %}", "")
            prompt = prompt.replace("{{selected_text}}", selected_text)
            # 移除 selected_text 的 {% endif %}
            prompt = prompt.replace("{% endif %}", "", 1)
        else:
            # 移除 selected_text 块
            prompt = re.sub(r'\{% if selected_text %\}.*?\{% endif %\}', '', prompt, flags=re.DOTALL)
        
        # 移除 document_content 的 {% endif %}
        prompt = prompt.replace("{% endif %}", "", 1)
    else:
        # 移除整个 document_content 块
        prompt = re.sub(r'\{% if document_content %\}.*?\{% endif %\}', '', prompt, flags=re.DOTALL)
    
    # 清理可能残留的模板标记
    prompt = re.sub(r'\{%.*?%\}', '', prompt)
    prompt = re.sub(r'\{\{.*?\}\}', '', prompt)
    
    return prompt


def parse_ai_response(raw_response: str) -> tuple:
    """
    解析AI的响应，识别操作类型
    
    Args:
        raw_response: AI的原始回复文本
    
    Returns:
        (message, operation_type, operation_content)
        - message: 显示给用户的消息（已清理原文标记）
        - operation_type: 操作类型
        - operation_content: 操作内容（保留原文标记用于定位）
    """
    # 清理响应文本
    message = raw_response.strip()
    
    # 移除可能的JSON代码块标记
    if message.startswith('```json'):
        message = message[7:]
    if message.startswith('```'):
        message = message[3:]
    if message.endswith('```'):
        message = message[:-3]
    message = message.strip()
    
    # 尝试解析JSON格式（兼容旧格式）
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', message)
        if json_match:
            data = json.loads(json_match.group())
            if 'message' in data and 'operation' in data:
                # 旧的JSON格式
                msg = data.get('message', message)
                operation = data.get('operation', {})
                op_type = operation.get('type', 'none')
                op_content = operation.get('content', '')
                return msg, op_type, op_content
    except (json.JSONDecodeError, Exception):
        pass
    
    # 新格式：纯文本，通过关键词识别操作类型
    op_type = 'none'
    op_content = ''
    
    # 检测是否生成了大纲（更严格的判断）
    # 只有明确包含"大纲"关键词时才识别为生成大纲操作
    if ('大纲' in message and any(keyword in message for keyword in ['生成', '如下', '：', ':'])):
        op_type = 'generate_outline'
        # 提取大纲内容（从"生成的大纲"或"大纲："之后的内容）
        import re
        outline_match = re.search(r'(?:生成的大纲[：:]\s*\n|大纲如下[：:]\s*\n|大纲[：:]\s*\n)([\s\S]+)', message)
        if outline_match:
            op_content = outline_match.group(1).strip()
        else:
            # 如果没有明确标记，尝试提取所有带编号的行
            lines = message.split('\n')
            outline_lines = []
            for line in lines:
                # 匹配 "1. ", "1.1 ", "一、", "（一）" 等格式
                if re.match(r'^\s*(\d+\.|\d+\.\d+|\d+\.\d+\.\d+|[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)', line):
                    outline_lines.append(line)
            if outline_lines:
                op_content = '\n'.join(outline_lines)
        
        # 清理大纲内容，移除任何残留的标记
        op_content = re.sub(r'\s*@@SOURCE:"[^"]*"@@', '', op_content)
        op_content = re.sub(r'\s*\(原文[:：]\s*["\'""][^"\'""]*["\'"]\s*\)', '', op_content)
        
        # 为显示创建清理后的消息
        display_message = re.sub(r'\s*@@SOURCE:"[^"]*"@@', '', message)
        display_message = re.sub(r'\s*\(原文[:：]\s*["\'""][^"\'""]*["\'"]\s*\)', '', display_message)
        
        return display_message, op_type, op_content
    
    # 检测是否进行了扩写
    elif '扩写' in message or '扩展' in message or '详细阐述' in message:
        op_type = 'expand_content'
        op_content = message
    
    # 检测是否生成了摘要
    elif '摘要' in message or '总结' in message:
        op_type = 'summarize'
        op_content = message
    
    # 检测是否进行了风格转换
    elif '风格' in message or '改写' in message or '转换' in message:
        op_type = 'style_transfer'
        op_content = message
    
    # 检测是否进行了语法检查
    elif '语法' in message or '错误' in message or '修正' in message:
        op_type = 'grammar_check'
        op_content = message
    
    return message, op_type, op_content
