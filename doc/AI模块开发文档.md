# AI 模块开发文档

## 概述

行云智能文档工作站的AI模块提供统一的智能文档处理能力：

- **统一问答接口** - 单一入口，自动处理RAG和文档操作
- **知识库管理** - 基于Qdrant的项目级知识库
- **Agent文件操作** - AI可返回可执行的文档操作指令

## 核心设计

### 1. 统一响应格式 (POJO)

AI的所有响应都遵循统一的格式，包含两个核心部分：

```json
{
    "message": "AI对用户的说明和解释",
    "operations": [
        {
            "operation_type": "generate_outline",
            "target_file": "文档ID",
            "content": "具体的操作内容",
            "position": {"start": 0, "end": 100},
            "metadata": {}
        }
    ],
    "sources": [...],
    "session_id": "会话ID",
    "tokens_used": 100,
    "requires_confirmation": true
}
```

- **message**: AI的回复说明，向用户解释做了什么
- **operations**: 文件操作列表，前端可据此执行文档修改

### 2. 操作类型

| 操作类型             | 说明           | 使用场景             |
| -------------------- | -------------- | -------------------- |
| `none`             | 无操作，仅回复 | 普通问答             |
| `generate_outline` | 生成大纲       | 用户请求生成文档结构 |
| `expand_content`   | 扩写内容       | 扩展选中或全部内容   |
| `summarize`        | 生成摘要       | 总结文档内容         |
| `style_transfer`   | 风格迁移       | 改变文档风格         |
| `grammar_check`    | 语法检查       | 检查并修正语法       |
| `insert_text`      | 插入文本       | 在指定位置插入       |
| `replace_text`     | 替换文本       | 替换选中内容         |

## 目录结构

```
backend/ai/
├── __init__.py              # 模块导出
├── schema.py                # 统一数据结构定义(POJO)
├── llm/                     # 大语言模型层
│   ├── base.py              # 基类和接口
│   ├── zhipu.py             # 智谱AI实现
│   ├── gemini.py            # Google Gemini实现
│   └── factory.py           # LLM工厂
├── rag/                     # RAG & 知识库
│   ├── chunker.py           # 文本分块器
│   ├── embedding.py         # 向量嵌入服务
│   ├── qdrant_store.py      # Qdrant向量存储
│   ├── knowledge_base.py    # 知识库服务
│   └── ai_service.py        # AI核心服务
└── prompts/                 # 提示工程
    ├── template.py          # 提示模板
    ├── context.py           # 对话上下文
    └── ...
```

## API 接口

### 1. 统一问答接口（推荐）

```
POST /api/ai/chat
```

**这是AI模块的唯一入口**，自动处理：

- 普通问答（Simple模式）
- Agent智能操作（Agent模式）
- RAG检索增强（如果项目有知识库）

#### 请求参数

| 参数                 | 类型    | 必需 | 说明                                 |
| -------------------- | ------- | ---- | ------------------------------------ |
| `message`          | string  | ✅   | 用户输入的问题或指令                 |
| `project_id`       | int     | ✅   | 项目ID（用于RAG检索）                |
| `mode`             | string  | ❌   | 模式：`simple`（默认）或 `agent` |
| `document_content` | string  | ❌   | 当前文档内容                         |
| `document_id`      | string  | ❌   | 文档ID                               |
| `selected_text`    | string  | ❌   | 选中的文本                           |
| `session_id`       | string  | ❌   | 会话ID（用于多轮对话）               |
| `stream`           | boolean | ❌   | 是否流式返回（暂不支持）             |

**请求体示例：**

```json
{
    "message": "请帮我生成一个Python入门教程的大纲",
    "project_id": 1,
    "mode": "agent",
    "document_content": "# 文档标题\n\n",
    "document_id": "doc_001",
    "session_id": "session_123"
}
```

#### 响应格式（Simple模式 - 普通问答）

