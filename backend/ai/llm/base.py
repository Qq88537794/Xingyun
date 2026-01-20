"""
LLM基类定义
提供统一的模型调用接口封装
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Generator, AsyncGenerator
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """模型提供商枚举"""
    ZHIPU = "zhipu"           # 智谱清言
    GEMINI = "gemini"         # Google Gemini
    OPENAI = "openai"         # OpenAI (预留)
    ANTHROPIC = "anthropic"   # Anthropic Claude (预留)
    LOCAL = "local"           # 本地模型 (预留)


@dataclass
class TokenUsage:
    """Token使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens
        }


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str                           # 生成的内容
    model: str                             # 使用的模型
    provider: str                          # 提供商
    usage: TokenUsage = field(default_factory=TokenUsage)  # Token使用情况
    finish_reason: str = "stop"            # 结束原因
    latency_ms: float = 0.0               # 响应延迟(毫秒)
    raw_response: Optional[Dict] = None    # 原始响应数据
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'model': self.model,
            'provider': self.provider,
            'usage': self.usage.to_dict(),
            'finish_reason': self.finish_reason,
            'latency_ms': self.latency_ms
        }


@dataclass
class Message:
    """对话消息"""
    role: str       # 'system', 'user', 'assistant'
    content: str    # 消息内容
    
    def to_dict(self) -> Dict[str, str]:
        return {'role': self.role, 'content': self.content}


class BaseLLM(ABC):
    """
    LLM基类
    所有具体模型实现都应继承此类
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str,
        api_base: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        初始化LLM
        
        Args:
            api_key: API密钥
            model_name: 模型名称
            api_base: API基础URL (可选)
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.model_name = model_name
        self.api_base = api_base
        self.timeout = timeout
        self.max_retries = max_retries
        self.extra_config = kwargs
        
        # 统计信息
        self._total_tokens = 0
        self._total_requests = 0
        self._failed_requests = 0
    
    @property
    @abstractmethod
    def provider(self) -> ModelProvider:
        """返回模型提供商"""
        pass
    
    @abstractmethod
    def _call_api(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        调用API (同步)
        子类必须实现此方法
        """
        pass
    
    @abstractmethod
    def _stream_api(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """
        流式调用API
        子类必须实现此方法
        返回生成器，逐字符/逐chunk返回内容
        """
        pass
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse | Generator[str, None, LLMResponse]:
        """
        对话接口 (统一入口)
        
        Args:
            messages: 消息列表 [{'role': 'user', 'content': '...'}]
            temperature: 温度参数 (0-1)
            max_tokens: 最大生成token数
            stream: 是否流式输出
        
        Returns:
            LLMResponse 或 流式生成器
        """
        # 转换为Message对象
        msg_objects = [Message(**m) for m in messages]
        
        start_time = time.time()
        
        try:
            if stream:
                return self._stream_with_retry(
                    msg_objects, temperature, max_tokens, **kwargs
                )
            else:
                response = self._call_with_retry(
                    msg_objects, temperature, max_tokens, **kwargs
                )
                response.latency_ms = (time.time() - start_time) * 1000
                self._total_requests += 1
                self._total_tokens += response.usage.total_tokens
                return response
                
        except Exception as e:
            self._failed_requests += 1
            logger.error(f"LLM调用失败: {str(e)}")
            raise
    
    def _call_with_retry(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> LLMResponse:
        """带重试的API调用"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return self._call_api(messages, temperature, max_tokens, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        raise last_exception
    
    def _stream_with_retry(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """带重试的流式API调用"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return self._stream_api(messages, temperature, max_tokens, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"流式API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        raise last_exception
    
    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        简单对话接口
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词(可选)
        
        Returns:
            模型生成的文本
        """
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        response = self.chat(messages, **kwargs)
        return response.content
    
    def count_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        默认实现：简单按字符数估算
        子类可覆盖实现更精确的计算
        """
        # 粗略估算: 中文约1.5字符/token, 英文约4字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'provider': self.provider.value,
            'model': self.model_name,
            'total_requests': self._total_requests,
            'failed_requests': self._failed_requests,
            'total_tokens': self._total_tokens,
            'success_rate': (
                (self._total_requests - self._failed_requests) / self._total_requests 
                if self._total_requests > 0 else 0
            )
        }
    
    def chat_with_tools(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带工具调用的对话接口
        
        用于Agent模式，支持LLM调用工具
        
        Args:
            system_prompt: 系统提示词
            messages: 消息列表 (包含tool和tool_call消息)
            tools: 工具定义列表
            temperature: 温度参数
        
        Returns:
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
                "finish_reason": "stop" | "tool_calls",
                "usage": {"total_tokens": 100}
            }
        """
        # 默认实现: 不支持工具调用，直接调用普通chat
        # 子类应覆盖此方法实现具体的工具调用逻辑
        logger.warning(f"{self.__class__.__name__} 不支持原生工具调用，使用模拟实现")
        
        # 将工具描述添加到系统提示词
        tool_descriptions = self._format_tools_for_prompt(tools)
        enhanced_system = f"{system_prompt}\n\n{tool_descriptions}"
        
        # 构建消息列表
        full_messages = [{'role': 'system', 'content': enhanced_system}]
        for msg in messages:
            if msg.get('role') == 'tool':
                # 将工具结果转换为user消息
                full_messages.append({
                    'role': 'user',
                    'content': f"[工具 {msg.get('name')} 执行结果]: {msg.get('content')}"
                })
            elif msg.get('role') == 'assistant' and msg.get('tool_calls'):
                # 将工具调用转换为助手消息
                tool_call_text = "\n".join([
                    f"调用工具: {tc['function']['name']}({tc['function'].get('arguments', {})})"
                    for tc in msg['tool_calls']
                ])
                full_messages.append({
                    'role': 'assistant',
                    'content': f"{msg.get('content', '')}\n{tool_call_text}".strip()
                })
            else:
                full_messages.append(msg)
        
        # 调用普通chat
        response = self.chat(full_messages, temperature=temperature, **kwargs)
        
        return {
            "content": response.content,
            "tool_calls": [],  # 默认实现不支持工具调用
            "finish_reason": "stop",
            "usage": {"total_tokens": response.usage.total_tokens}
        }
    
    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """将工具定义格式化为提示词"""
        if not tools:
            return ""
        
        lines = ["## 可用工具", ""]
        for tool in tools:
            func = tool.get('function', {})
            lines.append(f"### {func.get('name', 'unknown')}")
            lines.append(func.get('description', ''))
            
            params = func.get('parameters', {}).get('properties', {})
            if params:
                lines.append("\n参数:")
                for name, spec in params.items():
                    lines.append(f"  - {name}: {spec.get('description', '')}")
            lines.append("")
        
        return "\n".join(lines)
    
    def reset_stats(self):
        """重置统计信息"""
        self._total_tokens = 0
        self._total_requests = 0
        self._failed_requests = 0
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(model={self.model_name}, provider={self.provider.value})>"
