"""
提示模板系统
支持变量替换、条件逻辑和模板继承
"""

import re
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class VariableType(Enum):
    """变量类型"""
    STRING = "string"
    NUMBER = "number"
    LIST = "list"
    BOOLEAN = "boolean"
    OPTIONAL = "optional"


@dataclass
class PromptVariable:
    """提示变量定义"""
    name: str
    var_type: VariableType = VariableType.STRING
    default: Any = None
    description: str = ""
    required: bool = True
    validator: Optional[Callable[[Any], bool]] = None


@dataclass
class PromptTemplate:
    """
    提示模板
    支持变量替换、条件块、循环等功能
    """
    
    name: str
    template: str
    description: str = ""
    variables: List[PromptVariable] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    
    # 模板语法
    VAR_PATTERN = r'\{\{(\w+)\}\}'           # {{variable}}
    COND_PATTERN = r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}'  # {% if var %}...{% endif %}
    LOOP_PATTERN = r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}'  # {% for item in list %}...{% endfor %}
    ELSE_PATTERN = r'\{%\s*else\s*%\}'       # {% else %}
    
    def __post_init__(self):
        """初始化后处理"""
        # 构建变量映射
        self._var_map = {v.name: v for v in self.variables}
        
        # 自动检测模板中的变量
        self._detect_variables()
    
    def _detect_variables(self):
        """自动检测模板中的变量"""
        found_vars = set(re.findall(self.VAR_PATTERN, self.template))
        
        # 添加未定义的变量
        for var_name in found_vars:
            if var_name not in self._var_map:
                self.variables.append(PromptVariable(
                    name=var_name,
                    required=True
                ))
                self._var_map[var_name] = self.variables[-1]
    
    def render(self, **kwargs) -> str:
        """
        渲染模板
        
        Args:
            **kwargs: 变量值
        
        Returns:
            渲染后的字符串
        """
        # 合并默认值
        context = {}
        for var in self.variables:
            if var.name in kwargs:
                context[var.name] = kwargs[var.name]
            elif var.default is not None:
                context[var.name] = var.default
            elif var.required:
                raise ValueError(f"缺少必需变量: {var.name}")
        
        # 验证变量
        self._validate_variables(context)
        
        result = self.template
        
        # 处理条件块
        result = self._process_conditionals(result, context)
        
        # 处理循环
        result = self._process_loops(result, context)
        
        # 替换变量
        result = self._replace_variables(result, context)
        
        # 清理多余空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    def _validate_variables(self, context: Dict[str, Any]):
        """验证变量值"""
        for var in self.variables:
            if var.name in context and var.validator:
                if not var.validator(context[var.name]):
                    raise ValueError(f"变量 {var.name} 验证失败")
    
    def _process_conditionals(self, template: str, context: Dict[str, Any]) -> str:
        """处理条件块"""
        
        def replace_cond(match):
            var_name = match.group(1)
            content = match.group(2)
            
            # 检查else块
            else_match = re.search(self.ELSE_PATTERN, content)
            if else_match:
                if_content = content[:else_match.start()]
                else_content = content[else_match.end():]
            else:
                if_content = content
                else_content = ""
            
            # 评估条件
            value = context.get(var_name)
            if value:  # 真值
                return if_content
            else:
                return else_content
        
        # 递归处理嵌套条件
        prev_result = None
        result = template
        while prev_result != result:
            prev_result = result
            result = re.sub(
                self.COND_PATTERN,
                replace_cond,
                result,
                flags=re.DOTALL
            )
        
        return result
    
    def _process_loops(self, template: str, context: Dict[str, Any]) -> str:
        """处理循环"""
        
        def replace_loop(match):
            item_name = match.group(1)
            list_name = match.group(2)
            loop_content = match.group(3)
            
            items = context.get(list_name, [])
            if not isinstance(items, (list, tuple)):
                return ""
            
            parts = []
            for item in items:
                # 在循环内容中替换循环变量
                part = loop_content.replace(f'{{{{{item_name}}}}}', str(item))
                parts.append(part)
            
            return ''.join(parts)
        
        return re.sub(
            self.LOOP_PATTERN,
            replace_loop,
            template,
            flags=re.DOTALL
        )
    
    def _replace_variables(self, template: str, context: Dict[str, Any]) -> str:
        """替换变量"""
        
        def replace_var(match):
            var_name = match.group(1)
            value = context.get(var_name, '')
            
            if isinstance(value, list):
                return '\n'.join(str(v) for v in value)
            return str(value)
        
        return re.sub(self.VAR_PATTERN, replace_var, template)
    
    def get_required_variables(self) -> List[str]:
        """获取必需变量列表"""
        return [v.name for v in self.variables if v.required]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'template': self.template,
            'description': self.description,
            'variables': [
                {
                    'name': v.name,
                    'type': v.var_type.value,
                    'default': v.default,
                    'description': v.description,
                    'required': v.required
                }
                for v in self.variables
            ],
            'tags': self.tags,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """从字典创建"""
        variables = [
            PromptVariable(
                name=v['name'],
                var_type=VariableType(v.get('type', 'string')),
                default=v.get('default'),
                description=v.get('description', ''),
                required=v.get('required', True)
            )
            for v in data.get('variables', [])
        ]
        
        return cls(
            name=data['name'],
            template=data['template'],
            description=data.get('description', ''),
            variables=variables,
            tags=data.get('tags', []),
            version=data.get('version', '1.0')
        )