```json
{
    "code": 200,
    "data": {
        "message": "人工智能是计算机科学的一个分支，致力于创建能够模拟人类智能行为的系统...",
        "operations": [],
        "sources": [
            {
                "content": "相关知识库内容片段...",
                "metadata": {
                    "resource_name": "AI基础.pdf",
                    "page": 3
                },
                "score": 0.85
            }
        ],
        "session_id": "session_123",
        "tokens_used": 150,
        "requires_confirmation": false
    }
}
```

**Simple模式特点**：

- ✅ 直接返回AI回复
- ✅ 自动使用RAG（如果有知识库）
- ✅ 无工具调用，响应速度快
- ✅ 适合普通问答、知识查询

#### 响应格式（Agent模式 - 智能操作）

```json
{
    "code": 200,
    "data": {
        "message": "我已为您生成了Python入门教程的大纲，包含6个主要章节，涵盖基础语法、数据结构、面向对象等核心内容。",
        "operations": [
            {
                "operation_type": "generate_outline",
                "content": "# Python入门教程\n\n## 1. Python简介\n### 1.1 什么是Python\n### 1.2 Python的优势\n\n## 2. 环境搭建\n...",
                "target_file": "doc_001",
                "metadata": {
                    "tool": "generate_outline",
                    "confidence": 0.95
                }
            }
        ],
        "sources": [],
        "session_id": "session_123",
        "tokens_used": 450,
        "requires_confirmation": true,
        "agent_info": {
            "iterations": 2,
            "tools_used": ["generate_outline"],
            "success": true
        }
    }
}
```

**Agent模式特点**：

- ✅ 可执行文档操作（读取、编辑、搜索等）
- ✅ 多轮推理，完成复杂任务
- ✅ 返回可执行的操作指令
- ✅ 适合文档编辑、内容生成、批量处理

### 2. Agent工具系统

Agent模式下，AI可以调用以下7个工具完成文档操作。本节详细说明每个工具的输入输出格式及前端处理方式。

#### 2.1 工具概览

| 工具名称             | 功能分类 | 功能描述                       | 是否修改文档 |
| -------------------- | -------- | ------------------------------ | ------------ |
| `read_document`    | 读写     | 读取文档完整内容               | 否           |
| `write_document`   | 读写     | 完全覆盖文档内容               | 是           |
| `edit_document`    | 读写     | 精确编辑文档（插入/替换/删除） | 是           |
| `search_document`  | 读写     | 搜索文档关键词                 | 否           |
| `generate_outline` | 生成     | 生成文档大纲                   | 是（建议）   |
| `expand_content`   | 生成     | 扩写指定内容                   | 是（建议）   |
| `summarize`        | 生成     | 总结文档或段落                 | 否（仅返回） |

#### 2.2 工具详细规范

##### 2.2.1 read_document - 读取文档

**后端调用（Agent内部）**：

```python
result = read_document(document_id="doc_001")
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "read_document",
  "data": {
    "success": true,
    "content": "文档的完整文本内容...",
    "length": 1234,
    "document_id": "doc_001"
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'read_document') {
    // 通常不需要特殊处理，这是Agent内部用于分析的
    // 前端只需展示AI的回复即可
    console.log('AI正在分析文档内容...');
}
```

##### 2.2.2 search_document - 搜索文档

**后端调用**：

```python
result = search_document(document_id="doc_001", query="第二章")
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "search_document",
  "data": {
    "success": true,
    "query": "第二章",
    "matches": 2,
    "results": [
      {
        "position": 100,
        "context": "...第二章 系统架构...",
        "score": 0.95
      },
      {
        "position": 500,
        "context": "...参考第二章的内容...",
        "score": 0.78
      }
    ]
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'search_document') {
    // 可选：高亮显示搜索结果位置
    const results = response.data.results;
    results.forEach(match => {
        highlightPosition(match.position, match.context);
    });
}
```

##### 2.2.3 write_document - 完全覆盖文档

**后端调用**：

