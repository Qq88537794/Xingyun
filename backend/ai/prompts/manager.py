"""
提示管理器
统一管理提示模板和Few-shot示例
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Callable

from .template import PromptTemplate, BUILTIN_TEMPLATES, PromptVariable
from .few_shot import FewShotManager, get_few_shot_manager, FewShotExample

logger = logging.getLogger(__name__)


class PromptManager:
    """
    提示管理器
    提供模板的统一管理、加载和渲染功能
    """
    
    def __init__(
        self,
        templates_dir: Optional[str] = None,
        load_builtin: bool = True
    ):
        """
        初始化提示管理器
        
        Args:
            templates_dir: 模板目录路径
            load_builtin: 是否加载内置模板
        """
        self._templates: Dict[str, PromptTemplate] = {}
        self._few_shot_manager = get_few_shot_manager()
        self._templates_dir = templates_dir
        
        # 加载内置模板
        if load_builtin:
            self._load_builtin_templates()
        
        # 加载目录模板
        if templates_dir:
            self.load_from_directory(templates_dir)
    
    def _load_builtin_templates(self):
        """加载内置模板"""
        for name, template in BUILTIN_TEMPLATES.items():
            self._templates[name] = template
        logger.info(f"加载 {len(BUILTIN_TEMPLATES)} 个内置模板")
    
    def load_from_directory(self, directory: str):
        """
        从目录加载模板文件
        支持 .json 和 .txt 格式
        """
        if not os.path.exists(directory):
            logger.warning(f"模板目录不存在: {directory}")
            return
        
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if filename.endswith('.json'):
                self._load_json_template(filepath)
            elif filename.endswith('.txt'):
                self._load_txt_template(filepath)
    
    def _load_json_template(self, filepath: str):
        """加载JSON格式模板"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            template = PromptTemplate.from_dict(data)
            self._templates[template.name] = template
            logger.debug(f"加载模板: {template.name} (from {filepath})")
            
        except Exception as e:
            logger.error(f"加载模板失败 {filepath}: {e}")
    
    def _load_txt_template(self, filepath: str):
        """加载纯文本格式模板"""
        try:
            filename = os.path.basename(filepath)
            name = os.path.splitext(filename)[0]
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            template = PromptTemplate(
                name=name,
                template=content
            )
            self._templates[name] = template
            logger.debug(f"加载模板: {name} (from {filepath})")
            
        except Exception as e:
            logger.error(f"加载模板失败 {filepath}: {e}")
    
    def register_template(self, template: PromptTemplate, overwrite: bool = False):
        """
        注册模板
        
        Args:
            template: 提示模板
            overwrite: 是否覆盖同名模板
        """
        if template.name in self._templates and not overwrite:
            raise ValueError(f"模板 {template.name} 已存在，设置 overwrite=True 覆盖")
        
        self._templates[template.name] = template
        logger.info(f"注册模板: {template.name}")
    
    def create_template(
        self,
        name: str,
        template: str,
        description: str = "",
        variables: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None
    ) -> PromptTemplate:
        """
        创建并注册新模板
        
        Args:
            name: 模板名称
            template: 模板内容
            description: 描述
            variables: 变量定义
            tags: 标签
        
        Returns:
            创建的模板
        """
        var_list = []
        if variables:
            from .template import VariableType
            for v in variables:
                var_list.append(PromptVariable(
                    name=v['name'],
                    var_type=VariableType(v.get('type', 'string')),
                    default=v.get('default'),
                    description=v.get('description', ''),
                    required=v.get('required', True)
                ))
        
        prompt_template = PromptTemplate(
            name=name,
            template=template,
            description=description,
            variables=var_list,
            tags=tags or []
        )
        
        self.register_template(prompt_template)
        return prompt_template
    
    def get_template(self, name: str) -> PromptTemplate:
        """获取模板"""
        if name not in self._templates:
            raise KeyError(f"模板不存在: {name}")
        return self._templates[name]
    
    def render(
        self,
        template_name: str,
        include_few_shot: bool = False,
        few_shot_count: int = 3,
        **kwargs
    ) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            include_few_shot: 是否包含Few-shot示例
            few_shot_count: Few-shot示例数量
            **kwargs: 模板变量
        
        Returns:
            渲染后的提示文本
        """
        template = self.get_template(template_name)
        
        # 添加Few-shot示例
        if include_few_shot:
            examples = self._few_shot_manager.format_examples(
                task_type=template_name,
                n=few_shot_count
            )
            if examples and 'examples' not in kwargs:
                kwargs['examples'] = examples
        
        return template.render(**kwargs)
    
    def render_with_context(
        self,
        template_name: str,
        context: str,
        **kwargs
    ) -> str:
        """
        渲染带有RAG上下文的模板
        
        Args:
            template_name: 模板名称
            context: RAG检索到的上下文
            **kwargs: 其他变量
        
        Returns:
            渲染后的提示文本
        """
        kwargs['context'] = context
        return self.render(template_name, **kwargs)
    
    def list_templates(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有模板
        
        Args:
            tag: 按标签过滤
        
        Returns:
            模板信息列表
        """
        templates = []
        for name, template in self._templates.items():
            if tag and tag not in template.tags:
                continue
            
            templates.append({
                'name': name,
                'description': template.description,
                'tags': template.tags,
                'variables': template.get_required_variables(),
                'version': template.version
            })
        
        return templates
    
    def delete_template(self, name: str):
        """删除模板"""
        if name in self._templates:
            del self._templates[name]
            logger.info(f"删除模板: {name}")
    
    def save_template(self, name: str, filepath: str):
        """保存模板到文件"""
        if name not in self._templates:
            raise KeyError(f"模板不存在: {name}")
        
        template = self._templates[name]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"保存模板 {name} 到 {filepath}")
    
    # Few-shot 相关方法
    def add_few_shot_example(self, example: FewShotExample):
        """添加Few-shot示例"""
        self._few_shot_manager.add_example(example)
    
    def get_few_shot_examples(
        self,
        task_type: str,
        n: int = 3,
        **kwargs
    ) -> List[FewShotExample]:
        """获取Few-shot示例"""
        return self._few_shot_manager.get_examples(task_type, n, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'templates_count': len(self._templates),
            'templates': list(self._templates.keys()),
            'few_shot_stats': self._few_shot_manager.get_stats()
        }


