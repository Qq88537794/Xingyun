"""
混合检索器
实现向量检索+关键词检索的混合检索策略
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter
import math

from .vector_store import VectorStore, SearchResult
from .embedding import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    id: str
    content: str
    score: float                      # 综合分数
    vector_score: float = 0.0         # 向量相似度分数
    keyword_score: float = 0.0        # 关键词匹配分数
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)  # 高亮片段
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'score': self.score,
            'vector_score': self.vector_score,
            'keyword_score': self.keyword_score,
            'metadata': self.metadata,
            'highlights': self.highlights
        }


class KeywordSearcher:
    """
    关键词搜索器
    基于BM25算法实现关键词检索
    """
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25
    ):
        """
        初始化BM25搜索器
        
        Args:
            k1: 词频饱和参数
            b: 文档长度归一化参数
            epsilon: IDF平滑参数
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        
        # 索引数据
        self._documents: Dict[str, str] = {}  # id -> content
        self._doc_lengths: Dict[str, int] = {}
        self._avg_doc_length: float = 0
        self._term_freqs: Dict[str, Dict[str, int]] = {}  # doc_id -> {term: freq}
        self._doc_freqs: Dict[str, int] = {}  # term -> doc_count
        self._idf: Dict[str, float] = {}
    
    def add_documents(
        self,
        documents: List[str],
        ids: List[str]
    ):
        """添加文档到索引"""
        for doc_id, content in zip(ids, documents):
            self._documents[doc_id] = content
            tokens = self._tokenize(content)
            self._doc_lengths[doc_id] = len(tokens)
            
            # 计算词频
            term_freq = Counter(tokens)
            self._term_freqs[doc_id] = dict(term_freq)
            
            # 更新文档频率
            for term in set(tokens):
                self._doc_freqs[term] = self._doc_freqs.get(term, 0) + 1
        
        # 更新平均文档长度
        if self._doc_lengths:
            self._avg_doc_length = sum(self._doc_lengths.values()) / len(self._doc_lengths)
        
        # 重新计算IDF
        self._calculate_idf()
    
    def remove_documents(self, ids: List[str]):
        """从索引中移除文档"""
        for doc_id in ids:
            if doc_id in self._documents:
                # 更新文档频率
                for term in self._term_freqs.get(doc_id, {}).keys():
                    if term in self._doc_freqs:
                        self._doc_freqs[term] -= 1
                        if self._doc_freqs[term] <= 0:
                            del self._doc_freqs[term]
                
                del self._documents[doc_id]
                del self._doc_lengths[doc_id]
                del self._term_freqs[doc_id]
        
        # 重新计算
        if self._doc_lengths:
            self._avg_doc_length = sum(self._doc_lengths.values()) / len(self._doc_lengths)
        self._calculate_idf()
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 简单分词: 中文按字符，英文按空格和标点
        text = text.lower()
        
        # 提取中文字符
        chinese_pattern = r'[\u4e00-\u9fff]+'
        chinese_matches = re.findall(chinese_pattern, text)
        chinese_tokens = list(''.join(chinese_matches))
        
        # 提取英文单词
        english_pattern = r'[a-zA-Z]+'
        english_tokens = re.findall(english_pattern, text)
        
        # 提取数字
        number_pattern = r'\d+'
        number_tokens = re.findall(number_pattern, text)
        
        return chinese_tokens + english_tokens + number_tokens
    
    def _calculate_idf(self):
        """计算IDF值"""
        n_docs = len(self._documents)
        if n_docs == 0:
            return
        
        for term, doc_freq in self._doc_freqs.items():
            # BM25 IDF公式
            idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
            self._idf[term] = max(idf, self.epsilon)
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_ids: Optional[Set[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        BM25搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filter_ids: 限制搜索范围的文档ID集合
        
        Returns:
            (doc_id, score) 列表
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scores = {}
        
        doc_ids = filter_ids if filter_ids else set(self._documents.keys())
        
        for doc_id in doc_ids:
            if doc_id not in self._documents:
                continue
            
            score = 0.0
            doc_len = self._doc_lengths[doc_id]
            term_freqs = self._term_freqs.get(doc_id, {})
            
            for term in query_tokens:
                if term not in self._idf:
                    continue
                
                tf = term_freqs.get(term, 0)
                if tf == 0:
                    continue
                
                idf = self._idf[term]
                
                # BM25 公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_length)
                score += idf * numerator / denominator
            
            if score > 0:
                scores[doc_id] = score
        
        # 排序
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def get_highlights(
        self,
        content: str,
        query: str,
        max_highlights: int = 3,
        context_chars: int = 50
    ) -> List[str]:
        """获取高亮片段"""
        query_tokens = set(self._tokenize(query))
        highlights = []
        
        # 查找匹配位置
        for token in query_tokens:
            # 在内容中查找
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            for match in pattern.finditer(content):
                start = max(0, match.start() - context_chars)
                end = min(len(content), match.end() + context_chars)
                snippet = content[start:end]
                
                # 添加省略号
                if start > 0:
                    snippet = '...' + snippet
                if end < len(content):
                    snippet = snippet + '...'
                
                highlights.append(snippet)
                
                if len(highlights) >= max_highlights:
                    break
            
            if len(highlights) >= max_highlights:
                break
        
        return highlights


class HybridRetriever:
    """
    混合检索器
    结合向量检索和关键词检索，提供更好的检索效果
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        """
        初始化混合检索器
        
        Args:
            vector_store: 向量存储
            embedding_service: 嵌入服务
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        
        # 关键词搜索器
        self._keyword_searcher = KeywordSearcher()
        
        # 文档缓存
        self._doc_cache: Dict[str, Dict[str, Any]] = {}
    
    def index_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        索引文档(同时建立向量索引和关键词索引)
        
        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
            collection_name: 集合名称
        
        Returns:
            文档ID列表
        """
        # 生成嵌入向量
        embedding_result = self.embedding_service.embed_texts(documents)
        
        # 添加到向量存储
        doc_ids = self.vector_store.add_documents(
            documents=documents,
            embeddings=embedding_result.embeddings,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name
        )
        
        # 添加到关键词索引
        self._keyword_searcher.add_documents(documents, doc_ids)
        
        # 缓存文档
        for i, doc_id in enumerate(doc_ids):
            self._doc_cache[doc_id] = {
                'content': documents[i],
                'metadata': metadatas[i] if metadatas else {}
            }
        
        return doc_ids
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        collection_name: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
        rerank: bool = False
    ) -> List[RetrievalResult]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            collection_name: 集合名称
            filter_metadata: 元数据过滤
            use_hybrid: 是否使用混合检索(False则只用向量检索)
            rerank: 是否进行重排序
        
        Returns:
            RetrievalResult列表
        """
        # 1. 向量检索
        query_embedding = self.embedding_service.embed_query(query)
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2 if use_hybrid else top_k,  # 获取更多结果用于融合
            collection_name=collection_name,
            filter_metadata=filter_metadata
        )
        
        # 转换为字典便于合并
        result_dict: Dict[str, RetrievalResult] = {}
        
        # 归一化向量分数
        max_vector_score = max((r.score for r in vector_results), default=1.0)
        
        for result in vector_results:
            normalized_score = result.score / max_vector_score if max_vector_score > 0 else 0
            result_dict[result.id] = RetrievalResult(
                id=result.id,
                content=result.content,
                score=normalized_score * self.vector_weight,
                vector_score=normalized_score,
                keyword_score=0.0,
                metadata=result.metadata
            )
        
        # 2. 关键词检索(如果启用混合检索)
        if use_hybrid:
            # 限制搜索范围到向量检索的结果集，或全量搜索
            filter_ids = set(result_dict.keys()) if filter_metadata else None
            keyword_results = self._keyword_searcher.search(
                query=query,
                top_k=top_k * 2,
                filter_ids=filter_ids
            )
            
            # 归一化关键词分数
            max_keyword_score = max((score for _, score in keyword_results), default=1.0)
            
            for doc_id, score in keyword_results:
                normalized_score = score / max_keyword_score if max_keyword_score > 0 else 0
                
                if doc_id in result_dict:
                    # 合并分数
                    result_dict[doc_id].keyword_score = normalized_score
                    result_dict[doc_id].score += normalized_score * self.keyword_weight
                else:
                    # 新增结果
                    doc_info = self._doc_cache.get(doc_id, {})
                    result_dict[doc_id] = RetrievalResult(
                        id=doc_id,
                        content=doc_info.get('content', ''),
                        score=normalized_score * self.keyword_weight,
                        vector_score=0.0,
                        keyword_score=normalized_score,
                        metadata=doc_info.get('metadata', {})
                    )
        
        # 3. 按综合分数排序
        sorted_results = sorted(
            result_dict.values(),
            key=lambda x: x.score,
            reverse=True
        )[:top_k]
        
        # 4. 添加高亮
        for result in sorted_results:
            result.highlights = self._keyword_searcher.get_highlights(
                result.content, query
            )
        
        return sorted_results
    
    def remove_documents(
        self,
        ids: List[str],
        collection_name: Optional[str] = None
    ):
        """移除文档"""
        self.vector_store.delete_documents(ids, collection_name)
        self._keyword_searcher.remove_documents(ids)
        
        for doc_id in ids:
            if doc_id in self._doc_cache:
                del self._doc_cache[doc_id]
    
    def set_weights(self, vector_weight: float, keyword_weight: float):
        """设置检索权重"""
        total = vector_weight + keyword_weight
        self.vector_weight = vector_weight / total
        self.keyword_weight = keyword_weight / total
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计"""
        return {
            'vector_weight': self.vector_weight,
            'keyword_weight': self.keyword_weight,
            'indexed_documents': len(self._doc_cache),
            'vector_store_stats': self.vector_store.get_collection_stats()
        }