```python
result = write_document(
    document_id="doc_001",
    content="新的完整文档内容"
)
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "replace_text",
  "data": {
    "success": true,
    "action": "write",
    "new_content": "新的完整文档内容",
    "old_length": 1234,
    "new_length": 5678
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'replace_text' && 
    response.data.action === 'write') {
    // 完全替换编辑器内容
    editor.setValue(response.data.new_content);
  
    // 显示提示
    showNotification('文档已完全重写', 'success');
}
```

##### 2.2.4 edit_document - 精确编辑文档

**后端调用（支持3种操作）**：

```python
# 1. 插入内容
result = edit_document(
    document_id="doc_001",
    action="insert",
    position=100,
    content="要插入的内容"
)

# 2. 替换内容
result = edit_document(
    document_id="doc_001",
    action="replace",
    start_position=100,
    end_position=200,
    content="替换后的内容"
)

# 3. 删除内容
result = edit_document(
    document_id="doc_001",
    action="delete",
    start_position=100,
    end_position=200
)
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "replace_text",
  "data": {
    "success": true,
    "action": "insert",
    "position": 100,
    "start_position": 100,
    "end_position": 200,
    "content": "新内容",
    "affected_length": 50
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'replace_text') {
    const { action, position, start_position, end_position, content } = response.data;
  
    switch (action) {
        case 'insert':
            // 在指定位置插入内容
            editor.replaceRange(content, editor.posFromIndex(position));
            break;
        
        case 'replace':
            // 替换指定范围的内容
            const from = editor.posFromIndex(start_position);
            const to = editor.posFromIndex(end_position);
            editor.replaceRange(content, from, to);
            break;
        
        case 'delete':
            // 删除指定范围的内容
            const delFrom = editor.posFromIndex(start_position);
            const delTo = editor.posFromIndex(end_position);
            editor.replaceRange('', delFrom, delTo);
            break;
    }
  
    const actionNames = {
        insert: '插入',
        replace: '替换',
        delete: '删除'
    };
    showNotification(`已${actionNames[action]}内容`, 'success');
}
```

##### 2.2.5 generate_outline - 生成大纲

**后端调用**：

```python
result = generate_outline(
    topic="AI应用开发指南",
    detail_level="medium"  # low/medium/high
)
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "generate_outline",
  "data": {
    "success": true,
    "topic": "AI应用开发指南",
    "outline": "# AI应用开发指南\n\n## 1. 基础概念\n### 1.1 什么是AI\n### 1.2 应用场景\n\n## 2. 技术选型\n...",
    "structure": [
      {
        "level": 1,
        "title": "基础概念",
        "children": [
          {"level": 2, "title": "什么是AI"},
          {"level": 2, "title": "应用场景"}
        ]
      }
    ]
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'generate_outline') {
    const { outline } = response.data;
  
    // 询问用户是否应用大纲
    const confirmed = await showConfirmDialog(
        '生成的大纲',
        outline,
        '应用到文档'
    );
  
    if (confirmed) {
        // 插入到编辑器
        editor.setValue(outline);
        showNotification('大纲已应用', 'success');
    } else {
        // 显示在侧边预览
        showPreview(outline);
    }
}
```

##### 2.2.6 expand_content - 扩写内容

**后端调用**：

```python
result = expand_content(
    content="简短的内容",
    target_length=500,  # 目标字数
    style="professional"  # 风格: casual/professional/academic
)
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "expand_content",
  "data": {
    "success": true,
    "original_content": "简短的内容",
    "expanded_content": "扩写后的详细内容...（约500字）",
    "original_length": 50,
    "expanded_length": 487,
    "expansion_ratio": 9.74
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'expand_content') {
    const { original_content, expanded_content } = response.data;
  
    // 如果用户选中了文本，替换选中部分
    if (editor.somethingSelected()) {
        const selection = editor.getSelection();
        if (selection === original_content.trim()) {
            editor.replaceSelection(expanded_content);
            showNotification('内容已扩写', 'success');
        }
    } else {
        // 否则在光标位置插入
        editor.replaceSelection(expanded_content);
    }
}
```

