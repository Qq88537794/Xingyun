# 行云智能文档工作站技术架构

## 后端技术栈
- **Web框架**: Flask 3.0
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy
- **认证**: JWT (Flask-JWT-Extended)
- **AI服务**: 智谱AI GLM-4

## 前端技术栈
- **框架**: Vue 3 + Vite
- **UI库**: Tailwind CSS
- **状态管理**: Pinia
- **编辑器**: 自研富文本编辑器

## AI功能
- 智能问答（支持RAG检索增强）
- 文档大纲生成
- 内容扩写
- 摘要生成
- Agent工具调用

## 向量数据库
- **存储**: Qdrant
- **嵌入模型**: BGE-small-zh-v1.5
- **检索算法**: 余弦相似度