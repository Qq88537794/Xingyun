"""
文本分块器
实现多种文本分块策略，处理长文档的分块与上下文窗口管理
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """分块策略枚举"""
    FIXED_SIZE = "fixed_size"           # 固定大小分块
    SENTENCE = "sentence"               # 按句子分块
    PARAGRAPH = "paragraph"             # 按段落分块
    SEMANTIC = "semantic"               # 语义分块
    RECURSIVE = "recursive"             # 递归分块
    MARKDOWN = "markdown"               # Markdown结构分块
    SLIDING_WINDOW = "sliding_window"   # 滑动窗口分块


@dataclass
class TextChunk:
    """文本块数据类"""
    id: str                          # 块ID
    content: str                     # 块内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    start_index: int = 0             # 在原文中的起始位置
    end_index: int = 0               # 在原文中的结束位置
    chunk_index: int = 0             # 块索引
    token_count: int = 0             # 估算token数
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'start_index': self.start_index,
            'end_index': self.end_index,
            'chunk_index': self.chunk_index,
            'token_count': self.token_count
        }


class TextChunker:
    """
    文本分块器
    支持多种分块策略，用于RAG系统的文档预处理
    """
    
    # 句子分隔符
    SENTENCE_SEPARATORS = [
        '。', '！', '？', '；',  # 中文
        '.', '!', '?', ';',      # 英文
        '\n\n',                   # 空行
    ]
    
    # 段落分隔符
    PARAGRAPH_SEPARATORS = ['\n\n', '\r\n\r\n']
    
    # Markdown标题模式
    MARKDOWN_HEADER_PATTERN = r'^#{1,6}\s+'
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        separators: Optional[List[str]] = None,
        length_function: Optional[Callable[[str], int]] = None
    ):
        """
        初始化分块器
        
        Args:
            chunk_size: 目标块大小(字符数或token数)
            chunk_overlap: 块之间的重叠大小
            strategy: 分块策略
            separators: 自定义分隔符列表
            length_function: 长度计算函数(默认使用字符数)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.separators = separators
        self.length_function = length_function or len
        
        # 递归分块的默认分隔符优先级
        self._recursive_separators = [
            '\n\n',    # 段落
            '\n',      # 换行
            '。', '！', '？',  # 中文句子结束
            '.', '!', '?',    # 英文句子结束
            '，', '；',       # 中文逗号分号
            ',', ';',         # 英文逗号分号
            ' ',              # 空格
            ''                # 字符级别
        ]
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> List[TextChunk]:
        """
        对文本进行分块
        
        Args:
            text: 待分块文本
            metadata: 文档元数据
            doc_id: 文档ID
        
        Returns:
            TextChunk列表
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        doc_id = doc_id or "doc"
        
        # 根据策略选择分块方法
        strategy_methods = {
            ChunkingStrategy.FIXED_SIZE: self._chunk_fixed_size,
            ChunkingStrategy.SENTENCE: self._chunk_by_sentence,
            ChunkingStrategy.PARAGRAPH: self._chunk_by_paragraph,
            ChunkingStrategy.RECURSIVE: self._chunk_recursive,
            ChunkingStrategy.MARKDOWN: self._chunk_markdown,
            ChunkingStrategy.SLIDING_WINDOW: self._chunk_sliding_window,
        }
        
        method = strategy_methods.get(self.strategy, self._chunk_recursive)
        raw_chunks = method(text)
        
        # 创建TextChunk对象
        chunks = []
        current_pos = 0
        
        for i, content in enumerate(raw_chunks):
            # 查找在原文中的位置
            start_idx = text.find(content, current_pos)
            if start_idx == -1:
                start_idx = current_pos
            end_idx = start_idx + len(content)
            
            chunk = TextChunk(
                id=f"{doc_id}_chunk_{i}",
                content=content,
                metadata={**metadata, 'doc_id': doc_id},
                start_index=start_idx,
                end_index=end_idx,
                chunk_index=i,
                token_count=self._estimate_tokens(content)
            )
            chunks.append(chunk)
            current_pos = start_idx + 1
        
        logger.info(f"文档 {doc_id} 分块完成: {len(chunks)} 块")
        return chunks
    
    def _chunk_fixed_size(self, text: str) -> List[str]:
        """固定大小分块"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap if end < text_len else end
        
        return chunks
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """按句子分块"""
        # 使用正则分割句子
        sentence_pattern = r'([。！？.!?]+[\s]*)'
        sentences = re.split(sentence_pattern, text)
        
        # 合并分隔符和句子
        merged_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence.strip():
                merged_sentences.append(sentence)
        
        # 如果最后一个不是分隔符
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            merged_sentences.append(sentences[-1])
        
        # 合并小句子到目标大小
        return self._merge_small_chunks(merged_sentences)
    
    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """按段落分块"""
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return self._merge_small_chunks(paragraphs)
    
    def _chunk_recursive(
        self,
        text: str,
        separators: Optional[List[str]] = None
    ) -> List[str]:
        """
        递归分块
        尝试使用不同的分隔符，从大到小粒度
        """
        separators = separators or self._recursive_separators
        
        final_chunks = []
        
        # 如果文本已经足够小，直接返回
        if self.length_function(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        # 尝试使用当前分隔符分割
        separator = separators[0]
        remaining_separators = separators[1:] if len(separators) > 1 else ['']
        
        if separator:
            splits = text.split(separator)
        else:
            # 字符级别分割
            splits = list(text)
        
        # 合并小块
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_with_sep = split + separator if separator else split
            split_length = self.length_function(split_with_sep)
            
            # 如果单个分割就超过大小，递归处理
            if split_length > self.chunk_size and remaining_separators:
                # 先保存当前累积的内容
                if current_chunk:
                    merged = separator.join(current_chunk) if separator else ''.join(current_chunk)
                    final_chunks.append(merged)
                    current_chunk = []
                    current_length = 0
                
                # 递归处理大块
                sub_chunks = self._chunk_recursive(split, remaining_separators)
                final_chunks.extend(sub_chunks)
            
            elif current_length + split_length > self.chunk_size:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    merged = separator.join(current_chunk) if separator else ''.join(current_chunk)
                    final_chunks.append(merged)
                
                # 添加重叠
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = self._get_overlap(merged)
                    current_chunk = [overlap_text, split] if overlap_text else [split]
                    current_length = self.length_function(overlap_text or '') + split_length
                else:
                    current_chunk = [split]
                    current_length = split_length
            else:
                current_chunk.append(split)
                current_length += split_length
        
        # 处理最后的块
        if current_chunk:
            merged = separator.join(current_chunk) if separator else ''.join(current_chunk)
            if merged.strip():
                final_chunks.append(merged)
        
        return final_chunks
    
    def _chunk_markdown(self, text: str) -> List[str]:
        """
        Markdown结构分块
        按标题层级分块，保持文档结构
        """
        chunks = []
        
        # 按标题分割
        header_pattern = r'(^#{1,6}\s+.+$)'
        parts = re.split(header_pattern, text, flags=re.MULTILINE)
        
        current_chunk = ""
        current_header = ""
        
        for part in parts:
            if re.match(r'^#{1,6}\s+', part):
                # 这是一个标题
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_header = part
                current_chunk = part
            else:
                # 这是内容
                if self.length_function(current_chunk + part) > self.chunk_size:
                    # 当前块太大，需要进一步分割内容
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    
                    # 对大内容使用递归分块
                    sub_chunks = self._chunk_recursive(part)
                    for i, sub_chunk in enumerate(sub_chunks):
                        if i == 0 and current_header:
                            chunks.append(current_header + '\n' + sub_chunk)
                        else:
                            chunks.append(sub_chunk)
                    
                    current_chunk = ""
                    current_header = ""
                else:
                    current_chunk += part
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_sliding_window(self, text: str) -> List[str]:
        """
        滑动窗口分块
        固定步长滑动，每个块之间有固定重叠
        """
        chunks = []
        step = self.chunk_size - self.chunk_overlap
        
        for start in range(0, len(text), step):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            
            if end >= len(text):
                break
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """合并小块到目标大小"""
        merged = []
        current = []
        current_length = 0
        
        for chunk in chunks:
            chunk_length = self.length_function(chunk)
            
            if current_length + chunk_length > self.chunk_size and current:
                merged.append('\n'.join(current))
                
                # 添加重叠
                if self.chunk_overlap > 0:
                    overlap = self._get_overlap('\n'.join(current))
                    current = [overlap] if overlap else []
                    current_length = len(overlap) if overlap else 0
                else:
                    current = []
                    current_length = 0
            
            current.append(chunk)
            current_length += chunk_length
        
        if current:
            merged.append('\n'.join(current))
        
        return merged
    
    def _get_overlap(self, text: str) -> str:
        """获取重叠文本"""
        if len(text) <= self.chunk_overlap:
            return text
        return text[-self.chunk_overlap:]
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        # 粗略估算
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def set_strategy(self, strategy: ChunkingStrategy):
        """设置分块策略"""
        self.strategy = strategy
    
    def get_config(self) -> Dict[str, Any]:
        """获取分块器配置"""
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'strategy': self.strategy.value
        }
