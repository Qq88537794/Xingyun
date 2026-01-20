"""
嵌入向量服务
支持多种嵌入模型，生成文本的向量表示
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入本地模型库
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers未安装，本地模型不可用")


class EmbeddingModel(Enum):
    """嵌入模型枚举"""
    # 智谱清言嵌入模型
    ZHIPU_EMBEDDING_3 = "embedding-3"
    ZHIPU_EMBEDDING_2 = "embedding-2"
    
    # Google 嵌入模型
    GEMINI_EMBEDDING = "text-embedding-004"
    
    # OpenAI 嵌入模型 (预留)
    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    
    # 本地模型 (预留)
    LOCAL_BGE_SMALL = "bge-small-zh-v1.5"
    LOCAL_BGE_BASE = "bge-base-zh-v1.5"
    LOCAL_BGE_LARGE = "bge-large-zh-v1.5"
    LOCAL_M3E_BASE = "m3e-base"


@dataclass
class EmbeddingResult:
    """嵌入结果"""
    embeddings: List[List[float]]  # 嵌入向量列表
    model: str                      # 使用的模型
    dimensions: int                 # 向量维度
    token_count: int = 0           # 消耗的token数
    
    def to_numpy(self) -> np.ndarray:
        """转换为numpy数组"""
        return np.array(self.embeddings)


class BaseEmbedding(ABC):
    """嵌入模型基类"""
    
    def __init__(
        self,
        api_key: str,
        model_name: str,
        api_base: Optional[str] = None,
        dimensions: Optional[int] = None,
        **kwargs
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.api_base = api_base
        self.dimensions = dimensions
        self.extra_config = kwargs
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """批量嵌入文本"""
        pass
    
    def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        result = self.embed_texts([text])
        return result.embeddings[0]
    
    def embed_query(self, query: str) -> List[float]:
        """嵌入查询文本(某些模型对query和document有不同处理)"""
        return self.embed_text(query)


class ZhipuEmbedding(BaseEmbedding):
    """智谱清言嵌入模型"""
    
    DEFAULT_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_MODEL = "embedding-3"
    
    # 模型信息
    MODEL_INFO = {
        'embedding-3': {'dimensions': 2048, 'max_tokens': 8192},
        'embedding-2': {'dimensions': 1024, 'max_tokens': 512},
    }
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        api_base: str = DEFAULT_API_BASE,
        **kwargs
    ):
        info = self.MODEL_INFO.get(model_name, {'dimensions': 2048})
        super().__init__(
            api_key=api_key,
            model_name=model_name,
            api_base=api_base or self.DEFAULT_API_BASE,
            dimensions=info.get('dimensions'),
            **kwargs
        )
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """批量嵌入文本"""
        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        all_embeddings = []
        total_tokens = 0
        
        # 智谱API支持批量请求，但有大小限制，分批处理
        batch_size = 25
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            payload = {
                "model": self.model_name,
                "input": batch
            }
            
            try:
                import httpx
                with httpx.Client(timeout=60) as client:
                    response = client.post(url, headers=headers, json=payload)
            except ImportError:
                import requests
                response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                raise Exception(f"智谱Embedding API错误: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # 提取嵌入向量
            for item in data.get('data', []):
                all_embeddings.append(item['embedding'])
            
            # 提取token使用
            usage = data.get('usage', {})
            total_tokens += usage.get('total_tokens', 0)
        
class GeminiEmbedding(BaseEmbedding):
    """Google Gemini嵌入模型"""
    
    DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "text-embedding-004"
    
    MODEL_INFO = {
        'text-embedding-004': {'dimensions': 768, 'max_tokens': 2048},
        'embedding-001': {'dimensions': 768, 'max_tokens': 2048},
    }
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        api_base: str = DEFAULT_API_BASE,
        **kwargs
    ):
        info = self.MODEL_INFO.get(model_name, {'dimensions': 768})
        super().__init__(
            api_key=api_key,
            model_name=model_name,
            api_base=api_base or self.DEFAULT_API_BASE,
            dimensions=info.get('dimensions'),
            **kwargs
        )
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """批量嵌入文本"""
        all_embeddings = []
        
        # Gemini需要逐个请求或使用batchEmbedContents
        for text in texts:
            url = f"{self.api_base}/models/{self.model_name}:embedContent?key={self.api_key}"
            
            payload = {
                "model": f"models/{self.model_name}",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            
            try:
                import httpx
                with httpx.Client(timeout=60) as client:
                    response = client.post(url, json=payload)
            except ImportError:
                import requests
                response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code != 200:
                raise Exception(f"Gemini Embedding API错误: {response.status_code} - {response.text}")
            
            data = response.json()
            embedding = data.get('embedding', {}).get('values', [])
            all_embeddings.append(embedding)
        
        return EmbeddingResult(
            embeddings=all_embeddings,
            model=self.model_name,
            dimensions=self.dimensions or len(all_embeddings[0]) if all_embeddings else 0,
            token_count=0  # Gemini不返回token计数
        )


class LocalEmbedding(BaseEmbedding):
    """本地嵌入模型（使用sentence-transformers）"""
    
    # 支持的本地模型及其信息
    MODEL_INFO = {
        'BAAI/bge-small-zh-v1.5': {'dimensions': 512, 'max_tokens': 512},
        'BAAI/bge-base-zh-v1.5': {'dimensions': 768, 'max_tokens': 512},
        'BAAI/bge-large-zh-v1.5': {'dimensions': 1024, 'max_tokens': 512},
        'moka-ai/m3e-base': {'dimensions': 768, 'max_tokens': 512},
        'moka-ai/m3e-small': {'dimensions': 512, 'max_tokens': 512},
    }
    
    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        cache_folder: Optional[str] = None,
        **kwargs
    ):
        """
        初始化本地嵌入模型
        
        Args:
            model_name: 模型名称或路径
            device: 设备 ('cpu', 'cuda', 'mps')，None为自动选择
            cache_folder: 模型缓存目录
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "使用本地嵌入模型需要安装sentence-transformers: "
                "pip install sentence-transformers"
            )
        
        info = self.MODEL_INFO.get(model_name, {'dimensions': 768})
        super().__init__(
            api_key="",  # 本地模型不需要API密钥
            model_name=model_name,
            dimensions=info.get('dimensions'),
            **kwargs
        )
        
        self.device = device
        self.cache_folder = cache_folder
        self._model = None
        
        # 延迟加载模型
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        if self._model is None:
            try:
                logger.info(f"正在加载本地嵌入模型: {self.model_name}")
                
                load_kwargs = {}
                if self.device:
                    load_kwargs['device'] = self.device
                if self.cache_folder:
                    load_kwargs['cache_folder'] = self.cache_folder
                
                self._model = SentenceTransformer(self.model_name, **load_kwargs)
                
                # 获取实际维度
                if self.dimensions is None:
                    self.dimensions = self._model.get_sentence_embedding_dimension()
                
                logger.info(
                    f"本地模型加载成功: {self.model_name}, "
                    f"维度: {self.dimensions}, "
                    f"设备: {self._model.device}"
                )
            except Exception as e:
                logger.error(f"加载本地模型失败: {e}")
                raise
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """批量嵌入文本"""
        if self._model is None:
            self._load_model()
        
        # 使用sentence-transformers进行编码
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # 归一化向量
        )
        
        return EmbeddingResult(
            embeddings=embeddings.tolist(),
            model=self.model_name,
            dimensions=self.dimensions,
            token_count=0  # 本地模型不计算token
        )
    
    def embed_query(self, query: str) -> List[float]:
        """
        嵌入查询文本
        BGE模型建议为查询添加指令前缀以提高检索效果
        """
        # BGE模型推荐的查询指令
        if self.model_name.startswith('BAAI/bge'):
            query = f"为这个句子生成表示以用于检索相关文章：{query}"
        
        return self.embed_text(query)