# 预定义任务特定的提示构建器
class PromptBuilder:
    """
    提示构建器
    提供更简洁的提示构建方式
    """
    
    def __init__(self, manager: Optional[PromptManager] = None):
        self.manager = manager or get_prompt_manager()
    
    def outline(
        self,
        topic: str,
        context: Optional[str] = None,
        requirements: Optional[str] = None,
        style: Optional[str] = None,
        include_examples: bool = True
    ) -> str:
        """构建大纲生成提示"""
        return self.manager.render(
            'outline_generation',
            topic=topic,
            context=context,
            requirements=requirements,
            style=style,
            include_few_shot=include_examples
        )
    
    def expand(
        self,
        content: str,
        context: Optional[str] = None,
        ratio: str = "2-3",
        tone: str = "专业、正式",
        focus_areas: Optional[List[str]] = None,
        include_examples: bool = True
    ) -> str:
        """构建内容扩写提示"""
        return self.manager.render(
            'content_expansion',
            content=content,
            context=context,
            expansion_ratio=ratio,
            tone=tone,
            focus_areas=focus_areas,
            include_few_shot=include_examples
        )
    
    def style_transfer(
        self,
        content: str,
        target_style: str,
        style_description: str = "",
        examples: Optional[str] = None,
        preserve_structure: bool = True
    ) -> str:
        """构建风格迁移提示"""
        return self.manager.render(
            'style_transfer',
            content=content,
            target_style=target_style,
            style_description=style_description,
            examples=examples,
            preserve_structure=preserve_structure
        )
    
    def summarize(
        self,
        content: str,
        length: str = "200-300字",
        include_keywords: bool = True,
        focus_points: Optional[str] = None
    ) -> str:
        """构建摘要生成提示"""
        return self.manager.render(
            'summary_generation',
            content=content,
            summary_length=length,
            include_keywords=include_keywords,
            focus_points=focus_points
        )
    
    def rag_qa(
        self,
        question: str,
        context: str,
        chat_history: Optional[str] = None,
        response_format: Optional[str] = None
    ) -> str:
        """构建RAG问答提示"""
        return self.manager.render(
            'rag_qa',
            question=question,
            context=context,
            chat_history=chat_history,
            response_format=response_format
        )
    
    def grammar_check(
        self,
        content: str,
        check_style: bool = False
    ) -> str:
        """构建语法检查提示"""
        return self.manager.render(
            'grammar_check',
            content=content,
            check_style=check_style
        )


# 全局提示管理器
_global_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """获取全局提示管理器"""
    global _global_prompt_manager
    if _global_prompt_manager is None:
        _global_prompt_manager = PromptManager()
    return _global_prompt_manager


def get_prompt_builder() -> PromptBuilder:
    """获取提示构建器"""
    return PromptBuilder(get_prompt_manager())
