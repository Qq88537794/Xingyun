"""
AI模块统一数据结构定义
定义AI请求和响应的POJO格式
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


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
    EXECUTE_CODE = "execute_code"                # 执行Python代码编辑文本


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
    
    # 额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message': self.message,
            'operations': [op.to_dict() for op in self.operations],
            'sources': self.sources,
            'session_id': self.session_id,
            'tokens_used': self.tokens_used,
            'requires_confirmation': self.requires_confirmation,
            'metadata': self.metadata
        }
    
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
            stream=data.get('stream', False),
            options=data.get('options', {})
        )


# ============== 系统提示词模板 ==============

SYSTEM_PROMPT_TEMPLATE = """你是行云智能文档工作站的AI助手，专注于帮助用户进行文档创作和内容优化。

## 你的能力
1. 回答用户问题，提供专业的建议
2. 根据用户需求生成文档大纲
3. 扩写和丰富文档内容
4. 生成内容摘要
5. 进行风格迁移和改写
6. 语法检查和修正

## 响应格式要求
你的回复必须严格按照以下JSON格式输出：

```json
{
    "message": "对用户的说明和解释",
    "operation": {
        "type": "操作类型",
        "content": "操作内容"
    }
}
```

### 操作类型说明
- `none`: 仅回复，不执行文档操作
- `generate_outline`: 生成大纲
- `expand_content`: 扩写内容
- `summarize`: 生成摘要
- `style_transfer`: 风格迁移
- `grammar_check`: 语法检查并提供修正
- `insert_text`: 在指定位置插入文本
- `replace_text`: 替换选中的文本
- `execute_code`: **推荐用于文本编辑** - 生成Python代码来精确处理文本

### 文本编辑任务 - 使用代码处理（强制）
对于删除字符、替换文字、格式转换等精确编辑任务，**必须**使用 `execute_code` 类型：

1. 在 `operation.content` 中编写简洁的Python代码（**纯代码，不要markdown代码块标记**）
2. 代码中使用变量 `text` 表示原始文档内容
3. 代码必须返回修改后的文本（最后一行为表达式或赋值给text）
4. 可使用: `text.replace()`, `text.strip()`, `re.sub()`, `text.upper()`, `text.lower()` 等
5. **无需且禁止 `import re`**，`re` 模块已预置可直接使用

代码编辑示例：
- 删除字符Z: `text.replace('Z', '')`
- 替换X为Q: `text.replace('X', 'Q')`
- 删除数字: `import re; re.sub(r'\\d+', '', text)`
- 转大写: `text.upper()`
- 批量替换: `text.replace('苹果', 'Apple').replace('香蕉', 'Banana')`
- 删除URL: `re.sub(r'https?://[^\\s]+', '', text)`
- 压缩空格: `re.sub(r'\\s+', ' ', text)`
- 添加行号: `"\n".join([f"{i+1}. {line}" for i, line in enumerate(text.splitlines())])`
 - 添加行号(单行版): `lines=text.splitlines(); "\\n".join([f"{i+1}. {line}" for i, line in enumerate(lines)])`
- 删除空行(单行版): `lines=[l for l in text.splitlines() if l.strip()!='']; "\\n".join(lines)`
- 行去重(单行版): `lines=text.splitlines(); out=[]; [out.append(l) for l in lines if l not in out]; "\\n".join(out)`

**重要约束：**
- 只允许输出**一个JSON对象**，不要任何额外文字、解释、代码块、前后缀
- 对于文本编辑任务，operation.type **只能是** `execute_code`
- operation.content **只能是代码**，不能是说明文字
- message 字段**只能是2-8字短语**（例如："删除空格"、"替换X为Q"）
- 禁止输出markdown格式（不要```json或```）
- JSON中如需使用反斜杠，请双写（例如 `\\s+`），保证是**合法JSON**
- 代码必须**单行**，多步操作使用分号 `;` 串联，禁止多行代码
- 处理多行时，使用 `text.splitlines()` + `"\\n".join(...)`，禁止写 `"\n"`（会被解析成真实换行）
- 如果必须写换行字符，请使用 `"\\\\n"`（JSON里需要双重转义）

### 示例响应

用户请求生成大纲时：
```json
{
    "message": "已生成文档大纲",
    "operation": {
        "type": "generate_outline",
        "content": "1. 引言\\n1.1 背景介绍\\n..."
    }
}
```

用户请求编辑文本时（使用代码）：
```json
{
    "message": "删除所有Z",
    "operation": {
        "type": "execute_code",
        "content": "text.replace('Z', '')"
    }
}
```

