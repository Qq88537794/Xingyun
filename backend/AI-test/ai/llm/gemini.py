"""
Google Gemini 模型实现
官方文档: https://ai.google.dev/docs
"""

import json
import logging
from typing import List, Dict, Any, Optional, Generator

from .base import BaseLLM, LLMResponse, TokenUsage, Message, ModelProvider

logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """
    Google Gemini LLM 实现
    支持 Gemini 2.0, 1.5 Pro, 1.5 Flash 等模型
    """
    
    # 默认配置
    DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-3-flash-preview" # 默认使用最新的Gemini 3 Flash预览模型
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        'gemini-3-flash-preview': {'max_tokens': 8192, 'context_length': 128000},
        'gemini-2.5-pro': {'max_tokens': 8192, 'context_length': 128000},
        'gemini-2.5-flash': {'max_tokens': 8192, 'context_length': 128000},
        'gemini-2.5-flash-preview-tts': {'max_tokens': 8192, 'context_length': 128000},
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
        初始化Gemini LLM
        
        Args:
            api_key: Google AI API密钥
            model_name: 模型名称，默认 gemini-2.0-flash-exp
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
        
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"未知模型 {model_name}，将尝试调用")
    
    @property
    def provider(self) -> ModelProvider:
        return ModelProvider.GEMINI
    
    def _convert_messages_to_gemini_format(self, messages: List[Message]) -> Dict[str, Any]:
        """
        将标准消息格式转换为Gemini API格式
        
        Gemini使用不同的消息结构:
        - 'user' 和 'model' 角色
        - system prompt通过 system_instruction 传递
        """
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == 'system':
                system_instruction = msg.content
            elif msg.role == 'user':
                contents.append({
                    'role': 'user',
                    'parts': [{'text': msg.content}]
                })
            elif msg.role == 'assistant':
                contents.append({
                    'role': 'model',
                    'parts': [{'text': msg.content}]
                })
        
        result = {'contents': contents}
        
        if system_instruction:
            result['system_instruction'] = {
                'parts': [{'text': system_instruction}]
            }
        
        return result
    
    def _build_generation_config(
        self,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """构建生成配置"""
        config = {
            'temperature': temperature,
        }
        
        if max_tokens:
            config['maxOutputTokens'] = max_tokens
        
        # 添加其他支持的参数
        for key, gemini_key in [
            ('top_p', 'topP'),
            ('top_k', 'topK'),
            ('stop_sequences', 'stopSequences'),
        ]:
            if key in kwargs:
                config[gemini_key] = kwargs[key]
        
        return config
    
    def _call_api(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        同步调用Gemini API
        """
        # 构建请求体
        payload = self._convert_messages_to_gemini_format(messages)
        payload['generationConfig'] = self._build_generation_config(
            temperature, max_tokens, **kwargs
        )
        
        # 构建URL
        url = f"{self.api_base}/models/{self.model_name}:generateContent?key={self.api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 发送请求
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except ImportError:
            import requests
            response = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
        
        # 检查响应
        if response.status_code != 200:
            error_msg = f"Gemini API错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 解析响应
        data = response.json()
        
        # 提取内容
        candidates = data.get('candidates', [])
        if not candidates:
            raise Exception("Gemini API返回空响应")
        
        content_parts = candidates[0].get('content', {}).get('parts', [])
        content = ''.join(part.get('text', '') for part in content_parts)
        
        finish_reason = candidates[0].get('finishReason', 'STOP')
        
        # 提取token使用情况
        usage_metadata = data.get('usageMetadata', {})
        usage = TokenUsage(
            prompt_tokens=usage_metadata.get('promptTokenCount', 0),
            completion_tokens=usage_metadata.get('candidatesTokenCount', 0),
            total_tokens=usage_metadata.get('totalTokenCount', 0)
        )
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            provider=self.provider.value,
            usage=usage,
            finish_reason=finish_reason.lower(),
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
        流式调用Gemini API
        """
        # 构建请求体
        payload = self._convert_messages_to_gemini_format(messages)
        payload['generationConfig'] = self._build_generation_config(
            temperature, max_tokens, **kwargs
        )
        
        # 使用streamGenerateContent端点
        url = f"{self.api_base}/models/{self.model_name}:streamGenerateContent?key={self.api_key}&alt=sse"
        
        headers = {'Content-Type': 'application/json'}
        
        full_content = ""
        usage = TokenUsage()
        finish_reason = "stop"
        
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        raise Exception(f"Gemini API错误: {response.status_code}")
                    
                    for line in response.iter_lines():
                        if not line:
                            continue
                        
                        if line.startswith('data: '):
                            line = line[6:]
                        
                        try:
                            chunk = json.loads(line)
                            
                            candidates = chunk.get('candidates', [])
                            if candidates:
                                content_parts = candidates[0].get('content', {}).get('parts', [])
                                for part in content_parts:
                                    text = part.get('text', '')
                                    if text:
                                        full_content += text
                                        yield text
                                
                                if candidates[0].get('finishReason'):
                                    finish_reason = candidates[0]['finishReason'].lower()
                            
                            # 获取usage信息
                            if 'usageMetadata' in chunk:
                                usage_metadata = chunk['usageMetadata']
                                usage = TokenUsage(
                                    prompt_tokens=usage_metadata.get('promptTokenCount', 0),
                                    completion_tokens=usage_metadata.get('candidatesTokenCount', 0),
                                    total_tokens=usage_metadata.get('totalTokenCount', 0)
                                )
                                
                        except json.JSONDecodeError:
                            continue
                            
        except ImportError:
            import requests
            response = requests.post(
                url, headers=headers, json=payload, stream=True, timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API错误: {response.status_code}")
            
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                
                if line.startswith('data: '):
                    line = line[6:]
                
                try:
                    chunk = json.loads(line)
                    candidates = chunk.get('candidates', [])
                    if candidates:
                        content_parts = candidates[0].get('content', {}).get('parts', [])
                        for part in content_parts:
                            text = part.get('text', '')
                            if text:
                                full_content += text
                                yield text
                except json.JSONDecodeError:
                    continue
        
        return LLMResponse(
            content=full_content,
            model=self.model_name,
            provider=self.provider.value,
            usage=usage,
            finish_reason=finish_reason
        )
    
    def count_tokens(self, text: str) -> int:
        """
        使用Gemini API计算token数
        """
        url = f"{self.api_base}/models/{self.model_name}:countTokens?key={self.api_key}"
        
        payload = {
            'contents': [{
                'parts': [{'text': text}]
            }]
        }
        
        try:
            import httpx
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    url,
                    headers={'Content-Type': 'application/json'},
                    json=payload
                )
            data = response.json()
            return data.get('totalTokens', super().count_tokens(text))
        except Exception as e:
            logger.warning(f"Token计数失败，使用估算值: {e}")
            return super().count_tokens(text)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        info = self.SUPPORTED_MODELS.get(self.model_name, {})
        return {
            'model': self.model_name,
            'provider': self.provider.value,
            'max_tokens': info.get('max_tokens', 8192),
            'context_length': info.get('context_length', 1048576)
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
        
        Gemini API支持Function Calling
        
        Args:
            system_prompt: 系统提示词
            messages: 消息列表 (包含tool和tool_call消息)
            tools: 工具定义列表 (OpenAI格式)
            temperature: 温度参数
        
        Returns:
            标准化的工具调用响应
        """
        # 转换工具格式为Gemini格式
        gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        # 构建消息内容
        contents = []
        
        for msg in messages:
            if msg.get('role') == 'user':
                contents.append({
                    'role': 'user',
                    'parts': [{'text': msg.get('content', '')}]
                })
            elif msg.get('role') == 'assistant':
                parts = []
                if msg.get('content'):
                    parts.append({'text': msg['content']})
                # 处理工具调用
                if msg.get('tool_calls'):
                    for tc in msg['tool_calls']:
                        func = tc.get('function', {})
                        parts.append({
                            'functionCall': {
                                'name': func.get('name', ''),
                                'args': func.get('arguments', {})
                            }
                        })
                contents.append({
                    'role': 'model',
                    'parts': parts
                })
            elif msg.get('role') == 'tool':
                # Gemini的工具结果格式
                contents.append({
                    'role': 'user',
                    'parts': [{
                        'functionResponse': {
                            'name': msg.get('name', ''),
                            'response': {'result': msg.get('content', '')}
                        }
                    }]
                })
        
        # 构建请求体
        payload = {
            'contents': contents,
            'generationConfig': self._build_generation_config(temperature, None, **kwargs)
        }
        
        # 添加系统指令
        if system_prompt:
            payload['system_instruction'] = {
                'parts': [{'text': system_prompt}]
            }
        
        # 添加工具
        if gemini_tools:
            payload['tools'] = [{'function_declarations': gemini_tools}]
        
        # 构建URL
        url = f"{self.api_base}/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        
        # 发送请求
        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except ImportError:
            import requests
            response = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
        
        # 检查响应
        if response.status_code != 200:
            error_msg = f"Gemini API错误: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 解析响应
        data = response.json()
        candidates = data.get('candidates', [])
        
        if not candidates:
            raise Exception("Gemini API返回空响应")
        
        # 提取内容和工具调用
        content_parts = candidates[0].get('content', {}).get('parts', [])
        content = ""
        tool_calls = []
        
        for part in content_parts:
            if 'text' in part:
                content += part['text']
            elif 'functionCall' in part:
                fc = part['functionCall']
                tool_calls.append({
                    'id': f"call_{len(tool_calls)}",  # Gemini不提供call id，我们生成一个
                    'function': {
                        'name': fc.get('name', ''),
                        'arguments': fc.get('args', {})
                    }
                })
        
        # 判断finish_reason
        finish_reason = candidates[0].get('finishReason', 'STOP').lower()
        if tool_calls:
            finish_reason = 'tool_calls'
        
        # 提取token使用情况
        usage_metadata = data.get('usageMetadata', {})
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "usage": {
                "prompt_tokens": usage_metadata.get('promptTokenCount', 0),
                "completion_tokens": usage_metadata.get('candidatesTokenCount', 0),
                "total_tokens": usage_metadata.get('totalTokenCount', 0)
            }
        }
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将OpenAI格式的工具定义转换为Gemini格式
        
        OpenAI格式:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": {...}
            }
        }
        
        Gemini格式:
        {
            "name": "...",
            "description": "...",
            "parameters": {...}
        }
        """
        gemini_tools = []
        for tool in tools:
            if tool.get('type') == 'function':
                func = tool.get('function', {})
                gemini_tools.append({
                    'name': func.get('name', ''),
                    'description': func.get('description', ''),
                    'parameters': func.get('parameters', {})
                })
        return gemini_tools
