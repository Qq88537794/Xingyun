"""
LLM工厂类
提供统一的模型创建和管理接口
实现模型切换和降级策略
"""

import logging
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .base import BaseLLM, ModelProvider, LLMResponse
from .zhipu import ZhipuLLM
from .gemini import GeminiLLM

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """降级策略"""
    NONE = "none"           # 不降级，直接失败
    SEQUENTIAL = "sequential"  # 按顺序尝试备用模型
    ROUND_ROBIN = "round_robin"  # 轮询负载均衡


class LLMFactory:
    """
    LLM工厂类
    
    功能:
    1. 统一创建不同提供商的LLM实例
    2. 管理多个LLM实例
    3. 实现模型切换和降级策略
    4. 统一的调用接口
    """
    
    # 注册的LLM实现类
    _registry: Dict[ModelProvider, Type[BaseLLM]] = {
        ModelProvider.ZHIPU: ZhipuLLM,
        ModelProvider.GEMINI: GeminiLLM,
    }
    
    def __init__(
        self,
        default_provider: ModelProvider = ModelProvider.ZHIPU,
        fallback_strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL
    ):
        """
        初始化LLM工厂
        
        Args:
            default_provider: 默认模型提供商
            fallback_strategy: 降级策略
        """
        self.default_provider = default_provider
        self.fallback_strategy = fallback_strategy
        
        # 已创建的LLM实例
        self._instances: Dict[str, BaseLLM] = {}
        
        # 降级顺序
        self._fallback_order: List[str] = []
        
        # 轮询索引
        self._robin_index = 0
    
    @classmethod
    def register(cls, provider: ModelProvider, llm_class: Type[BaseLLM]):
        """注册新的LLM实现"""
        cls._registry[provider] = llm_class
        logger.info(f"注册LLM提供商: {provider.value}")
    
    def create_llm(
        self,
        provider: ModelProvider,
        api_key: str,
        model_name: Optional[str] = None,
        instance_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
        """
        创建LLM实例
        
        Args:
            provider: 模型提供商
            api_key: API密钥
            model_name: 模型名称(可选,使用默认值)
            instance_name: 实例名称(用于管理多个实例)
            **kwargs: 其他配置参数
        
        Returns:
            LLM实例
        """
        if provider not in self._registry:
            raise ValueError(f"不支持的LLM提供商: {provider.value}")
        
        llm_class = self._registry[provider]
        
        # 构建参数
        init_kwargs = {'api_key': api_key, **kwargs}
        if model_name:
            init_kwargs['model_name'] = model_name
        
        # 创建实例
        llm = llm_class(**init_kwargs)
        
        # 存储实例
        name = instance_name or f"{provider.value}_{model_name or 'default'}"
        self._instances[name] = llm
        
        # 添加到降级顺序
        if name not in self._fallback_order:
            self._fallback_order.append(name)
        
        logger.info(f"创建LLM实例: {name}")
        return llm
    
    def get_llm(self, name: Optional[str] = None) -> BaseLLM:
        """
        获取LLM实例
        
        Args:
            name: 实例名称，为空则返回默认实例
        """
        if not self._instances:
            raise RuntimeError("没有可用的LLM实例，请先调用create_llm创建")
        
        if name:
            if name not in self._instances:
                raise KeyError(f"LLM实例不存在: {name}")
            return self._instances[name]
        
        # 返回默认实例(第一个)
        return list(self._instances.values())[0]
    
    def set_fallback_order(self, order: List[str]):
        """
        设置降级顺序
        
        Args:
            order: 实例名称列表，按优先级排序
        """
        # 验证所有实例都存在
        for name in order:
            if name not in self._instances:
                raise KeyError(f"LLM实例不存在: {name}")
        
        self._fallback_order = order
        logger.info(f"设置降级顺序: {order}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        preferred_instance: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        统一的对话接口，支持自动降级
        
        Args:
            messages: 消息列表
            preferred_instance: 首选实例名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            **kwargs: 其他参数
        
        Returns:
            LLMResponse
        """
        if not self._instances:
            raise RuntimeError("没有可用的LLM实例")
        
        # 确定调用顺序
        if self.fallback_strategy == FallbackStrategy.NONE:
            instances_to_try = [preferred_instance] if preferred_instance else [self._fallback_order[0]]
        elif self.fallback_strategy == FallbackStrategy.ROUND_ROBIN:
            # 轮询策略
            self._robin_index = (self._robin_index + 1) % len(self._fallback_order)
            instances_to_try = [self._fallback_order[self._robin_index]]
        else:
            # 顺序降级策略
            if preferred_instance and preferred_instance in self._instances:
                instances_to_try = [preferred_instance] + [
                    n for n in self._fallback_order if n != preferred_instance
                ]
            else:
                instances_to_try = self._fallback_order.copy()
        
        last_error = None
        
        for instance_name in instances_to_try:
            if instance_name not in self._instances:
                continue
            
            llm = self._instances[instance_name]
            try:
                logger.debug(f"尝试使用LLM: {instance_name}")
                response = llm.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    **kwargs
                )
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"LLM {instance_name} 调用失败: {str(e)}")
                
                if self.fallback_strategy == FallbackStrategy.NONE:
                    raise
                
                continue
        
        # 所有实例都失败
        raise RuntimeError(f"所有LLM实例调用失败。最后错误: {last_error}")
    
    def simple_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """简单对话接口"""
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        response = self.chat(messages, **kwargs)
        return response.content
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """列出所有LLM实例"""
        return [
            {
                'name': name,
                'provider': llm.provider.value,
                'model': llm.model_name,
                'stats': llm.get_stats()
            }
            for name, llm in self._instances.items()
        ]
    
    def remove_instance(self, name: str):
        """移除LLM实例"""
        if name in self._instances:
            del self._instances[name]
            if name in self._fallback_order:
                self._fallback_order.remove(name)
            logger.info(f"移除LLM实例: {name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取所有实例的统计信息"""
        return {
            'total_instances': len(self._instances),
            'fallback_strategy': self.fallback_strategy.value,
            'fallback_order': self._fallback_order,
            'instances': {
                name: llm.get_stats() 
                for name, llm in self._instances.items()
            }
        }


# 全局工厂实例
_global_factory: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """获取全局LLM工厂实例"""
    global _global_factory
    if _global_factory is None:
        _global_factory = LLMFactory()
    return _global_factory


def init_llm_factory(
    configs: List[Dict[str, Any]],
    default_provider: ModelProvider = ModelProvider.ZHIPU,
    fallback_strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL
) -> LLMFactory:
    """
    初始化全局LLM工厂
    
    Args:
        configs: LLM配置列表，每个配置包含:
            - provider: 提供商名称 ('zhipu', 'gemini')
            - api_key: API密钥
            - model_name: 模型名称(可选)
            - instance_name: 实例名称(可选)
        default_provider: 默认提供商
        fallback_strategy: 降级策略
    
    Example:
        configs = [
            {'provider': 'zhipu', 'api_key': 'xxx', 'model_name': 'glm-4-flash'},
            {'provider': 'gemini', 'api_key': 'yyy', 'model_name': 'gemini-2.0-flash-exp'}
        ]
        factory = init_llm_factory(configs)
    """
    global _global_factory
    
    _global_factory = LLMFactory(
        default_provider=default_provider,
        fallback_strategy=fallback_strategy
    )
    
    for config in configs:
        provider_name = config.pop('provider')
        provider = ModelProvider(provider_name)
        _global_factory.create_llm(provider=provider, **config)
    
    return _global_factory
