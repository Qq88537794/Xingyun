"""
Few-shot学习管理器
管理和选择Few-shot示例
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import random

logger = logging.getLogger(__name__)


@dataclass
class FewShotExample:
    """Few-shot示例"""
    id: str
    input: str                           # 输入文本
    output: str                          # 期望输出
    task_type: str                       # 任务类型
    quality_score: float = 1.0           # 质量分数(用于选择)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'input': self.input,
            'output': self.output,
            'task_type': self.task_type,
            'quality_score': self.quality_score,
            'metadata': self.metadata,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FewShotExample':
        return cls(
            id=data['id'],
            input=data['input'],
            output=data['output'],
            task_type=data['task_type'],
            quality_score=data.get('quality_score', 1.0),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', [])
        )
    
    def format(self, input_label: str = "输入", output_label: str = "输出") -> str:
        """格式化为提示文本"""
        return f"【{input_label}】\n{self.input}\n\n【{output_label}】\n{self.output}"


class FewShotManager:
    """
    Few-shot示例管理器
    提供示例的存储、检索和选择功能
    """
    
    def __init__(self):
        """初始化管理器"""
        # 按任务类型存储示例
        self._examples: Dict[str, List[FewShotExample]] = {}
        
        # 加载内置示例
        self._load_builtin_examples()
    
    def _load_builtin_examples(self):
        """加载内置示例"""
        # 大纲生成示例
        self.add_example(FewShotExample(
            id="outline_1",
            task_type="outline_generation",
            input="主题：人工智能在教育领域的应用",
            output="""1. 引言
   1.1 AI教育的发展背景
   1.2 研究意义与目标

2. AI教育技术概述
   2.1 智能辅导系统
   2.2 自适应学习平台
   2.3 教育数据挖掘

3. 主要应用场景
   3.1 个性化学习路径规划
   3.2 智能作业批改与反馈
   3.3 虚拟教学助手
   3.4 学情分析与预警

4. 案例分析
   4.1 国内典型应用
   4.2 国际先进实践

5. 挑战与展望
   5.1 当前面临的问题
   5.2 未来发展趋势

6. 结论""",
            quality_score=0.95,
            tags=["education", "technology"]
        ))
        
        # 内容扩写示例
        self.add_example(FewShotExample(
            id="expansion_1",
            task_type="content_expansion",
            input="机器学习是人工智能的一个分支。",
            output="""机器学习是人工智能领域中最为活跃和重要的研究分支之一。它专注于研究如何让计算机系统能够自动从数据中学习和改进，而无需进行明确的编程。

从技术原理来看，机器学习通过分析大量数据来识别模式和规律，然后利用这些发现来做出决策或预测。这一过程类似于人类的学习方式——通过经验积累来提升能力。

机器学习主要包含三大类方法：
- **监督学习**：使用带标签的数据进行训练，如图像分类、垃圾邮件识别
- **无监督学习**：从无标签数据中发现隐藏结构，如聚类分析、降维处理
- **强化学习**：通过与环境交互来学习最优策略，如游戏AI、机器人控制

近年来，深度学习的突破使机器学习在图像识别、自然语言处理、语音识别等领域取得了革命性进展，深刻改变了我们的生活方式。""",
            quality_score=0.9,
            tags=["technical", "ai"]
        ))
        
        # 风格迁移示例
        self.add_example(FewShotExample(
            id="style_1",
            task_type="style_transfer",
            input="原文：这个产品使用了最新的技术，性能很好。\n目标风格：营销文案",
            output="颠覆想象，重新定义卓越！我们倾力打造的这款旗舰产品，集成前沿黑科技，带来前所未有的极致性能体验。每一个细节都经过精心雕琢，只为给您呈现完美。",
            quality_score=0.85,
            tags=["marketing", "formal"]
        ))
        
        # 摘要生成示例
        self.add_example(FewShotExample(
            id="summary_1",
            task_type="summary_generation",
            input="""人工智能(AI)是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。这些任务包括学习、推理、问题解决、感知和语言理解。AI的历史可以追溯到1950年代，当时艾伦·图灵提出了著名的"图灵测试"。近年来，随着计算能力的提升和大数据的普及，AI技术取得了突破性进展。深度学习、自然语言处理、计算机视觉等领域都有显著发展。AI正在改变各行各业，从医疗诊断到自动驾驶，从金融分析到客户服务。然而，AI的发展也带来了伦理和社会挑战，包括就业影响、隐私问题和算法偏见等。""",
            output="""人工智能(AI)是致力于模拟人类智能的计算机科学分支，起源于1950年代的图灵测试。近年来受益于算力提升和大数据发展，AI在深度学习、自然语言处理等领域取得重大突破，广泛应用于医疗、自动驾驶、金融等行业。但同时也面临就业影响、隐私和算法偏见等伦理挑战。

**关键词**：人工智能、深度学习、图灵测试、应用落地、伦理挑战""",
            quality_score=0.9,
            tags=["technical", "summary"]
        ))
        
        # 语法检查示例
        self.add_example(FewShotExample(
            id="grammar_1",
            task_type="grammar_check",
            input="他昨天去了北京，并且参加了一个重要得会议。会议上，他发言了很多有意义的观点。",
            output="""**错误列表：**