# 预定义模板 - 大纲生成
OUTLINE_TEMPLATE = PromptTemplate(
    name="outline_generation",
    description="根据主题生成文档大纲",
    template="""你是一位专业的文档架构师。请根据以下信息生成详细的文档大纲。

【主题】
{{topic}}

{% if context %}
【参考资料】
{{context}}
{% endif %}

{% if requirements %}
【具体要求】
{{requirements}}
{% endif %}

【输出格式要求】
- 使用层级编号（1. 1.1 1.1.1）
- 每个章节需包含简要说明
- 大纲层级不超过3层
- 内容需要逻辑清晰、结构完整

{% if style %}
【风格要求】
{{style}}
{% endif %}

请生成大纲：""",
    variables=[
        PromptVariable(name="topic", description="文档主题", required=True),
        PromptVariable(name="context", description="参考资料", required=False),
        PromptVariable(name="requirements", description="具体要求", required=False),
        PromptVariable(name="style", description="风格要求", required=False),
    ],
    tags=["outline", "structure", "planning"]
)


# 预定义模板 - 内容扩写
EXPANSION_TEMPLATE = PromptTemplate(
    name="content_expansion",
    description="扩展和丰富现有内容",
    template="""你是一位专业的内容写作专家。请扩展以下内容，使其更加丰富和详细。

【原始内容】
{{content}}

{% if context %}
【相关资料】
{{context}}
{% endif %}

【扩展要求】
- 保持原有观点和立场
- 增加具体案例和数据支持
- 扩展篇幅约{{expansion_ratio}}倍
- 语言风格：{{tone}}

{% if focus_areas %}
【重点扩展方向】
{% for area in focus_areas %}
- {{area}}
{% endfor %}
{% endif %}

请生成扩展后的内容：""",
    variables=[
        PromptVariable(name="content", description="待扩展内容", required=True),
        PromptVariable(name="context", description="相关资料", required=False),
        PromptVariable(name="expansion_ratio", description="扩展倍数", default="2-3"),
        PromptVariable(name="tone", description="语言风格", default="专业、正式"),
        PromptVariable(name="focus_areas", description="重点扩展方向", required=False, var_type=VariableType.LIST),
    ],
    tags=["expansion", "writing", "content"]
)