##### 2.2.7 summarize - 生成摘要

**后端调用**：

```python
result = summarize(
    content="长文本内容...",
    max_length=200,  # 摘要最大字数
    format="paragraph"  # paragraph/bullet_points
)
```

**返回给前端的数据结构**：

```json
{
  "type": "tool_result",
  "operation_type": "summarize",
  "data": {
    "success": true,
    "original_content": "长文本内容...",
    "summary": "摘要内容...",
    "original_length": 2000,
    "summary_length": 180,
    "compression_ratio": 11.11,
    "key_points": [
      "要点1",
      "要点2",
      "要点3"
    ]
  }
}
```

**前端处理方式**：

```javascript
if (response.operation_type === 'summarize') {
    const { summary, key_points } = response.data;
  
    // 显示在侧边栏或弹窗中
    showSummaryPanel({
        summary: summary,
        keyPoints: key_points,
        actions: [
            {
                label: '插入到文档',
                onClick: () => editor.replaceSelection(summary)
            },
            {
                label: '复制摘要',
                onClick: () => copyToClipboard(summary)
            }
        ]
    });
}
```

#### 2.3 统一前端处理流程

```javascript
// 处理AI响应的统一流程
function handleAIResponse(response) {
    // 1. 始终显示AI的文字回复
    if (response.reply) {
        appendChatMessage('assistant', response.reply);
    }
  
    // 2. 如果有操作结果，根据类型处理
    if (response.operation_type) {
        switch (response.operation_type) {
            case 'replace_text':
                handleReplaceText(response.data);
                break;
            case 'generate_outline':
                handleGenerateOutline(response.data);
                break;
            case 'expand_content':
                handleExpandContent(response.data);
                break;
            case 'summarize':
                handleSummarize(response.data);
                break;
            case 'read_document':
            case 'search_document':
                // 通常不需要前端处理，这些是Agent内部使用
                console.log('Agent工具调用:', response.operation_type);
                break;
        }
    }
}
```

#### 2.4 错误处理

所有工具失败时的统一错误格式：

```json
{
  "type": "tool_result",
  "operation_type": "...",
  "data": {
    "success": false,
    "error": "错误原因描述",
    "error_code": "DOCUMENT_NOT_FOUND",
    "details": {
      "document_id": "doc_001"
    }
  }
}
```

**前端错误处理**：

```javascript
if (!response.data.success) {
    showErrorNotification(
        `操作失败: ${response.data.error}`,
        response.data.error_code
    );
    return;
}
```

**常见错误代码**：

- `DOCUMENT_NOT_FOUND`: 文档不存在
- `INVALID_POSITION`: 位置参数无效
- `CONTENT_TOO_LONG`: 内容超出限制
- `AI_SERVICE_ERROR`: AI服务异常

### 3. 模式选择建议

| 场景     | 推荐模式 | 理由                 |
| -------- | -------- | -------------------- |
| 普通问答 | Simple   | 响应快，够用         |
| 知识查询 | Simple   | RAG检索效果好        |
| 生成大纲 | Agent    | 需要工具支持         |
| 扩写内容 | Agent    | 需要读取和编辑       |
| 批量修改 | Agent    | 需要搜索和多次操作   |
| 文档重构 | Agent    | 需要复杂的多步骤操作 |

**前端自动选择策略**：

```javascript
function determineMode(userInput, hasDocument) {
    const agentKeywords = ['生成大纲', '扩写', '修改', '替换', '插入', '重写'];
  
    if (!hasDocument) {
        return 'simple';  // 无文档时只能问答
    }
  
    for (const keyword of agentKeywords) {
        if (userInput.includes(keyword)) {
            return 'agent';
        }
    }
  
    return 'simple';  // 默认普通问答
}
```

### 4. 知识库（RAG）- 自动集成