class EmbeddingService:
    """
    嵌入服务统一接口
    管理多种嵌入模型，提供统一的调用方式
    """
    
    _providers = {
        'zhipu': ZhipuEmbedding,
        'gemini': GeminiEmbedding,
        'local': LocalEmbedding,
    }
    
    def __init__(
        self,
        provider: str = "local",
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ):
        """
        初始化嵌入服务
        
        Args:
            provider: 嵌入模型提供商 ('local', 'zhipu', 'gemini')
            api_key: API密钥（本地模型不需要）
            model_name: 模型名称
        """
        self.provider = provider
        
        if provider not in self._providers:
            raise ValueError(f"不支持的嵌入模型提供商: {provider}")
        
        self._embedding_class = self._providers[provider]
        self._embedding_model = None
        
        # 本地模型不需要API密钥
        if provider == 'local':
            if model_name is None:
                model_name = LocalEmbedding.DEFAULT_MODEL
            self._init_model(None, model_name, **kwargs)
        elif api_key:
            self._init_model(api_key, model_name, **kwargs)
    
    def _init_model(
        self,
        api_key: Optional[str],
        model_name: Optional[str] = None,
        **kwargs
    ):
        """初始化嵌入模型"""
        init_kwargs = {**kwargs}
        
        # 本地模型不需要API密钥
        if self.provider != 'local' and api_key:
            init_kwargs['api_key'] = api_key
        
        if model_name:
            init_kwargs['model_name'] = model_name
        
        self._embedding_model = self._embedding_class(**init_kwargs)
        logger.info(f"初始化嵌入模型: {self.provider}/{self._embedding_model.model_name}")
    
    def configure(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ):
        """配置嵌入模型"""
        self._init_model(api_key, model_name, **kwargs)
    
    def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        批量嵌入文本
        
        Args:
            texts: 文本列表
        
        Returns:
            EmbeddingResult
        """
        if not self._embedding_model:
            raise RuntimeError("嵌入模型未初始化，请先调用configure()")
        
        return self._embedding_model.embed_texts(texts)
    
    def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        if not self._embedding_model:
            raise RuntimeError("嵌入模型未初始化")
        
        return self._embedding_model.embed_text(text)
    
    def embed_query(self, query: str) -> List[float]:
        """嵌入查询文本"""
        if not self._embedding_model:
            raise RuntimeError("嵌入模型未初始化")
        
        return self._embedding_model.embed_query(query)
    
    def get_dimensions(self) -> int:
        """获取向量维度"""
        if not self._embedding_model:
            raise RuntimeError("嵌入模型未初始化")
        return self._embedding_model.dimensions
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self._embedding_model:
            return {'provider': self.provider, 'status': 'not_initialized'}
        
        return {
            'provider': self.provider,
            'model': self._embedding_model.model_name,
            'dimensions': self._embedding_model.dimensions
        }


# 全局嵌入服务实例
_global_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取全局嵌入服务，如果未初始化则自动初始化为本地模型"""
    global _global_embedding_service
    if _global_embedding_service is None:
        # 自动初始化为本地模型
        _global_embedding_service = EmbeddingService(
            provider="local",
            model_name="BAAI/bge-small-zh-v1.5"
        )
    return _global_embedding_service


def init_embedding_service(
    provider: str = "local",
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs
) -> EmbeddingService:
    """
    初始化全局嵌入服务
    
    Args:
        provider: 提供商 ('local', 'zhipu', 'gemini')
        api_key: API密钥（本地模型不需要）
        model_name: 模型名称，默认 'BAAI/bge-small-zh-v1.5'
        **kwargs: 其他参数（如device, cache_folder等）
    """
    global _global_embedding_service
    _global_embedding_service = EmbeddingService(
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        **kwargs
    )
    return _global_embedding_service
