"""
内容质量控制
实现生成内容的质量检查、去重和优化
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """质量报告"""
    score: float                    # 综合质量分数 (0-1)
    issues: List[Dict[str, Any]]    # 发现的问题
    suggestions: List[str]          # 改进建议
    metrics: Dict[str, float]       # 详细指标
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'metrics': self.metrics
        }


class QualityController:
    """
    内容质量控制器
    提供去重、事实核查、质量评分等功能
    """
    
    def __init__(self):
        """初始化质量控制器"""
        # 常见问题模式
        self._repetition_threshold = 0.3  # 重复率阈值
        self._min_length = 50             # 最小长度
        self._max_sentence_length = 200   # 最大句子长度
    
    def check_quality(
        self,
        content: str,
        context: Optional[str] = None,
        check_repetition: bool = True,
        check_coherence: bool = True,
        check_completeness: bool = True
    ) -> QualityReport:
        """
        检查内容质量
        
        Args:
            content: 待检查内容
            context: 原始上下文(用于相关性检查)
            check_repetition: 检查重复
            check_coherence: 检查连贯性
            check_completeness: 检查完整性
        
        Returns:
            QualityReport
        """
        issues = []
        suggestions = []
        metrics = {}
        
        # 1. 基础检查
        if len(content) < self._min_length:
            issues.append({
                'type': 'length',
                'severity': 'warning',
                'message': f'内容过短 ({len(content)} 字符)'
            })
            suggestions.append('建议增加更多内容细节')
        
        # 2. 重复检查
        if check_repetition:
            rep_score, rep_issues = self._check_repetition(content)
            metrics['repetition_score'] = rep_score
            issues.extend(rep_issues)
            
            if rep_score < 0.7:
                suggestions.append('发现较多重复内容，建议精简或改写')
        
        # 3. 连贯性检查
        if check_coherence:
            coh_score, coh_issues = self._check_coherence(content)
            metrics['coherence_score'] = coh_score
            issues.extend(coh_issues)
            
            if coh_score < 0.6:
                suggestions.append('内容连贯性较差，建议增加过渡语句')
        
        # 4. 完整性检查
        if check_completeness:
            comp_score, comp_issues = self._check_completeness(content)
            metrics['completeness_score'] = comp_score
            issues.extend(comp_issues)
        
        # 5. 格式检查
        fmt_score, fmt_issues = self._check_formatting(content)
        metrics['format_score'] = fmt_score
        issues.extend(fmt_issues)
        
        # 计算综合分数
        weights = {
            'repetition_score': 0.25,
            'coherence_score': 0.25,
            'completeness_score': 0.25,
            'format_score': 0.25
        }
        
        total_score = sum(
            metrics.get(k, 1.0) * w
            for k, w in weights.items()
        )
        
        return QualityReport(
            score=total_score,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )
    
    def _check_repetition(self, content: str) -> Tuple[float, List[Dict]]:
        """检查重复内容"""
        issues = []
        
        # 1. 句子级重复
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 1:
            # 计算句子相似度
            sentence_set = set()
            duplicates = []
            
            for sent in sentences:
                # 简化比较(去除标点空格)
                simplified = re.sub(r'[\s\W]', '', sent)
                if simplified in sentence_set:
                    duplicates.append(sent)
                else:
                    sentence_set.add(simplified)
            
            if duplicates:
                issues.append({
                    'type': 'repetition',
                    'severity': 'warning',
                    'message': f'发现 {len(duplicates)} 处重复句子',
                    'details': duplicates[:3]
                })
        
        # 2. 短语级重复 (n-gram)
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content)
        
        if len(words) >= 4:
            # 检查3-gram重复
            trigrams = [tuple(words[i:i+3]) for i in range(len(words) - 2)]
            trigram_counts = Counter(trigrams)
            
            repeated_phrases = [
                ' '.join(phrase) 
                for phrase, count in trigram_counts.items() 
                if count > 2
            ]
            
            if repeated_phrases:
                issues.append({
                    'type': 'phrase_repetition',
                    'severity': 'info',
                    'message': f'发现 {len(repeated_phrases)} 处重复短语',
                    'details': repeated_phrases[:3]
                })
        
        # 计算重复分数
        unique_ratio = len(sentence_set) / len(sentences) if sentences else 1.0
        return unique_ratio, issues
    
    def _check_coherence(self, content: str) -> Tuple[float, List[Dict]]:
        """检查连贯性"""
        issues = []
        
        # 分段
        paragraphs = content.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # 检查过渡词使用
        transition_words = [
            '首先', '其次', '然后', '最后', '此外', '另外',
            '因此', '所以', '但是', '然而', '不过', '总之',
            '例如', '比如', '换句话说', '一方面', '另一方面'
        ]
        
        transition_count = sum(
            1 for word in transition_words
            if word in content
        )
        
        expected_transitions = max(1, len(paragraphs) - 1)
        transition_ratio = min(1.0, transition_count / expected_transitions)
        
        if transition_ratio < 0.3 and len(paragraphs) > 2:
            issues.append({
                'type': 'coherence',
                'severity': 'info',
                'message': '过渡语使用较少，内容可能不够连贯'
            })
        
        # 检查句子长度一致性
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if sentences:
            lengths = [len(s) for s in sentences]
            avg_length = sum(lengths) / len(lengths)
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            
            # 长度差异过大
            if variance > 2000:
                issues.append({
                    'type': 'sentence_length',
                    'severity': 'info',
                    'message': '句子长度差异较大，可能影响阅读流畅性'
                })
        
        score = 0.7 + 0.3 * transition_ratio
        return score, issues
    
    def _check_completeness(self, content: str) -> Tuple[float, List[Dict]]:
        """检查完整性"""
        issues = []
        score = 1.0
        
        # 检查是否有未完成的句子
        if content and not re.search(r'[。！？.!?]\s*$', content.strip()):
            issues.append({
                'type': 'incomplete',
                'severity': 'warning',
                'message': '内容可能未完成，缺少结束标点'
            })
            score -= 0.2
        
        # 检查是否有明显的占位符
        placeholders = re.findall(r'\[.{1,20}\]|{.{1,20}}|TODO|FIXME|XXX', content)
        if placeholders:
            issues.append({
                'type': 'placeholder',
                'severity': 'error',
                'message': f'发现 {len(placeholders)} 处占位符',
                'details': placeholders[:5]
            })
            score -= 0.3
        
        # 检查空白内容
        if re.search(r'\n{4,}', content):
            issues.append({
                'type': 'empty_section',
                'severity': 'info',
                'message': '存在大段空白区域'
            })
            score -= 0.1
        
        return max(0, score), issues
    
    def _check_formatting(self, content: str) -> Tuple[float, List[Dict]]:
        """检查格式"""
        issues = []
        score = 1.0
        
        # 检查过长句子
        sentences = re.split(r'[。！？.!?]', content)
        long_sentences = [s for s in sentences if len(s.strip()) > self._max_sentence_length]
        
        if long_sentences:
            issues.append({
                'type': 'long_sentence',
                'severity': 'info',
                'message': f'发现 {len(long_sentences)} 处过长句子(>200字)',
            })
            score -= 0.1 * min(3, len(long_sentences))
        
        # 检查连续标点
        if re.search(r'[。！？.!?]{2,}', content):
            issues.append({
                'type': 'punctuation',
                'severity': 'info',
                'message': '存在连续标点符号'
            })
            score -= 0.05
        
        return max(0, score), issues
    
    def remove_duplicates(self, content: str) -> str:
        """
        去除重复内容
        
        Args:
            content: 原始内容
        
        Returns:
            去重后的内容
        """
        # 按段落处理
        paragraphs = content.split('\n\n')
        seen_paragraphs = set()
        unique_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 简化比较
            simplified = re.sub(r'\s+', '', para)
            
            if simplified not in seen_paragraphs:
                seen_paragraphs.add(simplified)
                unique_paragraphs.append(para)
        
        # 句子级去重
        result_paragraphs = []
        for para in unique_paragraphs:
            sentences = re.split(r'([。！？.!?])', para)
            seen_sentences = set()
            unique_sentences = []
            
            i = 0
            while i < len(sentences):
                sent = sentences[i].strip()
                punct = sentences[i + 1] if i + 1 < len(sentences) else ''
                
                simplified = re.sub(r'\s+', '', sent)
                if simplified and simplified not in seen_sentences:
                    seen_sentences.add(simplified)
                    unique_sentences.append(sent + punct)
                
                i += 2
            
            if unique_sentences:
                result_paragraphs.append(''.join(unique_sentences))
        
        return '\n\n'.join(result_paragraphs)
    
    def improve_content(
        self,
        content: str,
        auto_fix: bool = True
    ) -> Tuple[str, QualityReport]:
        """
        改进内容质量
        
        Args:
            content: 原始内容
            auto_fix: 是否自动修复可修复的问题
        
        Returns:
            (改进后的内容, 质量报告)
        """
        if auto_fix:
            # 自动修复
            content = self.remove_duplicates(content)
            
            # 修复连续标点
            content = re.sub(r'([。！？.!?]){2,}', r'\1', content)
            
            # 修复多余空行
            content = re.sub(r'\n{4,}', '\n\n\n', content)
            
            # 修复首尾空白
            content = content.strip()
        
        # 生成质量报告
        report = self.check_quality(content)
        
        return content, report


# 全局质量控制器
_global_quality_controller: Optional[QualityController] = None


def get_quality_controller() -> QualityController:
    """获取全局质量控制器"""
    global _global_quality_controller
    if _global_quality_controller is None:
        _global_quality_controller = QualityController()
    return _global_quality_controller