**重要说明**：知识库的索引和删除已自动集成到资源模块中，**无需单独调用API**。

#### 自动索引规则

当通过资源模块上传文件时，系统会自动将以下类型的文件索引到知识库：

| 文件类型  | 扩展名        | 自动索引    |
| --------- | ------------- | ----------- |
| 纯文本    | `.txt`      | ✅ 自动     |
| Markdown  | `.md`       | ✅ 自动     |
| PDF文档   | `.pdf`      | ✅ 自动     |
| Word文档  | `.docx`     | ✅ 自动     |
| Excel表格 | `.xlsx`     | ❌ 暂不支持 |
| 图片      | `.png/.jpg` | ❌ 不支持   |

#### 自动删除规则

当通过资源模块删除文件时，系统会自动从知识库中移除对应的向量数据。

#### 资源状态字段

资源模型中的 `parsing_status` 字段反映索引状态：

| 状态          | 说明                           |
| ------------- | ------------------------------ |
| `pending`   | 等待处理（不可索引的文件类型） |
| `completed` | 索引成功                       |
| `failed`    | 索引失败                       |

#### 知识库使用流程

```javascript
// 前端只需调用资源上传API，知识库索引自动完成
async function uploadAndIndex(file, projectId) {
    const formData = new FormData();
    formData.append('file', file);
  
    const response = await fetch(`/api/projects/${projectId}/resources`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
  
    const result = await response.json();
  
    // 检查索引状态
    if (result.resource.parsing_status === 'completed') {
        console.log('文件已上传并索引到知识库');
    } else if (result.resource.parsing_status === 'failed') {
        console.log('文件上传成功，但索引失败');
    } else {
        console.log('文件上传成功（不可索引的类型）');
    }
  
    // 之后的AI问答会自动使用RAG检索
    const chatResponse = await fetch('/api/ai/chat', {
        method: 'POST',
        body: JSON.stringify({
            message: "根据文档内容回答问题",
            project_id: projectId,
            mode: 'simple'
        })
    });
}
```

#### 调试接口（可选）

虽然知识库已自动集成，但提供了以下调试接口用于开发测试：

**1. 查看知识库状态**

```
GET /api/ai/knowledge-base/<project_id>/info
```

返回项目知识库的索引状态：

```json
{
    "code": 200,
    "data": {
        "project_id": 1,
        "collection_name": "project_1_kb",
        "vector_count": 120,
        "indexed_resources": [1, 2, 5, 8]
    }
}
```

**2. 手动测试检索**

```
POST /api/ai/knowledge-base/<project_id>/search
```

请求体：

```json
{
    "query": "Python编程",
    "top_k": 5
}
```

返回匹配的向量数据，用于验证索引是否正确。

**注意**：这些接口仅用于调试，正常使用时不需要调用。

### 5. 会话管理（可选）

#### 获取会话历史

```
GET /api/ai/chat/history?session_id=xxx
```

**响应示例：**

```json
{
    "code": 200,
    "data": {
        "session_id": "session_123",
        "messages": [
            {
                "role": "user",
                "content": "Python是什么？",
                "timestamp": "2026-01-20T10:00:00Z"
            },
            {
                "role": "assistant",
                "content": "Python是一门高级编程语言...",
                "timestamp": "2026-01-20T10:00:02Z"
            }
        ]
    }
}
```

#### 删除会话

```
DELETE /api/ai/chat/sessions/<session_id>
```

**响应示例：**

```json
{
    "code": 200,
    "message": "会话已删除"
}
```

## 工作流程

### 1. Simple模式 - 普通问答流程

```
用户输入 
  ↓
检查项目是否有知识库
  ↓
有知识库: 使用RAG检索相关内容
  ↓
构建提示词(系统提示 + RAG上下文 + 用户输入)
  ↓
调用LLM生成回复
  ↓
返回 { message, sources }
```

**代码示例（后端）**：