1. "重要得会议" → "重要的会议" (语法错误：结构助词使用错误)
2. "发言了很多有意义的观点" → "发表了很多有意义的观点" (搭配错误："发言"不能直接搭配"观点")

**修正后的文本：**
他昨天去了北京，并且参加了一个重要的会议。会议上，他发表了很多有意义的观点。""",
            quality_score=0.95,
            tags=["grammar", "chinese"]
        ))
    
    def add_example(self, example: FewShotExample):
        """添加示例"""
        task_type = example.task_type
        if task_type not in self._examples:
            self._examples[task_type] = []
        
        # 检查是否已存在
        existing_ids = {e.id for e in self._examples[task_type]}
        if example.id not in existing_ids:
            self._examples[task_type].append(example)
            logger.debug(f"添加示例: {example.id} (任务类型: {task_type})")
    
    def get_examples(
        self,
        task_type: str,
        n: int = 3,
        tags: Optional[List[str]] = None,
        selection_strategy: str = "quality"
    ) -> List[FewShotExample]:
        """
        获取Few-shot示例
        
        Args:
            task_type: 任务类型
            n: 需要的示例数量
            tags: 过滤标签
            selection_strategy: 选择策略 ('quality', 'random', 'diverse')
        
        Returns:
            示例列表
        """
        if task_type not in self._examples:
            logger.warning(f"任务类型 {task_type} 没有可用示例")
            return []
        
        candidates = self._examples[task_type].copy()
        
        # 标签过滤
        if tags:
            candidates = [
                e for e in candidates
                if any(t in e.tags for t in tags)
            ]
        
        if not candidates:
            return []
        
        # 根据策略选择
        if selection_strategy == "quality":
            # 按质量分数排序
            candidates.sort(key=lambda x: x.quality_score, reverse=True)
            return candidates[:n]
        
        elif selection_strategy == "random":
            # 随机选择
            return random.sample(candidates, min(n, len(candidates)))
        
        elif selection_strategy == "diverse":
            # 多样性选择(尽量选择不同标签的示例)
            selected = []
            used_tags = set()
            
            for example in sorted(candidates, key=lambda x: x.quality_score, reverse=True):
                if len(selected) >= n:
                    break
                
                # 优先选择带有新标签的示例
                new_tags = set(example.tags) - used_tags
                if new_tags or len(selected) < n:
                    selected.append(example)
                    used_tags.update(example.tags)
            
            return selected
        
        return candidates[:n]
    
    def format_examples(
        self,
        task_type: str,
        n: int = 3,
        input_label: str = "输入",
        output_label: str = "输出",
        separator: str = "\n\n---\n\n",
        **kwargs
    ) -> str:
        """
        获取并格式化示例文本
        
        Args:
            task_type: 任务类型
            n: 示例数量
            input_label: 输入标签
            output_label: 输出标签
            separator: 示例之间的分隔符
        
        Returns:
            格式化的示例文本
        """
        examples = self.get_examples(task_type, n, **kwargs)
        
        if not examples:
            return ""
        
        formatted = [
            e.format(input_label, output_label)
            for e in examples
        ]
        
        return separator.join(formatted)
    
    def remove_example(self, example_id: str, task_type: Optional[str] = None):
        """移除示例"""
        if task_type:
            if task_type in self._examples:
                self._examples[task_type] = [
                    e for e in self._examples[task_type]
                    if e.id != example_id
                ]
        else:
            for task_type in self._examples:
                self._examples[task_type] = [
                    e for e in self._examples[task_type]
                    if e.id != example_id
                ]
    
    def update_example_score(self, example_id: str, score: float):
        """更新示例质量分数"""
        for task_type in self._examples:
            for example in self._examples[task_type]:
                if example.id == example_id:
                    example.quality_score = score
                    return
    
    def list_task_types(self) -> List[str]:
        """列出所有任务类型"""
        return list(self._examples.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'task_types': len(self._examples),
            'total_examples': sum(len(v) for v in self._examples.values()),
            'by_task_type': {
                k: len(v) for k, v in self._examples.items()
            }
        }
    
    def export_examples(self, task_type: Optional[str] = None) -> List[Dict]:
        """导出示例"""
        if task_type:
            return [e.to_dict() for e in self._examples.get(task_type, [])]
        
        all_examples = []
        for examples in self._examples.values():
            all_examples.extend(e.to_dict() for e in examples)
        return all_examples
    
    def import_examples(self, examples_data: List[Dict]):
        """导入示例"""
        for data in examples_data:
            example = FewShotExample.from_dict(data)
            self.add_example(example)


# 全局Few-shot管理器
_global_few_shot_manager: Optional[FewShotManager] = None


def get_few_shot_manager() -> FewShotManager:
    """获取全局Few-shot管理器"""
    global _global_few_shot_manager
    if _global_few_shot_manager is None:
        _global_few_shot_manager = FewShotManager()
    return _global_few_shot_manager
