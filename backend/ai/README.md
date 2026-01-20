# AI 模块说明文档

## 概述

AI模块为行云智能文档工作站提供智能文档处理能力，包括：

1. **统一问答接口** - 单一入口处理所有AI请求
2. **RAG检索增强** - 基于项目知识库的上下文增强
3. **Agent工具调用** - 基于Finish Reason驱动的智能文档操作

## 架构

```
ai/
├── __init__.py              # AI模块入口
├── schema.py                # POJO数据结构定义
├── README.md                # 本文档
├── agent/                   # Agent模块
│   ├── __init__.py
│   ├── tools.py            # 工具定义
│   └── processor.py        # Agent处理器
├── llm/                     # LLM提供商
│   ├── __init__.py
│   ├── base.py             # LLM基类
│   ├── factory.py          # LLM工厂
│   ├── zhipu.py            # 智谱清言
│   └── gemini.py           # Google Gemini
├── rag/                     # RAG模块
│   ├── __init__.py
│   ├── ai_service.py       # AI核心服务
│   ├── embedding.py        # 向量化服务
│   ├── knowledge_base.py   # 知识库服务
│   └── vector_store.py     # 向量存储
└── prompts/                 # 提示词管理
    ├── __init__.py
    └── context.py          # 上下文管理
```

## 核心组件

### 1. AIService (ai/rag/ai_service.py)

统一的AI服务入口，支持两种模式：

#### Simple模式（默认）

- 直接调用LLM生成响应
- 自动解析AI建议的文档操作
- 适用于简单问答和单次操作

#### Agent模式（enable_agent=true）

- 使用Finish Reason驱动的循环
- 支持多步骤工具调用
- 适用于复杂文档编辑任务

### 2. Agent模块 (ai/agent/)

基于工具调用的智能处理系统：

```python
# 核心流程
while iterations < max_iterations:
    response = llm.chat_with_tools(messages, tools)
    
    if finish_reason == "tool_calls":
        for tool_call in tool_calls:
            result = tool_registry.execute(name, arguments)
            messages.append(tool_result_message)
        continue  # 继续循环
    
    elif finish_reason == "stop":
        return final_response  # 任务完成
```

#### 可用工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `read_document` | 读取文档内容 | document_id |
| `write_document` | 覆盖写入文档 | document_id, content |
| `edit_document` | 编辑文档部分 | document_id, action, position, content |
| `search_document` | 搜索文档内容 | document_id, query |
| `generate_outline` | 生成大纲 | topic, requirements |
| `expand_content` | 扩写内容 | content, ratio |
| `summarize` | 生成摘要 | content, max_length |

### 3. LLM提供商 (ai/llm/)

支持多个LLM提供商，通过工厂模式切换：

- **智谱清言 (Zhipu)** - 默认，支持Function Calling
- **Google Gemini** - 支持Function Calling
- 可扩展其他提供商

### 4. RAG模块 (ai/rag/)

基于Qdrant的向量检索增强：

- **Embedding** - 使用BAAI/bge-small-zh-v1.5本地模型
- **Vector Store** - Qdrant向量数据库
- **Knowledge Base** - 项目知识库管理

## API接口

### POST /api/ai/chat

统一问答接口，支持所有AI功能。

**请求参数：**

```json
{
    "message": "用户输入（必需）",
    "session_id": "会话ID（可选）",
    "project_id": 1,
    "document_content": "当前文档内容",
    "document_id": "文档ID",
    "selected_text": "选中的文本",
    "selection_range": {"start": 0, "end": 100},
    "enable_rag": true,
    "enable_agent": false,
    "stream": false
}
```

**响应格式：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "message": "AI的回复说明",
        "operations": [
            {
                "operation_type": "replace",
                "target_file": "文档ID",
                "content": "新内容",
                "position": null,
                "metadata": {}
            }
        ],
        "sources": [
            {"text": "来源文本...", "score": 0.85, "resource_id": 1}
        ],
        "session_id": "会话ID",
        "tokens_used": 100,
        "requires_confirmation": true,
        "metadata": {
            "agent_iterations": 3,
            "agent_tool_calls": [...]
        }
    }
}
```

**流式响应事件：**

```
data: {"type": "content", "content": "AI回复..."}
data: {"type": "thinking", "iteration": 1}
data: {"type": "tool_call", "name": "read_document", "arguments": {...}}
data: {"type": "tool_result", "name": "read_document", "result": {...}}
data: {"type": "done", "session_id": "...", ...}
```

## 使用示例

### 简单问答

```python
request = AIRequest(
    message="帮我总结这篇文档",
    document_content="文档内容...",
    enable_agent=False
)
response = ai_service.chat(request)
```

### Agent模式文档编辑

```python
request = AIRequest(
    message="把文档第二段的'旧词'替换成'新词'",
    document_content="文档内容...",
    document_id="doc_123",
    enable_agent=True
)
response = ai_service.chat(request)

# response.operations 包含修改后的完整文档
```

### RAG增强问答

```python
request = AIRequest(
    message="根据知识库回答：什么是RAG？",
    project_id=1,
    enable_rag=True
)
response = ai_service.chat(request)

# response.sources 包含引用的知识库内容
```

## 配置

环境变量配置（.env）：

```env
# LLM配置
LLM_PROVIDER=zhipu              # zhipu 或 gemini
ZHIPU_API_KEY=your_api_key      # 智谱API密钥
GEMINI_API_KEY=your_api_key     # Gemini API密钥

# Embedding配置
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5  # 本地embedding模型

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_MEMORY_MODE=true         # 开发环境使用内存模式
```

## 扩展开发

### 添加新工具

1. 在 `ai/agent/tools.py` 中创建新工具类：

```python
class MyNewTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_new_tool"
    
    @property
    def description(self) -> str:
        return "工具描述"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # 实现工具逻辑
        return {"success": True, ...}
```

1. 在 `create_default_registry` 中注册工具

### 添加新LLM提供商

1. 在 `ai/llm/` 目录创建新的提供商类
2. 继承 `BaseLLM` 并实现必需方法
3. 在 `ai/llm/factory.py` 中注册

## 注意事项

1. **Token限制** - 注意LLM的上下文长度限制
2. **工具调用安全** - Agent工具直接操作文档，需确保权限验证
3. **流式响应** - 前端需正确处理SSE事件流
4. **RAG质量** - 知识库文档质量直接影响检索效果