```python
from ai import get_ai_service

ai_service = get_ai_service()

response = ai_service.chat(AIRequest(
    message="Python有哪些特点？",
    project_id=1,
    mode="simple"
))

# response.message: "Python具有以下特点：1. 语法简洁..."
# response.sources: [{"content": "...", "score": 0.85}]
```

**前端集成**：

```javascript
async function simpleChat(message, projectId) {
    const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            project_id: projectId,
            mode: 'simple'
        })
    });
  
    const result = await response.json();
  
    if (result.code === 200) {
        // 显示AI回复
        displayMessage(result.data.message);
  
        // 显示知识库来源（如果有）
        if (result.data.sources.length > 0) {
            displaySources(result.data.sources);
        }
    }
}
```

### 2. Agent模式 - 智能操作流程

```
用户输入 + 文档内容
  ↓
创建Agent处理器
  ↓
Agent循环开始
  ├─ 调用LLM（带工具定义）
  ├─ 检查finish_reason
  ├─ 如果是"tool_calls": 执行工具 → 继续循环
  └─ 如果是"stop": 返回结果
  ↓
解析工具执行结果
  ↓
返回 { message, operations, agent_info }
  ↓
前端确认操作
  ↓
执行文档修改
```

**Agent循环示例**：

```
轮次1: LLM决策
  用户: "请帮我生成Python教程大纲"
  LLM: "我需要先看看文档内容" → tool_calls: [read_document]

轮次2: 工具执行 + LLM继续
  工具结果: {"content": "# 标题\n\n", "length": 10}
  LLM: "好的，我来生成大纲" → tool_calls: [generate_outline]

轮次3: 最终响应
  工具结果: 大纲生成完成
  LLM: "我已为您生成包含6个章节的大纲..." → finish_reason: stop
```

**代码示例（后端）**：

```python
response = ai_service.chat(AIRequest(
    message="请帮我扩写第二章的内容",
    project_id=1,
    document_content="# Python教程\n\n## 第二章 数据类型\n\n简介",
    document_id="doc_001",
    mode="agent"
))

# response.message: "我已为您扩写了第二章的内容，增加了..."
# response.operations: [
#     {
#         "operation_type": "replace_text",
#         "content": "扩写后的完整内容...",
#         "target_file": "doc_001"
#     }
# ]
# response.agent_info: {
#     "iterations": 3,
#     "tools_used": ["read_document", "edit_document"],
#     "success": True
# }
```

**前端集成（完整流程）**：

```javascript
async function agentChat(message, documentContent, documentId) {
    // 1. 发送请求
    const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            project_id: currentProjectId,
            mode: 'agent',
            document_content: documentContent,
            document_id: documentId
        })
    });
  
    const result = await response.json();
  
    if (result.code !== 200) {
        showError(result.message);
        return;
    }
  
    const { message: aiMessage, operations, requires_confirmation, agent_info } = result.data;
  
    // 2. 显示AI说明
    displayMessage(aiMessage);
  
    // 3. 显示Agent执行信息（可选）
    if (agent_info) {
        console.log(`Agent执行: ${agent_info.iterations}轮迭代, 使用工具: ${agent_info.tools_used.join(', ')}`);
    }
  
    // 4. 处理文档操作
    if (operations.length > 0) {
        if (requires_confirmation) {
            // 显示操作预览和确认对话框
            showOperationConfirmDialog(operations, aiMessage, (confirmed) => {
                if (confirmed) {
                    applyOperations(operations);
                }
            });
        } else {
            // 直接应用操作
            applyOperations(operations);
        }
    }
}

// 应用操作到编辑器
function applyOperations(operations) {
    for (const op of operations) {
        switch (op.operation_type) {
            case 'generate_outline':
            case 'expand_content':
            case 'summarize':
                // 替换整个文档内容
                editor.setContent(op.content);
                showSuccess('内容已更新');
                break;
        
            case 'replace_text':
                if (op.position) {
                    // 替换指定位置
                    editor.replaceRange(
                        op.position.start,
                        op.position.end,
                        op.content
                    );
                } else {
                    // 替换选中内容或全部
                    editor.replaceSelection(op.content);
                }
                break;
        
            case 'insert_text':
                editor.insertAt(op.position.start, op.content);
                break;
        }
    }
  
    // 标记文档已修改
    markDocumentModified();
}
```

