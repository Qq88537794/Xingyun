"""
智谱清言 (Zhipu AI / ChatGLM) 模型实现
官方文档: https://open.bigmodel.cn/dev/api
"""

import json
import logging
from typing import List, Dict, Any, Optional, Generator

from .base import BaseLLM, LLMResponse, TokenUsage, Message, ModelProvider

logger = logging.getLogger(__name__)


class ZhipuLLM(BaseLLM):
    """
    智谱清言 LLM 实现
    支持 GLM-4, GLM-4-Flash, GLM-4-Air 等模型
    """
    
    # 默认配置
    DEFAULT_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_MODEL = "glm-4.5-flash"  # 免费模型，用于开发测试
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        "glm-4.5-flash": {"max_tokens": 8192, "context_length": 1048576},
    }
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        api_base: str = DEFAULT_API_BASE,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        初始化智谱清言LLM
        
        Args:
            api_key: 智谱API密钥
            model_name: 模型名称，默认 glm-4-flash
            api_base: API基础URL
            timeout: 超时时间
            max_retries: 重试次数
        """
        super().__init__(
            api_key=api_key,
            model_name=model_name,
            api_base=api_base or self.DEFAULT_API_BASE,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs
        )
        
        # 验证模型名称
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"未知模型 {model_name}，将尝试调用")
        
        self._client = None
    
    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.ZHIPU
    
    def _get_client(self):
        """获取/创建HTTP客户端"""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(timeout=self.timeout)
            except ImportError:
                import requests
                self._client = requests.Session()
        return self._client
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _call_api(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        同步调用智谱API
        """
        # 构建请求体
        payload = {
            "model": self.model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # 添加额外参数
        for key in ['top_p', 'do_sample', 'stop']:
            if key in kwargs:
                payload[key] = kwargs[key]
        
        # 发送请求
        url = f"{self.api_base}/chat/completions"
        
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self._build_headers(),
                    json=payload
                )
        except ImportError:
            import requests
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout
            )
        
        # 检查响应
        if response.status_code != 200:
            error_msg = f"智谱API错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 解析响应
        data = response.json()
        
        # 提取内容
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        finish_reason = data.get('choices', [{}])[0].get('finish_reason', 'stop')
        
        # 提取token使用情况
        usage_data = data.get('usage', {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get('prompt_tokens', 0),
            completion_tokens=usage_data.get('completion_tokens', 0),
            total_tokens=usage_data.get('total_tokens', 0)
        )
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            provider=self.provider.value,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=data
        )
    
    def _stream_api(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """
        流式调用智谱API
        """
        # 构建请求体
        payload = {
            "model": self.model_name,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        url = f"{self.api_base}/chat/completions"
        
        full_content = ""
        usage = TokenUsage()
        finish_reason = "stop"
        
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    url,
                    headers=self._build_headers(),
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        raise Exception(f"智谱API错误: {response.status_code}")
                    
                    for line in response.iter_lines():
                        if not line or line.startswith(':'):
                            continue
                        
                        if line.startswith('data: '):
                            line = line[6:]  # 移除 'data: ' 前缀
                        
                        if line == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            
                            if content:
                                full_content += content
                                yield content
                            
                            # 检查是否完成
                            if chunk.get('choices', [{}])[0].get('finish_reason'):
                                finish_reason = chunk['choices'][0]['finish_reason']
                            
                            # 获取usage信息(通常在最后一个chunk)
                            if 'usage' in chunk:
                                usage_data = chunk['usage']
                                usage = TokenUsage(
                                    prompt_tokens=usage_data.get('prompt_tokens', 0),
                                    completion_tokens=usage_data.get('completion_tokens', 0),
                                    total_tokens=usage_data.get('total_tokens', 0)
                                )
                                
                        except json.JSONDecodeError:
                            continue
                            
        except ImportError:
            # 使用 requests 的流式处理
            import requests
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"智谱API错误: {response.status_code}")
            
            for line in response.iter_lines(decode_unicode=True):
                if not line or line.startswith(':'):
                    continue
                
                if line.startswith('data: '):
                    line = line[6:]
                
                if line == '[DONE]':
                    break
                
                try:
                    chunk = json.loads(line)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content', '')
                    
                    if content:
                        full_content += content
                        yield content
                        
                except json.JSONDecodeError:
                    continue
        
        # 返回最终响应
        return LLMResponse(
            content=full_content,
            model=self.model_name,
            provider=self.provider.value,
            usage=usage,
            finish_reason=finish_reason
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        info = self.SUPPORTED_MODELS.get(self.model_name, {})
        return {
            'model': self.model_name,
            'provider': self.provider.value,
            'max_tokens': info.get('max_tokens', 4096),
            'context_length': info.get('context_length', 128000)
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
        
        智谱API原生支持function calling
        
        Args:
            system_prompt: 系统提示词
            messages: 消息列表 (包含tool和tool_call消息)
            tools: 工具定义列表
            temperature: 温度参数
        
        Returns:
            标准化的工具调用响应
        """
        # 构建完整消息列表
        full_messages = [{'role': 'system', 'content': system_prompt}]
        
        for msg in messages:
            if msg.get('role') == 'tool':
                # 智谱的工具结果格式
                full_messages.append({
                    'role': 'tool',
                    'content': msg.get('content', ''),
                    'tool_call_id': msg.get('tool_call_id', '')
                })
            elif msg.get('role') == 'assistant' and msg.get('tool_calls'):
                # 助手的工具调用消息
                full_messages.append({
                    'role': 'assistant',
                    'content': msg.get('content', '') or None,
                    'tool_calls': msg['tool_calls']
                })
            else:
                full_messages.append({
                    'role': msg.get('role'),
                    'content': msg.get('content', '')
                })
        
        # 构建请求体
        payload = {
            "model": self.model_name,
            "messages": full_messages,
            "temperature": temperature,
            "stream": False
        }
        
        # 添加工具定义
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        # 发送请求
        url = f"{self.api_base}/chat/completions"
        
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self._build_headers(),
                    json=payload
                )
        except ImportError:
            import requests
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout
            )
        
        # 检查响应
        if response.status_code != 200:
            error_msg = f"智谱API错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 解析响应
        data = response.json()
        choice = data.get('choices', [{}])[0]
        message = choice.get('message', {})
        
        # 提取内容
        content = message.get('content', '') or ''
        finish_reason = choice.get('finish_reason', 'stop')
        
        # 提取工具调用
        tool_calls = message.get('tool_calls', [])
        
        # 标准化工具调用格式
        normalized_tool_calls = []
        for tc in tool_calls:
            func = tc.get('function', {})
            # 智谱返回的arguments是字符串，需要解析
            arguments = func.get('arguments', '{}')
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            
            normalized_tool_calls.append({
                'id': tc.get('id', ''),
                'function': {
                    'name': func.get('name', ''),
                    'arguments': arguments
                }
            })
        
        # 判断finish_reason
        if normalized_tool_calls:
            finish_reason = 'tool_calls'
        
        # 提取token使用情况
        usage_data = data.get('usage', {})
        
        return {
            "content": content,
            "tool_calls": normalized_tool_calls,
            "finish_reason": finish_reason,
            "usage": {
                "prompt_tokens": usage_data.get('prompt_tokens', 0),
                "completion_tokens": usage_data.get('completion_tokens', 0),
                "total_tokens": usage_data.get('total_tokens', 0)
            }
        }