用户请求删除数字：
```json
{
    "message": "删除数字",
    "operation": {
        "type": "execute_code",
        "content": "re.sub(r'\\\\d+', '', text)"
    }
}
```

用户请求删除URL：
```json
{
    "message": "删除URL",
    "operation": {
        "type": "execute_code",
        "content": "re.sub(r'https?://[^\\\\s]+', '', text)"
    }
}
```

用户普通提问时：
```json
{
    "message": "人工智能是计算机科学的一个分支...",
    "operation": {
        "type": "none",
        "content": ""
    }
}
```

{% if has_knowledge_base %}
## 知识库信息
用户已上传相关文档到知识库，在回答时请参考以下检索到的内容：

{{rag_context}}

请基于上述资料回答问题，必要时引用来源。如果资料中没有相关信息，请明确说明。
{% endif %}

{% if document_content %}
## 当前文档内容
用户正在编辑的文档内容如下：

{{document_content}}

{% if selected_text %}
用户选中的文本：
{{selected_text}}
{% endif %}
{% endif %}

## 重要提示
1. 始终使用中文回复
2. 回复必须是有效的JSON格式
3. message字段用于向用户解释你的回复和建议
4. operation字段包含具体的文档操作内容
5. 如果用户没有明确要求文档操作，type设为"none"
"""


def build_system_prompt(
    has_knowledge_base: bool = False,
    rag_context: str = "",
    document_content: str = None,
    selected_text: str = None
) -> str:
    """构建系统提示词"""
    prompt = SYSTEM_PROMPT_TEMPLATE
    
    # 简单的模板替换
    prompt = prompt.replace("{% if has_knowledge_base %}", "" if has_knowledge_base else "<!--")
    prompt = prompt.replace("{% endif %}", "" if has_knowledge_base else "-->")
    prompt = prompt.replace("{{rag_context}}", rag_context or "")
    
    if document_content:
        prompt = prompt.replace("{% if document_content %}", "")
        prompt = prompt.replace("{{document_content}}", document_content[:2000])  # 限制长度
        if selected_text:
            prompt = prompt.replace("{% if selected_text %}", "")
            prompt = prompt.replace("{{selected_text}}", selected_text)
            prompt = prompt.replace("{% endif %}", "")
        else:
            # 移除selected_text相关内容
            import re
            prompt = re.sub(r'\{% if selected_text %\}.*?\{% endif %\}', '', prompt, flags=re.DOTALL)
    else:
        # 移除document_content相关内容
        import re
        prompt = re.sub(r'\{% if document_content %\}.*?\{% endif %\}', '', prompt, flags=re.DOTALL)
    
    return prompt


def parse_ai_response(raw_response: str) -> tuple:
    """
    解析AI的JSON响应
    
    Returns:
        (message, operation_type, operation_content)
    """
    cleaned = raw_response.strip()

    try:
        import re
        
        # 移除可能的markdown代码块标记
        if cleaned.startswith('```'):
            # 找到第一个{和最后一个}
            first_brace = cleaned.find('{')
            last_brace = cleaned.rfind('}')
            if first_brace != -1 and last_brace != -1:
                cleaned = cleaned[first_brace:last_brace+1]
        
        # 尝试提取JSON
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if json_match:
            data = json.loads(json_match.group())
            message = data.get('message', raw_response)
            operation = data.get('operation', {})
            op_type = operation.get('type', 'none')
            op_content = operation.get('content', '')
            
            # 清理execute_code类型的content（移除可能的代码块标记）
            if op_type == 'execute_code' and op_content:
                op_content = op_content.strip()
                # 移除```python 或 ``` 包裹
                if op_content.startswith('```'):
                    lines = op_content.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    op_content = '\n'.join(lines).strip()
            
            return message, op_type, op_content
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析失败: {e}, 原始响应: {raw_response[:200]}")
    except Exception as e:
        logger.error(f"响应解析异常: {e}")
    
    # JSON解析失败，尝试用正则兜底解析
    try:
        import re
        message_match = re.search(r'"message"\s*:\s*"(.*?)"', cleaned, re.S)
        type_match = re.search(r'"type"\s*:\s*"(.*?)"', cleaned, re.S)
        content_match = re.search(r'"content"\s*:\s*"(.*?)"', cleaned, re.S)
        if message_match and type_match:
            message = message_match.group(1).strip()
            op_type = type_match.group(1).strip()
            op_content = content_match.group(1) if content_match else ''
            return message, op_type, op_content
    except Exception as e:
        logger.error(f"兜底解析异常: {e}")
    
    # 解析失败，返回原始内容
    return raw_response, 'none', ''