### 3. RAG增强流程（自动）

RAG会在以下情况自动启用：

- ✅ 项目已创建知识库
- ✅ 知识库中有索引的资源
- ✅ 用户问题与知识库内容相关

```
用户提问: "这个项目用了什么技术栈？"
  ↓
知识库检索: 在项目的所有文档中搜索
  ↓
找到相关片段:
  - "使用Vue 3 + Vite构建前端" (相似度: 0.87)
  - "后端采用Flask框架" (相似度: 0.82)
  ↓
构建增强提示词:
  """
  根据以下知识库内容回答问题：
  [片段1] 使用Vue 3 + Vite构建前端
  [片段2] 后端采用Flask框架
  
  用户问题：这个项目用了什么技术栈？
  """
  ↓
LLM回复: "根据项目文档，技术栈包括：前端使用Vue 3 + Vite，后端使用Flask框架..."
  ↓
返回响应时附带sources（来源）
```

**知识库使用示例**：

```javascript
// 1. 用户上传文档后自动索引
async function handleFileUpload(file, projectId) {
    // 上传文件
    const uploadRes = await uploadFile(file, projectId);
  
    // 自动索引到知识库
    await fetch(`/api/ai/knowledge-base/${projectId}/index`, {
        method: 'POST',
        body: JSON.stringify({ resource_id: uploadRes.data.id })
    });
  
    showSuccess('文件已上传并索引到知识库');
}

// 2. 之后的问答会自动使用RAG
async function askQuestion(question) {
    const response = await fetch('/api/ai/chat', {
        method: 'POST',
        body: JSON.stringify({
            message: question,
            project_id: currentProjectId,
            mode: 'simple'  // RAG在Simple和Agent模式下都会自动启用
        })
    });
  
    const result = await response.json();
  
    // 显示回复和来源
    displayMessage(result.data.message);
  
    if (result.data.sources.length > 0) {
        displaySourceReferences(result.data.sources);
    }
}

// 3. 显示知识库来源（增强用户信任）
function displaySourceReferences(sources) {
    const sourcesList = sources.map(source => `
        <div class="source-item">
            <div class="source-name">${source.metadata.resource_name}</div>
            <div class="source-content">${source.content.substring(0, 100)}...</div>
            <div class="source-score">相关度: ${(source.score * 100).toFixed(0)}%</div>
        </div>
    `).join('');
  
    document.getElementById('sources-panel').innerHTML = sourcesList;
}
```

## 配置说明

### 环境变量

```bash
# AI提供商
ZHIPU_API_KEY=your-key
GEMINI_API_KEY=your-key
DEFAULT_AI_PROVIDER=zhipu

# Embedding（默认使用本地BGE模型）
EMBEDDING_PROVIDER=local                    # 'local', 'zhipu' 或 'gemini'
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5     # 本地模型名称
EMBEDDING_DEVICE=cpu                        # 'cpu', 'cuda', 'mps' 或 None(自动)
EMBEDDING_CACHE_FOLDER=./models             # 模型缓存目录（可选）

# 如需使用云端Embedding（可选）
# EMBEDDING_PROVIDER=zhipu
# ZHIPU_API_KEY=your-key

# Qdrant向量数据库
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_USE_MEMORY=true  # 开发环境使用内存模式

# RAG配置
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=5
```

### 本地 Embedding 模型优势

项目默认使用 **BAAI/bge-small-zh-v1.5** 本地嵌入模型：

- ✅ **免费开源** - 无需 API 密钥，无调用次数限制
- ✅ **隐私保护** - 数据不出本地
- ✅ **低成本** - 无云端调用费用
- ✅ **高性能** - 在中文文本检索任务上表现优异

