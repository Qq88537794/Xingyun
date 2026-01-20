"""
AI核心服务
提供统一的问答接口，集成RAG和Agent功能
"""

import logging
import uuid
import json
import re
from typing import Dict, Any, Optional, Generator, Callable

from ..schema import (
    AIRequest, AIResponse, FileOperation, OperationType,
    build_system_prompt, parse_ai_response
)
from ..llm.factory import get_llm_factory
from ..prompts.context import get_context_manager
from .knowledge_base import get_kb_service
from ..agent import AgentProcessor, ToolRegistry, create_default_registry, AgentResult

logger = logging.getLogger(__name__)


class DocumentProvider:
    """
    文档提供者
    为Agent工具提供文档读写能力
    """
    
    def __init__(self, document_content: str = None, document_id: str = None):
        """
        初始化文档提供者
        
        Args:
            document_content: 当前文档内容（来自前端）
            document_id: 文档ID
        """
        self._document_content = document_content or ""
        self._document_id = document_id
        self._modified_content = None  # 保存修改后的内容
    
    def get_document(self, doc_id: str) -> Optional[str]:
        """获取文档内容"""
        # 如果是当前文档，返回内容（优先返回修改后的内容）
        if doc_id == self._document_id or not doc_id:
            return self._modified_content if self._modified_content else self._document_content
        # 其他文档暂不支持
        return None
    
    def write_document(self, doc_id: str, content: str) -> bool:
        """写入文档内容"""
        if doc_id == self._document_id or not doc_id:
            self._modified_content = content
            return True
        return False
    
    def get_modified_content(self) -> Optional[str]:
        """获取修改后的内容"""
        return self._modified_content
    
    def has_modifications(self) -> bool:
        """是否有修改"""
        return self._modified_content is not None


