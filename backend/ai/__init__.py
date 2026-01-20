"""
AI模块初始化
导出所有AI组件
"""

# LLM 模块
from .llm import (
    BaseLLM,
    LLMResponse,
    TokenUsage,
    Message,
    ModelProvider,
    ZhipuLLM,
    GeminiLLM,
    LLMFactory,
    get_llm_factory,
    init_llm_factory,
)

# RAG 模块
from .rag import (
    TextChunker,
    TextChunk,
    ChunkingStrategy,
    EmbeddingService,
    LocalEmbedding,
    init_embedding_service,
    QdrantVectorStore,
    SearchResult,
    ProjectKnowledgeBase,
    HybridRetriever,
    RetrievalResult,
    Reranker,
    RerankerModel,
    KnowledgeBaseService,
    KnowledgeBaseConfig,
    get_kb_service,
    AIService,
    get_ai_service,
)

# Prompts 模块
from .prompts import (
    PromptTemplate,
    PromptVariable,
    PromptManager,
    FewShotManager,
    FewShotExample,
    ContextManager,
    ConversationContext,
    QualityController,
)

__all__ = [
    # LLM
    'BaseLLM',
    'LLMResponse',
    'TokenUsage',
    'Message',
    'ModelProvider',
    'ZhipuLLM',
    'GeminiLLM',
    'LLMFactory',
    'get_llm_factory',
    'init_llm_factory',
    # RAG
    'TextChunker',
    'TextChunk',
    'ChunkingStrategy',
    'EmbeddingService',
    'LocalEmbedding',
    'init_embedding_service',
    'QdrantVectorStore',
    'SearchResult',
    'ProjectKnowledgeBase',
    'HybridRetriever',
    'RetrievalResult',
    'Reranker',
    'RerankerModel',
    'KnowledgeBaseService',
    'KnowledgeBaseConfig',
    'get_kb_service',
    'AIService',
    'get_ai_service',
    # Prompts
    'PromptTemplate',
    'PromptVariable',
    'PromptManager',
    'FewShotManager',
    'FewShotExample',
    'ContextManager',
    'ConversationContext',
    'QualityController',
]
