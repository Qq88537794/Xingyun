# 提示工程模块初始化
from .template import PromptTemplate, PromptVariable
from .manager import PromptManager
from .few_shot import FewShotManager, FewShotExample
from .context import ContextManager, ConversationContext
from .quality import QualityController

__all__ = [
    'PromptTemplate',
    'PromptVariable',
    'PromptManager',
    'FewShotManager',
    'FewShotExample',
    'ContextManager',
    'ConversationContext',
    'QualityController',
]
