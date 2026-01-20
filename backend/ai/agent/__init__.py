"""
Agent模块
提供基于工具调用的智能文档处理能力

基于Finish Reason驱动的Agent循环:
1. 用户输入 → 构建提示词 → 调用LLM
2. LLM返回 → 解析finish_reason
   - "stop" → 结束循环，返回结果
   - "tool_calls" → 执行工具，将结果追加到消息历史，继续循环
3. 消息历史累积，直到任务完成
"""

from .tools import (
    # 基础类
    BaseTool,
    ToolRegistry,
    ToolCall,
    ToolStatus,
    ToolDefinition,
    # 文档操作工具
    ReadDocumentTool,
    WriteDocumentTool,
    EditDocumentTool,
    SearchDocumentTool,
    # 内容生成工具
    GenerateOutlineTool,
    ExpandContentTool,
    SummarizeTool,
    # 工厂函数
    create_default_registry
)

from .processor import (
    AgentProcessor,
    AgentState,
    AgentResult,
    AgentMessage,
    FinishReason
)

__all__ = [
    # 工具基础
    'BaseTool',
    'ToolRegistry',
    'ToolCall',
    'ToolStatus',
    'ToolDefinition',
    
    # 文档操作工具
    'ReadDocumentTool',
    'WriteDocumentTool',
    'EditDocumentTool',
    'SearchDocumentTool',
    
    # 内容生成工具
    'GenerateOutlineTool',
    'ExpandContentTool',
    'SummarizeTool',
    
    # 工厂函数
    'create_default_registry',
    
    # 处理器相关
    'AgentProcessor',
    'AgentState',
    'AgentResult',
    'AgentMessage',
    'FinishReason',
]