# 预定义模板 - 风格迁移
STYLE_TRANSFER_TEMPLATE = PromptTemplate(
    name="style_transfer",
    description="将内容转换为指定风格",
    template="""你是一位语言风格专家。请将以下内容改写为{{target_style}}风格。

【原始内容】
{{content}}

【目标风格描述】
{{style_description}}

{% if examples %}
【风格示例】
{{examples}}
{% endif %}

【改写要求】
- 保持原有核心信息不变
- 调整语气、用词和句式
- 适应目标读者群体
{% if preserve_structure %}
- 保持原有段落结构
{% endif %}

请生成改写后的内容：""",
    variables=[
        PromptVariable(name="content", description="原始内容", required=True),
        PromptVariable(name="target_style", description="目标风格", required=True),
        PromptVariable(name="style_description", description="风格详细描述", default=""),
        PromptVariable(name="examples", description="风格示例", required=False),
        PromptVariable(name="preserve_structure", description="是否保持结构", default=True, var_type=VariableType.BOOLEAN),
    ],
    tags=["style", "rewrite", "transfer"]
)


# 预定义模板 - 摘要生成
SUMMARY_TEMPLATE = PromptTemplate(
    name="summary_generation",
    description="生成内容摘要",
    template="""你是一位专业的内容分析师。请为以下内容生成摘要。

【原始内容】
{{content}}

【摘要要求】
- 摘要长度：{{summary_length}}
- 包含关键观点和核心信息
- 使用简洁明了的语言
{% if include_keywords %}
- 在摘要末尾列出3-5个关键词
{% endif %}

{% if focus_points %}
【重点关注】
{{focus_points}}
{% endif %}

请生成摘要：""",
    variables=[
        PromptVariable(name="content", description="待摘要内容", required=True),
        PromptVariable(name="summary_length", description="摘要长度", default="200-300字"),
        PromptVariable(name="include_keywords", description="是否包含关键词", default=True, var_type=VariableType.BOOLEAN),
        PromptVariable(name="focus_points", description="重点关注方向", required=False),
    ],
    tags=["summary", "analysis", "extraction"]
)


# 预定义模板 - RAG问答
RAG_QA_TEMPLATE = PromptTemplate(
    name="rag_qa",
    description="基于检索结果回答问题",
    template="""基于以下参考资料回答用户问题。如果资料中没有相关信息，请明确说明。

【参考资料】
{{context}}

【用户问题】
{{question}}

{% if chat_history %}
【对话历史】
{{chat_history}}
{% endif %}

【回答要求】
- 基于参考资料回答，必要时引用来源
- 回答要准确、完整、有条理
- 如果不确定，请明确表示
{% if response_format %}
- 回答格式：{{response_format}}
{% endif %}

请回答：""",
    variables=[
        PromptVariable(name="context", description="检索到的上下文", required=True),
        PromptVariable(name="question", description="用户问题", required=True),
        PromptVariable(name="chat_history", description="对话历史", required=False),
        PromptVariable(name="response_format", description="响应格式要求", required=False),
    ],
    tags=["rag", "qa", "retrieval"]
)


# 预定义模板 - 语法检查
GRAMMAR_CHECK_TEMPLATE = PromptTemplate(
    name="grammar_check",
    description="检查并修正语法错误",
    template="""你是一位专业的校对编辑。请检查以下文本中的语法、拼写和标点错误。

【待检查文本】
{{content}}

【检查范围】
- 语法错误
- 拼写错误
- 标点符号使用
- 句子通顺度
{% if check_style %}
- 文风一致性
{% endif %}

【输出格式】
请按以下格式输出：
1. 错误列表（原文 → 修正）
2. 修正后的完整文本

请开始检查：""",
    variables=[
        PromptVariable(name="content", description="待检查内容", required=True),
        PromptVariable(name="check_style", description="是否检查文风", default=False, var_type=VariableType.BOOLEAN),
    ],
    tags=["grammar", "proofreading", "correction"]
)


# 预定义模板集合
BUILTIN_TEMPLATES = {
    'outline_generation': OUTLINE_TEMPLATE,
    'content_expansion': EXPANSION_TEMPLATE,
    'style_transfer': STYLE_TRANSFER_TEMPLATE,
    'summary_generation': SUMMARY_TEMPLATE,
    'rag_qa': RAG_QA_TEMPLATE,
    'grammar_check': GRAMMAR_CHECK_TEMPLATE,
}
