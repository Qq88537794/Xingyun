"""
文档智能压缩工具
用于在保留结构信息的前提下压缩长文档
"""

import re
from typing import List, Tuple


def extract_headings(content: str) -> List[Tuple[str, int]]:
    """
    提取文档中的所有标题
    
    Returns:
        List of (heading_text, level) tuples
    """
    headings = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Markdown标题 (# ## ###)
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            if text:
                headings.append((text, level))
        
        # 数字编号标题 (1. 1.1 1.1.1)
        elif re.match(r'^\d+(\.\d+)*\.?\s+', line):
            # 计算层级
            dots = line.split()[0].count('.')
            level = dots + 1
            text = re.sub(r'^\d+(\.\d+)*\.?\s+', '', line).strip()
            if text and len(text) > 2:  # 避免太短的标题
                headings.append((text, level))
        
        # 中文编号标题 (一、二、三、)
        elif re.match(r'^[一二三四五六七八九十]+[、．]', line):
            text = re.sub(r'^[一二三四五六七八九十]+[、．]\s*', '', line).strip()
            if text and len(text) > 2:
                headings.append((text, 1))
    
    return headings


def extract_chapter_content(content: str, max_chars_per_chapter: int = 200) -> List[str]:
    """
    提取每个章节的关键内容
    
    Args:
        content: 文档内容
        max_chars_per_chapter: 每个章节最多保留的字符数
    
    Returns:
        List of chapter summaries
    """
    # 按段落分割
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    chapter_contents = []
    current_chapter = []
    current_length = 0
    
    for para in paragraphs:
        # 检查是否是标题
        is_heading = (
            para.startswith('#') or
            re.match(r'^\d+(\.\d+)*\.?\s+', para) or
            re.match(r'^[一二三四五六七八九十]+[、．]', para)
        )
        
        if is_heading and current_chapter:
            # 新章节开始，保存当前章节
            chapter_text = '\n'.join(current_chapter)
            if len(chapter_text) > max_chars_per_chapter:
                # 只保留前面的内容
                chapter_text = chapter_text[:max_chars_per_chapter] + '...'
            chapter_contents.append(chapter_text)
            current_chapter = [para]
            current_length = len(para)
        else:
            # 继续当前章节
            if current_length < max_chars_per_chapter:
                current_chapter.append(para)
                current_length += len(para)
    
    # 保存最后一个章节
    if current_chapter:
        chapter_text = '\n'.join(current_chapter)
        if len(chapter_text) > max_chars_per_chapter:
            chapter_text = chapter_text[:max_chars_per_chapter] + '...'
        chapter_contents.append(chapter_text)
    
    return chapter_contents


def compress_document_for_outline(content: str, max_length: int = 12000) -> str:
    """
    智能压缩文档，用于生成大纲
    
    策略：
    1. 提取所有标题（完整保留）
    2. 提取每个章节的开头部分（关键信息）
    3. 组合成压缩版本
    
    Args:
        content: 原始文档内容
        max_length: 最大长度限制
    
    Returns:
        压缩后的文档内容
    """
    if len(content) <= max_length:
        # 文档不长，直接返回
        return content
    
    # 1. 提取所有标题
    headings = extract_headings(content)
    
    # 2. 构建压缩版本
    compressed_parts = []
    
    # 添加文档开头（通常是引言或摘要）
    first_section = content[:500]
    compressed_parts.append(first_section)
    compressed_parts.append('\n\n')
    
    # 3. 按章节提取内容
    lines = content.split('\n')
    current_section = []
    section_char_count = 0
    max_section_chars = 300  # 每个章节最多保留300字符
    
    in_section = False
    section_count = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        # 检查是否是标题行
        is_heading = (
            line_stripped.startswith('#') or
            re.match(r'^\d+(\.\d+)*\.?\s+', line_stripped) or
            re.match(r'^[一二三四五六七八九十]+[、．]', line_stripped)
        )
        
        if is_heading and len(line_stripped) > 2:
            # 保存上一个章节
            if current_section and section_count > 0:
                section_text = '\n'.join(current_section)
                if len(section_text) > max_section_chars:
                    section_text = section_text[:max_section_chars] + '...'
                compressed_parts.append(section_text)
                compressed_parts.append('\n\n')
            
            # 开始新章节
            current_section = [line]
            section_char_count = len(line)
            in_section = True
            section_count += 1
        
        elif in_section and section_char_count < max_section_chars:
            # 继续当前章节，但限制长度
            if line_stripped:  # 跳过空行
                current_section.append(line)
                section_char_count += len(line)
    
    # 添加最后一个章节
    if current_section:
        section_text = '\n'.join(current_section)
        if len(section_text) > max_section_chars:
            section_text = section_text[:max_section_chars] + '...'
        compressed_parts.append(section_text)
    
    # 4. 组合并检查长度
    compressed = ''.join(compressed_parts)
    
    # 如果还是太长，进一步压缩
    if len(compressed) > max_length:
        # 只保留标题和极少的内容
        compressed_parts = []
        compressed_parts.append(content[:300])  # 开头
        compressed_parts.append('\n\n[文档结构]\n')
        
        # 只保留标题
        for heading, level in headings:
            indent = '  ' * (level - 1)
            compressed_parts.append(f'{indent}{heading}\n')
        
        compressed = ''.join(compressed_parts)
        
        # 如果还是太长，截断
        if len(compressed) > max_length:
            compressed = compressed[:max_length]
    
    return compressed


def get_compression_stats(original: str, compressed: str) -> dict:
    """
    获取压缩统计信息
    
    Returns:
        dict with compression statistics
    """
    return {
        'original_length': len(original),
        'compressed_length': len(compressed),
        'compression_ratio': len(compressed) / len(original) if len(original) > 0 else 0,
        'chars_saved': len(original) - len(compressed)
    }