支持的本地模型：

| 模型                   | 维度 | 大小   | 推荐场景              |
| ---------------------- | ---- | ------ | --------------------- |
| BAAI/bge-small-zh-v1.5 | 512  | ~95MB  | 开发/轻量应用（默认） |
| BAAI/bge-base-zh-v1.5  | 768  | ~400MB | 生产环境              |
| BAAI/bge-large-zh-v1.5 | 1024 | ~1.3GB | 高精度要求            |
| moka-ai/m3e-base       | 768  | ~400MB | 备选方案              |

## Qdrant部署

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v /data/qdrant:/qdrant/storage \
  qdrant/qdrant:latest
```

然后配置：

```bash
QDRANT_USE_MEMORY=false
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## 前端集成指南

### 1. 发送消息

```javascript
const response = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: userInput,
        project_id: currentProjectId,
        document_content: editor.getContent(),
        document_id: currentDocId,
        selected_text: editor.getSelectedText()
    })
});

const result = await response.json();
```

### 2. 处理响应

```javascript
if (result.code === 200) {
    const { message, operations, sources, requires_confirmation } = result.data;
  
    // 显示AI回复
    displayMessage(message);
  
    // 显示来源（如果有RAG）
    if (sources.length > 0) {
        displaySources(sources);
    }
  
    // 处理文档操作
    if (operations.length > 0 && requires_confirmation) {
        // 显示确认对话框
        showOperationConfirmation(operations, () => {
            applyOperations(operations);
        });
    }
}
```

### 3. 执行文档操作

```javascript
function applyOperations(operations) {
    for (const op of operations) {
        switch (op.operation_type) {
            case 'generate_outline':
            case 'expand_content':
            case 'summarize':
                // 替换或插入内容
                editor.setContent(op.content);
                break;
            case 'replace_text':
                editor.replaceSelection(op.content);
                break;
            case 'insert_text':
                editor.insertAt(op.position, op.content);
                break;
        }
    }
}
```

## 依赖安装

```bash
pip install -r requirements.txt
```

主要AI依赖：

- `httpx` - HTTP客户端（用于云端LLM API）
- `qdrant-client` - Qdrant向量数据库
- `sentence-transformers` - 本地嵌入模型（BGE）
- `torch` - PyTorch深度学习框架
- `PyPDF2` - PDF解析（可选）
- `python-docx` - Word文档解析（可选）

### GPU 加速（可选）

如果有 NVIDIA GPU，可以安装 CUDA 版本的 PyTorch 加速嵌入：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

然后配置：

```bash
EMBEDDING_DEVICE=cuda
```

Mac M 系列芯片可使用 MPS 加速：

```bash
EMBEDDING_DEVICE=mps
```

### 首次运行说明

首次启动时，系统会自动下载 BGE 模型（约95MB），请确保网络连接正常。模型会缓存到本地，后续使用无需重复下载。

国内用户可以配置镜像加速：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

## 测试

### Agent工具测试

运行Agent工具测试套件：

```bash
cd backend
venv\Scripts\python.exe test_agent_tools_comprehensive.py
```

测试报告: `backend/AGENT_TOOLS_TEST_REPORT.md`

### RAG模块测试

运行RAG模块测试：

```bash
cd backend
venv\Scripts\python.exe test_rag_simple.py
```

测试报告: `backend/RAG_TEST_REPORT.md`

### 测试覆盖范围

| 模块            | 测试文件                          | 通过率       |
| --------------- | --------------------------------- | ------------ |
| Agent工具 (7个) | test_agent_tools_comprehensive.py | 100% (10/10) |
| RAG组件 (4个)   | test_rag_simple.py                | 100% (4/4)   |

### 离线模式测试

如果网络不稳定，可以设置离线模式使用缓存的模型：

```bash
set TRANSFORMERS_OFFLINE=1
set HF_HUB_OFFLINE=1
python test_rag_simple.py
```
