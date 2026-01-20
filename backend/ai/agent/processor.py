"""
Agent处理器
基于Finish Reason驱动的Agent循环

核心流程：
1. 用户输入 → 构建提示词 → 调用LLM
2. LLM返回 → 解析finish_reason
   - "stop" → 结束循环，返回结果
   - "tool_calls" → 执行工具，将结果追加到消息历史，继续循环
3. 消息历史累积，直到任务完成
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional, Generator
from dataclasses import dataclass, field
from enum import Enum

from .tools import ToolRegistry, ToolCall, ToolStatus

logger = logging.getLogger(__name__)


class FinishReason(Enum):
    """LLM完成原因"""
    STOP = "stop"              # 模型主动停止（任务完成）
    TOOL_CALLS = "tool_calls"  # 需要执行工具调用
    LENGTH = "length"          # 输出过长
    ERROR = "error"            # 发生错误


@dataclass
class AgentMessage:
    """Agent消息"""
    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # 工具调用（assistant）
    tool_call_id: Optional[str] = None  # 工具调用ID（tool响应）
    name: Optional[str] = None  # 工具名称（tool响应）
    
    def to_llm_format(self) -> Dict[str, Any]:
        """转换为LLM消息格式"""
        msg = {"role": self.role, "content": self.content}
        
        if self.role == "assistant" and self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        
        if self.role == "tool":
            msg["tool_call_id"] = self.tool_call_id
            msg["name"] = self.name
        
        return msg


@dataclass
class AgentState:
    """Agent状态"""
    session_id: str
    messages: List[AgentMessage] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)  # 执行过的工具调用
    total_tokens: int = 0
    iterations: int = 0
    max_iterations: int = 10  # 防止无限循环
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append(AgentMessage(role="user", content=content))
    
    def add_assistant_message(self, content: str, tool_calls: List[Dict] = None):
        """添加助手消息"""
        self.messages.append(AgentMessage(
            role="assistant",
            content=content,
            tool_calls=tool_calls or []
        ))
    
    def add_tool_result(self, tool_call_id: str, name: str, result: Any):
        """添加工具执行结果"""
        content = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
        self.messages.append(AgentMessage(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=name
        ))
    
    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """获取LLM格式的消息列表"""
        return [msg.to_llm_format() for msg in self.messages]


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    message: str  # 最终回复
    tool_calls: List[ToolCall]  # 执行的工具调用记录
    iterations: int  # 循环次数
    total_tokens: int
    session_id: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "iterations": self.iterations,
            "total_tokens": self.total_tokens,
            "session_id": self.session_id,
            "error": self.error
        }


class AgentProcessor:
    """
    Agent处理器
    实现基于Finish Reason的循环驱动
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        llm_caller,  # LLM调用接口
        system_prompt: str = "",
        max_iterations: int = 10
    ):
        """
        初始化Agent处理器
        
        Args:
            tool_registry: 工具注册表
            llm_caller: LLM调用接口，需要支持tool_calls
            system_prompt: 系统提示词
            max_iterations: 最大迭代次数
        """
        self.tool_registry = tool_registry
        self.llm_caller = llm_caller
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
    
    def process(
        self,
        user_input: str,
        session_id: str = None,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        处理用户输入
        
        这是Agent的核心循环：
        1. 调用LLM
        2. 检查finish_reason
        3. 如果是tool_calls，执行工具并继续循环
        4. 如果是stop，返回结果
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            context: 额外上下文（如当前文档内容）
        
        Returns:
            AgentResult
        """
        session_id = session_id or str(uuid.uuid4())
        
        # 初始化状态
        state = AgentState(
            session_id=session_id,
            max_iterations=self.max_iterations
        )
        
        # 添加用户消息
        state.add_user_message(user_input)
        
        # 构建完整的系统提示词（包含工具说明）
        full_system_prompt = self._build_system_prompt(context)
        
        # ====== 核心循环 ======
        while state.iterations < state.max_iterations:
            state.iterations += 1
            logger.info(f"Agent迭代 #{state.iterations}")
            
            try:
                # 调用LLM
                response = self._call_llm(
                    system_prompt=full_system_prompt,
                    messages=state.get_messages_for_llm(),
                    tools=self.tool_registry.to_llm_tools()
                )
                
                # 更新token统计
                state.total_tokens += response.get("usage", {}).get("total_tokens", 0)
                
                # 解析finish_reason
                finish_reason = self._parse_finish_reason(response)
                content = response.get("content", "")
                tool_calls = response.get("tool_calls", [])
                
                logger.info(f"LLM返回: finish_reason={finish_reason}, tool_calls={len(tool_calls)}")
                
                # ====== 根据finish_reason决定下一步 ======
                
                if finish_reason == FinishReason.STOP:
                    # 模型主动停止，任务完成
                    state.add_assistant_message(content)
                    return AgentResult(
                        success=True,
                        message=content,
                        tool_calls=state.tool_calls,
                        iterations=state.iterations,
                        total_tokens=state.total_tokens,
                        session_id=session_id
                    )
                
                elif finish_reason == FinishReason.TOOL_CALLS:
                    # 需要执行工具调用
                    state.add_assistant_message(content, tool_calls)
                    
                    # 执行所有工具调用
                    for tc in tool_calls:
                        tool_result = self._execute_tool(tc, state)
                        state.add_tool_result(
                            tool_call_id=tc["id"],
                            name=tc["function"]["name"],
                            result=tool_result
                        )
                    
                    # 继续循环
                    continue
                
                elif finish_reason == FinishReason.LENGTH:
                    # 输出过长（可以在这里实现上下文压缩，暂时简化处理）
                    logger.warning("输出过长，终止循环")
                    return AgentResult(
                        success=False,
                        message=content or "响应过长，请简化问题",
                        tool_calls=state.tool_calls,
                        iterations=state.iterations,
                        total_tokens=state.total_tokens,
                        session_id=session_id,
                        error="length_exceeded"
                    )
                
                elif finish_reason == FinishReason.ERROR:
                    return AgentResult(
                        success=False,
                        message="处理过程中发生错误",
                        tool_calls=state.tool_calls,
                        iterations=state.iterations,
                        total_tokens=state.total_tokens,
                        session_id=session_id,
                        error="llm_error"
                    )
            
            except Exception as e:
                logger.error(f"Agent处理错误: {e}", exc_info=True)
                return AgentResult(
                    success=False,
                    message=f"处理错误: {str(e)}",
                    tool_calls=state.tool_calls,
                    iterations=state.iterations,
                    total_tokens=state.total_tokens,
                    session_id=session_id,
                    error=str(e)
                )
        
        # 达到最大迭代次数
        logger.warning(f"达到最大迭代次数: {self.max_iterations}")
        return AgentResult(
            success=False,
            message="处理步骤过多，已终止。请尝试简化请求。",
            tool_calls=state.tool_calls,
            iterations=state.iterations,
            total_tokens=state.total_tokens,
            session_id=session_id,
            error="max_iterations_exceeded"
        )
    
    def process_stream(
        self,
        user_input: str,
        session_id: str = None,
        context: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, AgentResult]:
        """
        流式处理用户输入
        
        产出事件：
        - {"type": "thinking", "content": "..."}  # 思考过程
        - {"type": "tool_call", "name": "...", "arguments": {...}}  # 工具调用
        - {"type": "tool_result", "name": "...", "result": {...}}  # 工具结果
        - {"type": "text", "content": "..."}  # 文本输出
        - {"type": "done", "result": {...}}  # 完成
        
        Returns:
            Generator产出事件，最后返回AgentResult
        """
        session_id = session_id or str(uuid.uuid4())
        state = AgentState(session_id=session_id, max_iterations=self.max_iterations)
        state.add_user_message(user_input)
        
        full_system_prompt = self._build_system_prompt(context)
        
        while state.iterations < state.max_iterations:
            state.iterations += 1
            
            yield {"type": "thinking", "iteration": state.iterations}
            
            try:
                response = self._call_llm(
                    system_prompt=full_system_prompt,
                    messages=state.get_messages_for_llm(),
                    tools=self.tool_registry.to_llm_tools()
                )
                
                state.total_tokens += response.get("usage", {}).get("total_tokens", 0)
                finish_reason = self._parse_finish_reason(response)
                content = response.get("content", "")
                tool_calls = response.get("tool_calls", [])
                
                if finish_reason == FinishReason.STOP:
                    state.add_assistant_message(content)
                    yield {"type": "text", "content": content}
                    
                    result = AgentResult(
                        success=True,
                        message=content,
                        tool_calls=state.tool_calls,
                        iterations=state.iterations,
                        total_tokens=state.total_tokens,
                        session_id=session_id
                    )
                    yield {"type": "done", "result": result.to_dict()}
                    return result
                
                elif finish_reason == FinishReason.TOOL_CALLS:
                    if content:
                        yield {"type": "text", "content": content}
                    
                    state.add_assistant_message(content, tool_calls)
                    
                    for tc in tool_calls:
                        yield {
                            "type": "tool_call",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "arguments": tc["function"].get("arguments", {})
                        }
                        
                        tool_result = self._execute_tool(tc, state)
                        
                        yield {
                            "type": "tool_result",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "result": tool_result
                        }
                        
                        state.add_tool_result(
                            tool_call_id=tc["id"],
                            name=tc["function"]["name"],
                            result=tool_result
                        )
                    
                    continue
                
                else:
                    result = AgentResult(
                        success=False,
                        message=content or "处理终止",
                        tool_calls=state.tool_calls,
                        iterations=state.iterations,
                        total_tokens=state.total_tokens,
                        session_id=session_id,
                        error=str(finish_reason)
                    )
                    yield {"type": "done", "result": result.to_dict()}
                    return result
            
            except Exception as e:
                logger.error(f"Agent流式处理错误: {e}", exc_info=True)
                result = AgentResult(
                    success=False,
                    message=f"处理错误: {str(e)}",
                    tool_calls=state.tool_calls,
                    iterations=state.iterations,
                    total_tokens=state.total_tokens,
                    session_id=session_id,
                    error=str(e)
                )
                yield {"type": "error", "error": str(e)}
                yield {"type": "done", "result": result.to_dict()}
                return result
        
        # 达到最大迭代
        result = AgentResult(
            success=False,
            message="处理步骤过多，已终止",
            tool_calls=state.tool_calls,
            iterations=state.iterations,
            total_tokens=state.total_tokens,
            session_id=session_id,
            error="max_iterations_exceeded"
        )
        yield {"type": "done", "result": result.to_dict()}
        return result
    
    def _build_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """构建完整系统提示词"""
        parts = [self.system_prompt]
        
        # 添加工具使用说明
        parts.append(self.tool_registry.build_tools_prompt())
        
        # 添加上下文信息
        if context:
            if context.get("document_content"):
                parts.append(f"\n## 当前文档内容\n{context['document_content'][:3000]}")
            if context.get("selected_text"):
                parts.append(f"\n## 选中的文本\n{context['selected_text']}")
            if context.get("rag_context"):
                parts.append(f"\n## 相关知识库内容\n{context['rag_context']}")
        
        return "\n\n".join(parts)
    
    def _call_llm(
        self,
        system_prompt: str,
        messages: List[Dict],
        tools: List[Dict]
    ) -> Dict[str, Any]:
        """
        调用LLM
        
        需要返回格式：
        {
            "content": "回复内容",
            "tool_calls": [
                {
                    "id": "call_xxx",
                    "function": {
                        "name": "tool_name",
                        "arguments": {...}
                    }
                }
            ],
            "finish_reason": "stop" | "tool_calls" | "length",
            "usage": {"total_tokens": 100}
        }
        """
        return self.llm_caller(
            system_prompt=system_prompt,
            messages=messages,
            tools=tools
        )
    
    def _parse_finish_reason(self, response: Dict[str, Any]) -> FinishReason:
        """解析finish_reason"""
        reason = response.get("finish_reason", "stop")
        
        # 标准化不同LLM的finish_reason
        if reason in ("stop", "end_turn", "end"):
            return FinishReason.STOP
        elif reason in ("tool_calls", "tool_use", "function_call"):
            return FinishReason.TOOL_CALLS
        elif reason in ("length", "max_tokens"):
            return FinishReason.LENGTH
        else:
            # 如果有tool_calls但reason不明确，认为是tool_calls
            if response.get("tool_calls"):
                return FinishReason.TOOL_CALLS
            return FinishReason.STOP
    
    def _execute_tool(self, tool_call: Dict, state: AgentState) -> Any:
        """执行单个工具调用"""
        tool_id = tool_call.get("id", str(uuid.uuid4()))
        func = tool_call.get("function", {})
        name = func.get("name", "")
        arguments = func.get("arguments", {})
        
        # 如果arguments是字符串，尝试解析JSON
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        
        # 记录工具调用
        call_record = ToolCall(
            id=tool_id,
            name=name,
            arguments=arguments,
            status=ToolStatus.RUNNING
        )
        state.tool_calls.append(call_record)
        
        logger.info(f"执行工具: {name}, 参数: {arguments}")
        
        try:
            result = self.tool_registry.execute(name, arguments)
            call_record.status = ToolStatus.COMPLETED
            call_record.result = result
            logger.info(f"工具执行成功: {name}")
            return result
        except Exception as e:
            logger.error(f"工具执行失败: {name}, 错误: {e}")
            call_record.status = ToolStatus.ERROR
            call_record.error = str(e)
            return {"error": str(e)}
