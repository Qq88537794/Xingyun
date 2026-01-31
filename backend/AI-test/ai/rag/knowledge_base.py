"""
知识库服务
集成资源模块，提供知识库的索引和检索功能
"""

import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .qdrant_store import ProjectKnowledgeBase, SearchResult
from .chunker import TextChunker, ChunkingStrategy
from .embedding import EmbeddingService, init_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeBaseConfig:
    """知识库配置"""
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_use_memory: bool = True  # 开发环境默认使用内存
    qdrant_path: Optional[str] = None
    
    embedding_provider: str = "local"  # 'local', 'zhipu' 或 'gemini'
    embedding_api_key: Optional[str] = None
    embedding_model: str = "BAAI/bge-small-zh-v1.5"  # 本地模型名称
    embedding_device: Optional[str] = None  # 'cpu', 'cuda', 'mps'
    embedding_cache_folder: Optional[str] = None  # 模型缓存目录
    
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunking_strategy: str = "recursive"


class KnowledgeBaseService:
    """
    知识库服务
    管理项目知识库的索引和检索
    """
    
    def __init__(self, config: KnowledgeBaseConfig = None):
        """
        初始化知识库服务
        
        Args:
            config: 配置对象
        """
        self.config = config or KnowledgeBaseConfig()
        
        # 项目知识库缓存
        self._project_kbs: Dict[int, ProjectKnowledgeBase] = {}
        
        # 初始化分块器
        strategy_map = {
            "fixed": ChunkingStrategy.FIXED_SIZE,
            "sentence": ChunkingStrategy.SENTENCE,
            "paragraph": ChunkingStrategy.PARAGRAPH,
            "recursive": ChunkingStrategy.RECURSIVE,
            "markdown": ChunkingStrategy.MARKDOWN,
        }
        self.chunker = TextChunker(
            strategy=strategy_map.get(self.config.chunking_strategy, ChunkingStrategy.RECURSIVE),
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        
        # 初始化嵌入服务
        self.embedding_service = self._init_embedding_service()
    
    def _init_embedding_service(self) -> Optional[EmbeddingService]:
        """初始化嵌入服务"""
        try:
            provider = self.config.embedding_provider
            
            # 本地模型不需要API密钥
            if provider == 'local':
                return init_embedding_service(
                    provider='local',
                    model_name=getattr(self.config, 'embedding_model', 'BAAI/bge-small-zh-v1.5'),
                    device=getattr(self.config, 'embedding_device', None),
                    cache_folder=getattr(self.config, 'embedding_cache_folder', None)
                )
            
            # 云端模型需要API密钥
            if not self.config.embedding_api_key:
                logger.warning(f"未配置{provider}的Embedding API Key")
                return None
            
            return init_embedding_service(
                provider=provider,
                api_key=self.config.embedding_api_key
            )
        except Exception as e:
            logger.error(f"初始化Embedding服务失败: {e}")
            return None
    
    def get_project_kb(self, project_id: int) -> ProjectKnowledgeBase:
        """
        获取项目知识库
        
        Args:
            project_id: 项目ID
        
        Returns:
            项目知识库实例
        """
        if project_id not in self._project_kbs:
            # 根据嵌入模型获取向量维度
            provider = self.config.embedding_provider
            if provider == 'local':
                # BGE-small: 512, BGE-base: 768, BGE-large: 1024
                model_name = getattr(self.config, 'embedding_model', 'BAAI/bge-small-zh-v1.5')
                if 'small' in model_name:
                    vector_size = 512
                elif 'large' in model_name:
                    vector_size = 1024
                else:
                    vector_size = 768
            elif provider == 'zhipu':
                vector_size = 2048
            else:  # gemini
                vector_size = 768
            
            self._project_kbs[project_id] = ProjectKnowledgeBase(
                project_id=project_id,
                qdrant_host=self.config.qdrant_host,
                qdrant_port=self.config.qdrant_port,
                use_memory=self.config.qdrant_use_memory,
                qdrant_path=self.config.qdrant_path,
                vector_size=vector_size
            )
        
        return self._project_kbs[project_id]
    
    def index_resource(
        self,
        project_id: int,
        resource_id: int,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        索引资源文件到知识库
        
        Args:
            project_id: 项目ID
            resource_id: 资源ID
            file_path: 文件路径
            metadata: 元数据
        
        Returns:
            索引结果信息
        """
        if not self.embedding_service:
            return {"success": False, "error": "Embedding服务未配置"}
        
        try:
            # 1. 读取文件内容
            text = self._read_file(file_path)
            if not text:
                return {"success": False, "error": "无法读取文件内容"}
            
            # 2. 分块
            chunks = self.chunker.chunk_text(text)
            if not chunks:
                return {"success": False, "error": "文件内容为空"}
            
            chunk_texts = [c.content for c in chunks]
            
            # 3. 生成向量
            embedding_result = self.embedding_service.embed_texts(chunk_texts)
            embeddings = embedding_result.embeddings
            
            # 4. 存入知识库
            kb = self.get_project_kb(project_id)
            
            # 先删除旧数据（如果存在）
            kb.remove_resource(resource_id)
            
            # 添加新数据
            chunk_ids = kb.add_resource(
                resource_id=resource_id,
                texts=chunk_texts,
                embeddings=embeddings,
                metadata=metadata
            )
            
            return {
                "success": True,
                "resource_id": resource_id,
                "chunk_count": len(chunk_ids),
                "total_chars": len(text)
            }
            
        except Exception as e:
            logger.error(f"索引资源失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def remove_resource(self, project_id: int, resource_id: int) -> bool:
        """
        从知识库移除资源
        
        Args:
            project_id: 项目ID
            resource_id: 资源ID
        
        Returns:
            是否成功
        """
        try:
            kb = self.get_project_kb(project_id)
            return kb.remove_resource(resource_id)
        except Exception as e:
            logger.error(f"移除资源失败: {e}")
            return False
    
    def search(
        self,
        project_id: int,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        在项目知识库中检索
        
        Args:
            project_id: 项目ID
            query: 查询文本
            top_k: 返回结果数量
        
        Returns:
            检索结果列表
        """
        if not self.embedding_service:
            logger.warning("Embedding服务未配置，无法检索")
            return []
        
        try:
            # 生成查询向量
            query_embedding = self.embedding_service.embed_query(query)
            
            # 检索
            kb = self.get_project_kb(project_id)
            return kb.search(query_embedding, top_k=top_k)
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    def build_context(
        self,
        results: List[SearchResult],
        max_length: int = 3000
    ) -> str:
        """
        构建RAG上下文
        
        Args:
            results: 检索结果
            max_length: 最大长度
        
        Returns:
            构建的上下文文本
        """
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results):
            part = f"[来源 {i+1}] (相关度: {result.score:.2f})\n{result.text}\n"
            
            if current_length + len(part) > max_length:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "\n".join(context_parts)
    
    def has_knowledge_base(self, project_id: int) -> bool:
        """
        检查项目是否有知识库内容
        
        Args:
            project_id: 项目ID
        
        Returns:
            是否有内容
        """
        try:
            kb = self.get_project_kb(project_id)
            resources = kb.list_resources()
            return len(resources) > 0
        except Exception:
            return False
    
    def get_kb_info(self, project_id: int) -> Dict[str, Any]:
        """获取知识库信息"""
        try:
            kb = self.get_project_kb(project_id)
            info = kb.get_info()
            info["indexed_resources"] = kb.list_resources()
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def _read_file(self, file_path: str) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件文本内容
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.txt' or ext == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif ext == '.pdf':
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    texts = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            texts.append(text)
                    return '\n\n'.join(texts)
                except ImportError:
                    logger.warning("PyPDF2未安装，无法解析PDF")
                    return ""
            
            elif ext == '.docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    texts = [para.text for para in doc.paragraphs if para.text.strip()]
                    return '\n\n'.join(texts)
                except ImportError:
                    logger.warning("python-docx未安装，无法解析DOCX")
                    return ""
            
            else:
                # 尝试作为文本读取
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except UnicodeDecodeError:
                    logger.warning(f"无法解析文件: {file_path}")
                    return ""
        
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return ""


# 全局知识库服务
_global_kb_service: Optional[KnowledgeBaseService] = None


def get_kb_service() -> KnowledgeBaseService:
    """获取全局知识库服务"""
    global _global_kb_service
    if _global_kb_service is None:
        from config import Config
        
        config = KnowledgeBaseConfig(
            qdrant_host=getattr(Config, 'QDRANT_HOST', 'localhost'),
            qdrant_port=getattr(Config, 'QDRANT_PORT', 6333),
            qdrant_use_memory=getattr(Config, 'QDRANT_USE_MEMORY', True),
            qdrant_path=getattr(Config, 'QDRANT_PATH', None),
            embedding_provider=getattr(Config, 'EMBEDDING_PROVIDER', 'local'),
            embedding_api_key=getattr(Config, 'ZHIPU_API_KEY', None) or getattr(Config, 'GEMINI_API_KEY', None),
            embedding_model=getattr(Config, 'EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5'),
            embedding_device=getattr(Config, 'EMBEDDING_DEVICE', None),
            embedding_cache_folder=getattr(Config, 'EMBEDDING_CACHE_FOLDER', None),
            chunk_size=getattr(Config, 'RAG_CHUNK_SIZE', 500),
            chunk_overlap=getattr(Config, 'RAG_CHUNK_OVERLAP', 50),
        )
        
        _global_kb_service = KnowledgeBaseService(config)
    
    return _global_kb_service


def init_kb_service(config: KnowledgeBaseConfig) -> KnowledgeBaseService:
    """初始化全局知识库服务"""
    global _global_kb_service
    _global_kb_service = KnowledgeBaseService(config)
    return _global_kb_service
