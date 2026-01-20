"""
Qdrant向量数据库存储
替代ChromaDB，提供更好的生产环境支持
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """检索结果"""
    text: str
    score: float
    doc_id: str
    chunk_id: str
    metadata: Dict[str, Any]


class QdrantVectorStore:
    """
    Qdrant向量存储
    支持本地模式和服务器模式
    """
    
    def __init__(
        self,
        collection_name: str = "xingyun_docs",
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = False,
        path: Optional[str] = None,
        vector_size: int = 2048,
        distance: str = "Cosine"
    ):
        """
        初始化Qdrant存储
        
        Args:
            collection_name: 集合名称
            host: Qdrant服务器地址
            port: Qdrant服务器端口
            use_memory: 是否使用内存模式（开发环境）
            path: 本地持久化路径（使用本地模式时）
            vector_size: 向量维度
            distance: 距离度量方式 (Cosine, Euclid, Dot)
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self._client = None
        self._use_memory = use_memory
        self._host = host
        self._port = port
        self._path = path
        
        self._init_client()
    
    def _init_client(self):
        """初始化Qdrant客户端"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            if self._use_memory:
                # 内存模式（开发/测试）
                self._client = QdrantClient(":memory:")
                logger.info("Qdrant使用内存模式")
            elif self._path:
                # 本地持久化模式
                self._client = QdrantClient(path=self._path)
                logger.info(f"Qdrant使用本地存储: {self._path}")
            else:
                # 服务器模式
                self._client = QdrantClient(host=self._host, port=self._port)
                logger.info(f"Qdrant连接服务器: {self._host}:{self._port}")
            
            # 确保集合存在
            self._ensure_collection()
            
        except ImportError:
            logger.warning("qdrant-client未安装，使用模拟模式")
            self._client = None
        except Exception as e:
            logger.error(f"Qdrant初始化失败: {e}")
            self._client = None
    
    def _ensure_collection(self):
        """确保集合存在"""
        if not self._client:
            return
        
        try:
            from qdrant_client.models import Distance, VectorParams
            
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                distance_map = {
                    "Cosine": Distance.COSINE,
                    "Euclid": Distance.EUCLID,
                    "Dot": Distance.DOT
                }
                
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=distance_map.get(self.distance, Distance.COSINE)
                    )
                )
                logger.info(f"创建Qdrant集合: {self.collection_name}")
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        doc_ids: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            texts: 文本列表
            embeddings: 向量列表
            doc_ids: 文档ID列表
            metadatas: 元数据列表
        
        Returns:
            chunk_id列表
        """
        if not self._client:
            logger.warning("Qdrant客户端未初始化")
            return []
        
        try:
            from qdrant_client.models import PointStruct
            
            metadatas = metadatas or [{} for _ in texts]
            chunk_ids = []
            points = []
            
            for i, (text, embedding, doc_id, metadata) in enumerate(
                zip(texts, embeddings, doc_ids, metadatas)
            ):
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)
                
                # 构建payload
                payload = {
                    "text": text,
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    **metadata
                }
                
                points.append(PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload=payload
                ))
            
            # 批量插入
            self._client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.debug(f"添加 {len(texts)} 个文档块到Qdrant")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return []
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件
            score_threshold: 最低分数阈值
        
        Returns:
            搜索结果列表
        """
        if not self._client:
            logger.warning("Qdrant客户端未初始化")
            return []
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # 构建过滤条件
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # 执行搜索 (qdrant-client >= 1.16 使用 query_points)
            results = self._client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                score_threshold=score_threshold
            ).points
            
            search_results = []
            for result in results:
                payload = result.payload or {}
                search_results.append(SearchResult(
                    text=payload.get("text", ""),
                    score=result.score,
                    doc_id=payload.get("doc_id", ""),
                    chunk_id=payload.get("chunk_id", str(result.id)),
                    metadata={k: v for k, v in payload.items() if k not in ["text", "doc_id", "chunk_id"]}
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def delete_by_doc_id(self, doc_id: str) -> bool:
        """
        删除指定文档的所有块
        
        Args:
            doc_id: 文档ID
        
        Returns:
            是否成功
        """
        if not self._client:
            return False
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )
                    ]
                )
            )
            
            logger.info(f"删除文档: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def delete_collection(self) -> bool:
        """删除整个集合"""
        if not self._client:
            return False
        
        try:
            self._client.delete_collection(self.collection_name)
            logger.info(f"删除集合: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        if not self._client:
            return {"error": "客户端未初始化"}
        
        try:
            info = self._client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value if info.status else "unknown"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_documents(self, limit: int = 100) -> List[str]:
        """
        列出所有文档ID
        
        Args:
            limit: 最大返回数量
        
        Returns:
            文档ID列表
        """
        if not self._client:
            return []
        
        try:
            # 滚动获取所有点
            results, _ = self._client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=["doc_id"]
            )
            
            doc_ids = set()
            for point in results:
                if point.payload and "doc_id" in point.payload:
                    doc_ids.add(point.payload["doc_id"])
            
            return list(doc_ids)
            
        except Exception as e:
            logger.error(f"列出文档失败: {e}")
            return []


# 项目级知识库管理
class ProjectKnowledgeBase:
    """
    项目知识库
    每个项目有独立的知识库（集合）
    """
    
    def __init__(
        self,
        project_id: int,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        use_memory: bool = False,
        qdrant_path: Optional[str] = None,
        vector_size: int = 2048
    ):
        """
        初始化项目知识库
        
        Args:
            project_id: 项目ID
            qdrant_host: Qdrant服务器地址
            qdrant_port: Qdrant服务器端口
            use_memory: 是否使用内存模式
            qdrant_path: 本地存储路径
            vector_size: 向量维度
        """
        self.project_id = project_id
        self.collection_name = f"project_{project_id}_kb"
        
        self.vector_store = QdrantVectorStore(
            collection_name=self.collection_name,
            host=qdrant_host,
            port=qdrant_port,
            use_memory=use_memory,
            path=qdrant_path,
            vector_size=vector_size
        )
    
    def add_resource(
        self,
        resource_id: int,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """
        添加资源到知识库
        
        Args:
            resource_id: 资源ID
            texts: 文本块列表
            embeddings: 向量列表
            metadata: 资源元数据
        
        Returns:
            chunk_id列表
        """
        doc_id = f"resource_{resource_id}"
        metadatas = [
            {
                "resource_id": resource_id,
                "project_id": self.project_id,
                **(metadata or {})
            }
            for _ in texts
        ]
        
        return self.vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            doc_ids=[doc_id] * len(texts),
            metadatas=metadatas
        )
    
    def remove_resource(self, resource_id: int) -> bool:
        """从知识库移除资源"""
        doc_id = f"resource_{resource_id}"
        return self.vector_store.delete_by_doc_id(doc_id)
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SearchResult]:
        """在知识库中搜索"""
        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
    
    def get_info(self) -> Dict[str, Any]:
        """获取知识库信息"""
        info = self.vector_store.get_collection_info()
        info["project_id"] = self.project_id
        return info
    
    def list_resources(self) -> List[int]:
        """列出知识库中的所有资源ID"""
        doc_ids = self.vector_store.list_documents()
        resource_ids = []
        for doc_id in doc_ids:
            if doc_id.startswith("resource_"):
                try:
                    resource_ids.append(int(doc_id.replace("resource_", "")))
                except ValueError:
                    pass
        return resource_ids