class AIService:
    """
    AI核心服务
    提供统一的问答接口
    
    支持两种模式：
    1. Simple模式：直接调用LLM，返回响应
    2. Agent模式：使用工具调用循环，可执行文档操作
    """
    
    def __init__(self):
        """初始化AI服务"""
        self._context_manager = get_context_manager()
    
    def chat(self, request: AIRequest) -> AIResponse:
        """
        统一问答接口
        
        根据请求自动判断：
        1. 是否需要RAG检索（基于项目知识库）
        2. 是否需要Agent模式（复杂文档操作）
        
        Args:
            request: AI请求
        
        Returns:
            AI响应（包含说明和可选的文件操作）
        """
        try:
            # 1. 获取或创建会话
            session_id = request.session_id or str(uuid.uuid4())
            
            # 2. 检查是否需要RAG
            rag_context = ""
            sources = []
            has_kb = False
            
            if request.project_id:
                kb_service = get_kb_service()
                has_kb = kb_service.has_knowledge_base(request.project_id)
                
                # 如果有知识库且未明确禁用RAG
                if has_kb and request.enable_rag is not False:
                    # 检索相关内容
                    results = kb_service.search(
                        project_id=request.project_id,
                        query=request.message,
                        top_k=5
                    )
                    
                    if results:
                        rag_context = kb_service.build_context(results)
                        sources = [
                            {
                                "text": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                                "score": r.score,
                                "resource_id": r.metadata.get("resource_id")
                            }
                            for r in results[:3]
                        ]
            
            # 3. 判断是否需要Agent模式
            # 当有文档内容且请求可能涉及文档操作时使用Agent
            use_agent = request.enable_agent and request.document_content
            
            if use_agent:
                return self._chat_with_agent(
                    request=request,
                    session_id=session_id,
                    rag_context=rag_context,
                    sources=sources
                )
            else:
                return self._chat_simple(
                    request=request,
                    session_id=session_id,
                    rag_context=rag_context,
                    sources=sources
                )
        
        except Exception as e:
            logger.error(f"AI服务错误: {e}", exc_info=True)
            return AIResponse(
                message=f"抱歉，处理您的请求时出现错误：{str(e)}",
                session_id=request.session_id,
                requires_confirmation=False
            )
    
    def _chat_simple(
        self,
        request: AIRequest,
        session_id: str,
        rag_context: str,
        sources: list
    ) -> AIResponse:
        """
        简单模式：直接调用LLM
        """
        # 构建系统提示词
        system_prompt = build_system_prompt(
            has_knowledge_base=bool(rag_context),
            rag_context=rag_context,
            document_content=request.document_content,
            selected_text=request.selected_text
        )
        
        # 获取对话上下文
        context = self._context_manager.get_or_create_context(
            session_id=session_id,
            system_prompt=system_prompt
        )
        
        # 更新系统提示词（可能因为RAG内容变化）
        context.system_prompt = system_prompt
        
        # 添加用户消息
        context.add_message("user", request.message)
        
        # 调用LLM
        factory = get_llm_factory()
        llm = factory.get_llm()
        
        messages = context.get_messages_for_llm()
        response = llm.chat(messages)
        
        # 解析响应
        message, op_type, op_content = parse_ai_response(response.content)
        
        # 保存助手回复
        context.add_message("assistant", message)
        
        # 构建响应
        operations = []
        if op_type != "none" and op_content:
            try:
                operation_type = OperationType(op_type)
            except ValueError:
                operation_type = OperationType.NONE
            
            if operation_type != OperationType.NONE:
                operations.append(FileOperation(
                    operation_type=operation_type,
                    target_file=request.document_id,
                    content=op_content,
                    position=request.selection_range
                ))
        
        return AIResponse(
            message=message,
            operations=operations,
            sources=sources,
            session_id=session_id,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            requires_confirmation=len(operations) > 0
        )
    
    def _chat_with_agent(
        self,
        request: AIRequest,
        session_id: str,
        rag_context: str,
        sources: list
    ) -> AIResponse:
        """
        Agent模式：使用工具调用循环
        """
        # 创建文档提供者
        doc_provider = DocumentProvider(
            document_content=request.document_content,
            document_id=request.document_id
        )
        
        # 创建工具注册表
        tool_registry = create_default_registry(
            document_provider=doc_provider.get_document,
            document_writer=doc_provider.write_document
        )
        
        # 构建系统提示词
        system_prompt = self._build_agent_system_prompt(
            rag_context=rag_context,
            selected_text=request.selected_text
        )
        
        # 创建LLM调用函数
        factory = get_llm_factory()
        llm = factory.get_llm()
        
        def llm_caller(system_prompt: str, messages: list, tools: list) -> Dict[str, Any]:
            """适配LLM调用到Agent所需格式"""
            return llm.chat_with_tools(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools
            )
        
        # 创建Agent处理器
        agent = AgentProcessor(
            tool_registry=tool_registry,
            llm_caller=llm_caller,
            system_prompt=system_prompt,
            max_iterations=10
        )
        
        # 运行Agent
        agent_context = {
            "document_content": request.document_content,
            "selected_text": request.selected_text,
            "rag_context": rag_context
        }
        
        result = agent.process(
            user_input=request.message,
            session_id=session_id,
            context=agent_context
        )
        
        # 转换Agent结果为AIResponse
        operations = []
        
        # 检查是否有文档修改
        if doc_provider.has_modifications():
            operations.append(FileOperation(
                operation_type=OperationType.REPLACE,
                target_file=request.document_id,
                content=doc_provider.get_modified_content(),
                metadata={"agent_tool_calls": len(result.tool_calls)}
            ))
        
        return AIResponse(
            message=result.message,
            operations=operations,
            sources=sources,
            session_id=session_id,
            tokens_used=result.total_tokens,
            requires_confirmation=len(operations) > 0,
            metadata={
                "agent_iterations": result.iterations,
                "agent_tool_calls": [tc.to_dict() for tc in result.tool_calls]
            }
        )
    
    def _build_agent_system_prompt(
        self,
        rag_context: str = "",
        selected_text: str = ""
    ) -> str:
        """构建Agent系统提示词"""
        prompt_parts = [
            "你是一个智能文档助手，可以帮助用户处理文档相关的任务。",
            "",
            "## 你的能力",
            "1. 阅读和理解文档内容",
            "2. 根据用户需求修改文档",
            "3. 生成新的内容（大纲、摘要、扩写等）",
            "4. 搜索文档中的特定内容",
            "",
            "## 工作流程",
            "1. 首先理解用户的请求",
            "2. 如果需要了解文档内容，使用 read_document 工具",
            "3. 如果需要定位特定内容，使用 search_document 工具",
            "4. 根据需求使用适当的工具完成任务",
            "5. 完成后向用户解释所做的操作",
            "",
            "## 注意事项",
            "- 对文档的修改需要谨慎，确保不会丢失重要内容",
            "- 优先使用 edit_document 进行局部修改，而非 write_document 全量覆盖",
            "- 在执行修改前，最好先读取文档确认当前状态",
        ]
        
        if selected_text:
            prompt_parts.extend([
                "",
                "## 用户选中的文本",
                f"```",
                selected_text,
                "```"
            ])
        
        if rag_context:
            prompt_parts.extend([
                "",
                "## 相关知识库内容",
                rag_context
            ])
        
        return "\n".join(prompt_parts)
    
    def chat_stream(self, request: AIRequest) -> Generator[Dict[str, Any], None, None]:
        """
        流式问答接口
        
        支持两种模式：
        1. Simple模式：直接流式输出
        2. Agent模式：输出工具调用过程和最终结果
        
        Args:
            request: AI请求
        
        Yields:
            流式响应数据块：
            - {"type": "content", "content": "..."}  # 文本内容
            - {"type": "thinking", "iteration": 1}   # Agent思考（仅Agent模式）
            - {"type": "tool_call", "name": "...", "arguments": {...}}  # 工具调用
            - {"type": "tool_result", "name": "...", "result": {...}}   # 工具结果
            - {"type": "done", "session_id": "...", ...}  # 完成
            - {"type": "error", "error": "..."}  # 错误
        """
        try:
            session_id = request.session_id or str(uuid.uuid4())
            
            # RAG检索
            rag_context = ""
            sources = []
            
            if request.project_id:
                kb_service = get_kb_service()
                if kb_service.has_knowledge_base(request.project_id) and request.enable_rag is not False:
                    results = kb_service.search(
                        project_id=request.project_id,
                        query=request.message,
                        top_k=5
                    )
                    if results:
                        rag_context = kb_service.build_context(results)
                        sources = [
                            {
                                "text": r.text[:200] + "...",
                                "score": r.score,
                                "resource_id": r.metadata.get("resource_id")
                            }
                            for r in results[:3]
                        ]
            
            # 判断是否使用Agent模式
            use_agent = request.enable_agent and request.document_content
            
            if use_agent:
                # Agent模式流式处理
                yield from self._chat_stream_with_agent(
                    request=request,
                    session_id=session_id,
                    rag_context=rag_context,
                    sources=sources
                )
            else:
                # Simple模式流式处理
                yield from self._chat_stream_simple(
                    request=request,
                    session_id=session_id,
                    rag_context=rag_context,
                    sources=sources
                )
        
        except Exception as e:
            logger.error(f"流式服务错误: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def _chat_stream_simple(
        self,
        request: AIRequest,
        session_id: str,
        rag_context: str,
        sources: list
    ) -> Generator[Dict[str, Any], None, None]:
        """Simple模式流式处理"""
        # 构建提示词
        system_prompt = build_system_prompt(
            has_knowledge_base=bool(rag_context),
            rag_context=rag_context,
            document_content=request.document_content,
            selected_text=request.selected_text
        )
        
        # 获取上下文
        context = self._context_manager.get_or_create_context(
            session_id=session_id,
            system_prompt=system_prompt
        )
        context.system_prompt = system_prompt
        context.add_message("user", request.message)
        
        # 流式调用LLM
        factory = get_llm_factory()
        llm = factory.get_llm()
        
        messages = context.get_messages_for_llm()
        full_response = ""
        
        for chunk in llm.stream(messages):
            if chunk.content:
                full_response += chunk.content
                yield {
                    "type": "content",
                    "content": chunk.content
                }
        
        # 解析完整响应
        message, op_type, op_content = parse_ai_response(full_response)
        
        # 保存助手回复
        context.add_message("assistant", message)
        
        # 发送最终结果
        yield {
            "type": "done",
            "session_id": session_id,
            "operation": {
                "type": op_type,
                "content": op_content
            } if op_type != "none" else None,
            "sources": sources if sources else None
        }
    
    def _chat_stream_with_agent(
        self,
        request: AIRequest,
        session_id: str,
        rag_context: str,
        sources: list
    ) -> Generator[Dict[str, Any], None, None]:
        """Agent模式流式处理"""
        # 创建文档提供者
        doc_provider = DocumentProvider(
            document_content=request.document_content,
            document_id=request.document_id
        )
        
        # 创建工具注册表
        tool_registry = create_default_registry(
            document_provider=doc_provider.get_document,
            document_writer=doc_provider.write_document
        )
        
        # 构建系统提示词
        system_prompt = self._build_agent_system_prompt(
            rag_context=rag_context,
            selected_text=request.selected_text
        )
        
        # 创建LLM调用函数
        factory = get_llm_factory()
        llm = factory.get_llm()
        
        def llm_caller(system_prompt: str, messages: list, tools: list) -> Dict[str, Any]:
            return llm.chat_with_tools(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools
            )
        
        # 创建Agent处理器
        agent = AgentProcessor(
            tool_registry=tool_registry,
            llm_caller=llm_caller,
            system_prompt=system_prompt,
            max_iterations=10
        )
        
        # 使用流式处理
        agent_context = {
            "document_content": request.document_content,
            "selected_text": request.selected_text,
            "rag_context": rag_context
        }
        
        result = None
        for event in agent.process_stream(
            user_input=request.message,
            session_id=session_id,
            context=agent_context
        ):
            yield event
            if event.get("type") == "done":
                result = event.get("result")
        
        # 构建最终操作
        if result and doc_provider.has_modifications():
            yield {
                "type": "operation",
                "operation": {
                    "type": "replace",
                    "target_file": request.document_id,
                    "content": doc_provider.get_modified_content()
                }
            }
        
        # 发送来源信息
        if sources:
            yield {
                "type": "sources",
                "sources": sources
            }
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取会话历史"""
        if session_id not in self._context_manager._sessions:
            return {"error": "会话不存在"}
        
        context = self._context_manager._sessions[session_id]
        messages = context.get_recent_messages(limit)
        
        return {
            "session_id": session_id,
            "messages": [m.to_dict() for m in messages],
            "total_tokens": context.total_tokens
        }
    
    def clear_session(self, session_id: str):
        """清空会话"""
        self._context_manager.delete_session(session_id)


# 全局AI服务实例
_global_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取全局AI服务"""
    global _global_ai_service
    if _global_ai_service is None:
        _global_ai_service = AIService()
    return _global_ai_service
