"""
多轮对话上下文管理
管理对话历史和上下文窗口
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """对话消息"""
    role: str              # 'user', 'assistant', 'system'
    content: str           # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0   # 估算的token数
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'token_count': self.token_count,
            'metadata': self.metadata
        }


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    system_prompt: Optional[str] = None
    total_tokens: int = 0
    max_tokens: int = 8000      # 上下文窗口最大token数
    max_messages: int = 50       # 最大消息数
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """添加消息"""
        token_count = self._estimate_tokens(content)
        
        message = Message(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        self.total_tokens += token_count
        self.updated_at = datetime.now()
        
        # 检查是否需要压缩
        self._maybe_compress()
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def _maybe_compress(self):
        """检查并执行上下文压缩"""
        # 消息数量超限
        while len(self.messages) > self.max_messages:
            removed = self.messages.pop(0)
            self.total_tokens -= removed.token_count
        
        # Token数超限
        while self.total_tokens > self.max_tokens and len(self.messages) > 2:
            removed = self.messages.pop(0)
            self.total_tokens -= removed.token_count
    
    def get_messages_for_llm(
        self,
        include_system: bool = True,
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        获取用于LLM的消息列表
        
        Args:
            include_system: 是否包含系统提示
            max_tokens: 最大token限制
        
        Returns:
            消息字典列表
        """
        max_tokens = max_tokens or self.max_tokens
        result = []
        current_tokens = 0
        
        # 添加系统提示
        if include_system and self.system_prompt:
            system_tokens = self._estimate_tokens(self.system_prompt)
            result.append({
                'role': 'system',
                'content': self.system_prompt
            })
            current_tokens += system_tokens
        
        # 从最新消息开始，向前获取
        selected_messages = []
        for message in reversed(self.messages):
            if current_tokens + message.token_count > max_tokens:
                break
            selected_messages.insert(0, {
                'role': message.role,
                'content': message.content
            })
            current_tokens += message.token_count
        
        result.extend(selected_messages)
        return result
    
    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """获取最近的n条消息"""
        return self.messages[-n:]
    
    def summarize_old_messages(self, keep_recent: int = 5) -> str:
        """
        生成旧消息的摘要
        用于长对话的上下文压缩
        """
        if len(self.messages) <= keep_recent:
            return ""
        
        old_messages = self.messages[:-keep_recent]
        
        # 简单的摘要生成
        summary_parts = []
        for msg in old_messages:
            if msg.role == 'user':
                summary_parts.append(f"用户问: {msg.content[:100]}...")
            elif msg.role == 'assistant':
                summary_parts.append(f"助手答: {msg.content[:100]}...")
        
        return "之前的对话摘要:\n" + "\n".join(summary_parts[-10:])  # 保留最后10条摘要
    
    def clear(self):
        """清空对话历史"""
        self.messages = []
        self.total_tokens = 0
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'messages': [m.to_dict() for m in self.messages],
            'system_prompt': self.system_prompt,
            'total_tokens': self.total_tokens,
            'max_tokens': self.max_tokens,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


class ContextManager:
    """
    上下文管理器
    管理多个对话会话的上下文
    """
    
    def __init__(
        self,
        max_sessions: int = 100,
        default_max_tokens: int = 8000,
        default_max_messages: int = 50
    ):
        """
        初始化上下文管理器
        
        Args:
            max_sessions: 最大会话数
            default_max_tokens: 默认最大token数
            default_max_messages: 默认最大消息数
        """
        self.max_sessions = max_sessions
        self.default_max_tokens = default_max_tokens
        self.default_max_messages = default_max_messages
        
        # 使用LRU缓存管理会话
        self._sessions: Dict[str, ConversationContext] = {}
        self._access_order: deque = deque()
    
    def get_or_create_context(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_messages: Optional[int] = None
    ) -> ConversationContext:
        """
        获取或创建对话上下文
        
        Args:
            session_id: 会话ID
            system_prompt: 系统提示
            max_tokens: 最大token数
            max_messages: 最大消息数
        
        Returns:
            对话上下文
        """
        if session_id in self._sessions:
            # 更新访问顺序
            if session_id in self._access_order:
                self._access_order.remove(session_id)
            self._access_order.append(session_id)
            
            return self._sessions[session_id]
        
        # 检查是否需要清理旧会话
        self._maybe_cleanup()
        
        # 创建新会话
        context = ConversationContext(
            session_id=session_id,
            system_prompt=system_prompt,
            max_tokens=max_tokens or self.default_max_tokens,
            max_messages=max_messages or self.default_max_messages
        )
        
        self._sessions[session_id] = context
        self._access_order.append(session_id)
        
        logger.debug(f"创建新会话: {session_id}")
        return context
    
    def _maybe_cleanup(self):
        """清理旧会话"""
        while len(self._sessions) >= self.max_sessions:
            # 移除最旧的会话
            oldest_id = self._access_order.popleft()
            if oldest_id in self._sessions:
                del self._sessions[oldest_id]
                logger.debug(f"清理旧会话: {oldest_id}")
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        向会话添加消息
        
        Args:
            session_id: 会话ID
            role: 角色
            content: 内容
            metadata: 元数据
        """
        context = self.get_or_create_context(session_id)
        context.add_message(role, content, metadata)
    
    def get_messages(
        self,
        session_id: str,
        include_system: bool = True,
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        获取会话的消息列表(用于LLM)
        """
        if session_id not in self._sessions:
            return []
        
        return self._sessions[session_id].get_messages_for_llm(
            include_system=include_system,
            max_tokens=max_tokens
        )
    
    def set_system_prompt(self, session_id: str, prompt: str):
        """设置系统提示"""
        context = self.get_or_create_context(session_id)
        context.system_prompt = prompt
    
    def clear_session(self, session_id: str):
        """清空会话"""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._access_order:
            self._access_order.remove(session_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id not in self._sessions:
            return None
        
        context = self._sessions[session_id]
        return {
            'session_id': session_id,
            'message_count': len(context.messages),
            'total_tokens': context.total_tokens,
            'created_at': context.created_at.isoformat(),
            'updated_at': context.updated_at.isoformat()
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return [
            self.get_session_info(sid)
            for sid in self._sessions.keys()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_messages = sum(len(c.messages) for c in self._sessions.values())
        total_tokens = sum(c.total_tokens for c in self._sessions.values())
        
        return {
            'active_sessions': len(self._sessions),
            'max_sessions': self.max_sessions,
            'total_messages': total_messages,
            'total_tokens': total_tokens
        }


# 全局上下文管理器
_global_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器"""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = ContextManager()
    return _global_context_manager
