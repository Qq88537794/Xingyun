"""
向量存储
使用ChromaDB作为向量数据库，支持向量的存储、检索和管理
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import uuid
import json
import os

logger = logging.getLogger(__name__)


class DistanceMetric(Enum):
    """距离度量方式"""
    COSINE = "cosine"           # 余弦相似度
    L2 = "l2"                   # 欧几里得距离
    IP = "ip"                   # 内积


@dataclass
class SearchResult:
    """搜索结果"""
    id: str                          # 文档/块ID
    content: str                     # 文本内容
    score: float                     # 相似度分数
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'score': self.score,
            'metadata': self.metadata
        }


class VectorStore:
    """
    向量存储类
    基于ChromaDB实现，支持：
    - 向量的增删改查
    - 多集合管理
    - 持久化存储
    - 元数据过滤
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "default",
        distance_metric: DistanceMetric = DistanceMetric.COSINE
    ):
        """
        初始化向量存储
        
        Args:
            persist_directory: 持久化目录，None则使用内存存储
            collection_name: 默认集合名称
            distance_metric: 距离度量方式
        """
        self.persist_directory = persist_directory
        self.distance_metric = distance_metric
        self._collections: Dict[str, Any] = {}
        self._client = None
        self._current_collection_name = collection_name
        
        # 初始化ChromaDB
        self._init_chroma()
    
    def _init_chroma(self):
        """初始化ChromaDB客户端"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            if self.persist_directory:
                # 确保目录存在
                os.makedirs(self.persist_directory, exist_ok=True)
                
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"ChromaDB持久化存储初始化: {self.persist_directory}")
            else:
                self._client = chromadb.Client(Settings(
                    anonymized_telemetry=False
                ))
                logger.info("ChromaDB内存存储初始化")
                
        except ImportError:
            logger.warning("ChromaDB未安装，使用内存模拟存储")
            self._client = None
            self._memory_store: Dict[str, Dict] = {}
    
    def _get_or_create_collection(self, name: str) -> Any:
        """获取或创建集合"""
        if name in self._collections:
            return self._collections[name]
        
        if self._client:
            # 使用ChromaDB
            distance_fn = {
                DistanceMetric.COSINE: "cosine",
                DistanceMetric.L2: "l2",
                DistanceMetric.IP: "ip"
            }.get(self.distance_metric, "cosine")
            
            collection = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": distance_fn}
            )
            self._collections[name] = collection
            return collection
        else:
            # 内存模拟
            if name not in self._memory_store:
                self._memory_store[name] = {
                    'ids': [],
                    'embeddings': [],
                    'documents': [],
                    'metadatas': []
                }
            return self._memory_store[name]
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档内容列表
            embeddings: 对应的嵌入向量
            metadatas: 元数据列表
            ids: 文档ID列表
            collection_name: 集合名称
        
        Returns:
            添加的文档ID列表
        """
        collection_name = collection_name or self._current_collection_name
        
        # 生成ID
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # 确保元数据存在
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        # 处理元数据中的复杂类型(ChromaDB只支持简单类型)
        processed_metadatas = []
        for meta in metadatas:
            processed = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    processed[k] = v
                else:
                    processed[k] = json.dumps(v, ensure_ascii=False)
            processed_metadatas.append(processed)
        
        collection = self._get_or_create_collection(collection_name)
        
        if self._client:
            # ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=processed_metadatas
            )
        else:
            # 内存模拟
            collection['ids'].extend(ids)
            collection['embeddings'].extend(embeddings)
            collection['documents'].extend(documents)
            collection['metadatas'].extend(processed_metadatas)
        
        logger.info(f"添加 {len(documents)} 个文档到集合 {collection_name}")
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        collection_name: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_embeddings: bool = False
    ) -> List[SearchResult]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            collection_name: 集合名称
            filter_metadata: 元数据过滤条件
            include_embeddings: 是否包含嵌入向量
        
        Returns:
            SearchResult列表
        """
        collection_name = collection_name or self._current_collection_name
        collection = self._get_or_create_collection(collection_name)
        
        results = []
        
        if self._client:
            # ChromaDB查询
            query_result = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 解析结果
            if query_result['ids'] and query_result['ids'][0]:
                for i, doc_id in enumerate(query_result['ids'][0]):
                    # 将距离转换为相似度分数
                    distance = query_result['distances'][0][i]
                    if self.distance_metric == DistanceMetric.COSINE:
                        score = 1 - distance  # 余弦距离转相似度
                    else:
                        score = 1 / (1 + distance)  # L2距离转相似度
                    
                    results.append(SearchResult(
                        id=doc_id,
                        content=query_result['documents'][0][i],
                        score=score,
                        metadata=query_result['metadatas'][0][i] if query_result['metadatas'] else {}
                    ))
        else:
            # 内存模拟搜索
            results = self._memory_search(
                collection, query_embedding, top_k, filter_metadata
            )
        
        return results
    
    def _memory_search(
        self,
        collection: Dict,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """内存存储的搜索实现"""
        import numpy as np
        
        if not collection['embeddings']:
            return []
        
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(collection['embeddings'])
        
        # 计算余弦相似度
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vecs, axis=1)
        
        # 避免除零
        doc_norms = np.where(doc_norms == 0, 1e-10, doc_norms)
        
        similarities = np.dot(doc_vecs, query_vec) / (doc_norms * query_norm)
        
        # 应用元数据过滤
        valid_indices = list(range(len(collection['ids'])))
        if filter_metadata:
            valid_indices = [
                i for i in valid_indices
                if all(
                    collection['metadatas'][i].get(k) == v
                    for k, v in filter_metadata.items()
                )
            ]
        
        # 获取top_k
        valid_similarities = [(i, similarities[i]) for i in valid_indices]
        valid_similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = valid_similarities[:top_k]
        
        results = []
        for idx, score in top_results:
            results.append(SearchResult(
                id=collection['ids'][idx],
                content=collection['documents'][idx],
                score=float(score),
                metadata=collection['metadatas'][idx]
            ))
        
        return results
    
    def delete_documents(
        self,
        ids: List[str],
        collection_name: Optional[str] = None
    ):
        """删除文档"""
        collection_name = collection_name or self._current_collection_name
        collection = self._get_or_create_collection(collection_name)
        
        if self._client:
            collection.delete(ids=ids)
        else:
            # 内存模拟
            for doc_id in ids:
                if doc_id in collection['ids']:
                    idx = collection['ids'].index(doc_id)
                    for key in ['ids', 'embeddings', 'documents', 'metadatas']:
                        del collection[key][idx]
        
        logger.info(f"从集合 {collection_name} 删除 {len(ids)} 个文档")
    
    def update_document(
        self,
        doc_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ):
        """更新文档"""
        collection_name = collection_name or self._current_collection_name
        collection = self._get_or_create_collection(collection_name)
        
        if self._client:
            update_kwargs = {'ids': [doc_id]}
            if document:
                update_kwargs['documents'] = [document]
            if embedding:
                update_kwargs['embeddings'] = [embedding]
            if metadata:
                update_kwargs['metadatas'] = [metadata]
            
            collection.update(**update_kwargs)
        else:
            # 内存模拟
            if doc_id in collection['ids']:
                idx = collection['ids'].index(doc_id)
                if document:
                    collection['documents'][idx] = document
                if embedding:
                    collection['embeddings'][idx] = embedding
                if metadata:
                    collection['metadatas'][idx] = metadata
    
    def get_collection_stats(
        self,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取集合统计信息"""
        collection_name = collection_name or self._current_collection_name
        collection = self._get_or_create_collection(collection_name)
        
        if self._client:
            count = collection.count()
        else:
            count = len(collection['ids'])
        
        return {
            'collection_name': collection_name,
            'document_count': count,
            'distance_metric': self.distance_metric.value
        }
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        if self._client:
            return [c.name for c in self._client.list_collections()]
        else:
            return list(self._memory_store.keys())
    
    def delete_collection(self, collection_name: str):
        """删除集合"""
        if self._client:
            self._client.delete_collection(collection_name)
        elif collection_name in self._memory_store:
            del self._memory_store[collection_name]
        
        if collection_name in self._collections:
            del self._collections[collection_name]
        
        logger.info(f"删除集合: {collection_name}")
    
    def clear_collection(self, collection_name: Optional[str] = None):
        """清空集合"""
        collection_name = collection_name or self._current_collection_name
        
        if self._client:
            # ChromaDB需要删除后重建
            self._client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
            self._get_or_create_collection(collection_name)
        else:
            if collection_name in self._memory_store:
                self._memory_store[collection_name] = {
                    'ids': [],
                    'embeddings': [],
                    'documents': [],
                    'metadatas': []
                }
        
        logger.info(f"清空集合: {collection_name}")


# 全局向量存储实例
_global_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取全局向量存储"""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStore()
    return _global_vector_store


def init_vector_store(
    persist_directory: Optional[str] = None,
    collection_name: str = "default",
    distance_metric: DistanceMetric = DistanceMetric.COSINE
) -> VectorStore:
    """初始化全局向量存储"""
    global _global_vector_store
    _global_vector_store = VectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name,
        distance_metric=distance_metric
    )
    return _global_vector_store
