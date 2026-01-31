"""
重排序器
对检索结果进行重排序，提升相关性
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from .retriever import RetrievalResult

logger = logging.getLogger(__name__)


class RerankerModel(Enum):
    """重排序模型"""
    CROSS_ENCODER = "cross_encoder"  # 交叉编码器
    LLM_RERANK = "llm_rerank"        # 使用LLM重排序
    COHERE = "cohere"                 # Cohere Rerank API
    SIMPLE = "simple"                 # 简单规则重排序


@dataclass
class RerankerConfig:
    """重排序配置"""
    model: RerankerModel = RerankerModel.SIMPLE
    top_k: int = 5
    min_score: float = 0.0
    boost_recent: bool = True
    boost_exact_match: bool = True


class Reranker:
    """
    重排序器
    支持多种重排序策略
    """
    
    def __init__(
        self,
        config: Optional[RerankerConfig] = None,
        llm_client: Optional[Any] = None
    ):
        """
        初始化重排序器
        
        Args:
            config: 重排序配置
            llm_client: LLM客户端(用于LLM重排序)
        """
        self.config = config or RerankerConfig()
        self.llm_client = llm_client
    
    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        重排序检索结果
        
        Args:
            query: 原始查询
            results: 检索结果列表
            top_k: 返回数量
        
        Returns:
            重排序后的结果
        """
        if not results:
            return results
        
        top_k = top_k or self.config.top_k
        
        # 根据配置选择重排序策略
        if self.config.model == RerankerModel.LLM_RERANK and self.llm_client:
            reranked = self._llm_rerank(query, results)
        elif self.config.model == RerankerModel.CROSS_ENCODER:
            reranked = self._cross_encoder_rerank(query, results)
        else:
            reranked = self._simple_rerank(query, results)
        
        # 过滤低分结果
        reranked = [r for r in reranked if r.score >= self.config.min_score]
        
        return reranked[:top_k]
    
    def _simple_rerank(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        简单规则重排序
        - 精确匹配加分
        - 关键词密度加分
        - 内容长度适中加分
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        for result in results:
            content_lower = result.content.lower()
            boost = 0.0
            
            # 1. 精确匹配加分
            if self.config.boost_exact_match:
                if query_lower in content_lower:
                    boost += 0.3
            
            # 2. 关键词密度
            term_matches = sum(1 for term in query_terms if term in content_lower)
            if query_terms:
                term_density = term_matches / len(query_terms)
                boost += term_density * 0.2
            
            # 3. 内容长度惩罚(太短或太长都扣分)
            content_len = len(result.content)
            if content_len < 50:
                boost -= 0.1
            elif content_len > 2000:
                boost -= 0.05
            
            # 4. 标题/开头包含关键词加分
            first_100 = content_lower[:100]
            if any(term in first_100 for term in query_terms):
                boost += 0.1
            
            # 更新分数
            result.score = min(1.0, result.score + boost)
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _cross_encoder_rerank(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        交叉编码器重排序
        使用预训练的交叉编码器模型计算query-document相关性
        """
        try:
            from sentence_transformers import CrossEncoder
            
            # 加载模型(使用缓存)
            if not hasattr(self, '_cross_encoder'):
                self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # 准备输入对
            pairs = [(query, r.content) for r in results]
            
            # 计算分数
            scores = self._cross_encoder.predict(pairs)
            
            # 更新分数
            for i, result in enumerate(results):
                result.score = float(scores[i])
            
            # 排序
            results.sort(key=lambda x: x.score, reverse=True)
            
        except ImportError:
            logger.warning("sentence-transformers未安装，使用简单重排序")
            return self._simple_rerank(query, results)
        except Exception as e:
            logger.error(f"交叉编码器重排序失败: {e}")
            return self._simple_rerank(query, results)
        
        return results
    
    def _llm_rerank(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        使用LLM进行重排序
        让LLM判断文档与查询的相关性
        """
        if not self.llm_client:
            return self._simple_rerank(query, results)
        
        try:
            # 构建重排序提示
            docs_text = "\n\n".join([
                f"文档{i+1}:\n{r.content[:500]}..."
                for i, r in enumerate(results[:10])  # 限制数量
            ])
            
            prompt = f"""请根据查询与以下文档的相关性，给每个文档打分(1-10分)。
只返回JSON格式的分数列表，如: {{"scores": [8, 5, 9, ...]}}

查询: {query}

{docs_text}

请返回分数:"""
            
            response = self.llm_client.simple_chat(prompt)
            
            # 解析响应
            import json
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                scores_data = json.loads(json_match.group())
                scores = scores_data.get('scores', [])
                
                # 更新分数
                for i, score in enumerate(scores):
                    if i < len(results):
                        results[i].score = float(score) / 10.0
                
                results.sort(key=lambda x: x.score, reverse=True)
                
        except Exception as e:
            logger.error(f"LLM重排序失败: {e}")
            return self._simple_rerank(query, results)
        
        return results
    
    def set_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
