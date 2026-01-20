# 已完成 API 开发表

本文档记录了后端已实现的所有 API 接口。

---

## 认证模块 (`/api/auth`)

| 方法 | 路径                   | 功能     | 认证 | 请求参数                                     | 响应                       |
| ---- | ---------------------- | -------- | ---- | -------------------------------------------- | -------------------------- |
| POST | `/api/auth/register` | 用户注册 | 否   | `username`, `email`, `password` (JSON) | `user`, `access_token` |
| POST | `/api/auth/login`    | 用户登录 | 否   | `username`, `password` (JSON)            | `user`, `access_token` |

### 详细说明

#### 1. 用户注册 `POST /api/auth/register`

**请求体：**

```json
{
    "username": "string (2-64字符)",
    "email": "string",
    "password": "string (至少6字符)"
}
```

**成功响应 (201)：**

```json
{
    "message": "注册成功",
    "user": { "id": 1, "username": "...", "email": "..." },
    "access_token": "jwt_token"
}
```

**错误响应：**

- `400` - 参数验证失败
- `409` - 用户名或邮箱已存在

---

#### 2. 用户登录 `POST /api/auth/login`

**请求体：**

```json
{
    "username": "string (用户名或邮箱)",
    "password": "string"
}
```

**成功响应 (200)：**

```json
{
    "message": "登录成功",
    "user": { "id": 1, "username": "...", "email": "..." },
    "access_token": "jwt_token"
}
```

**错误响应：**

- `400` - 参数为空
- `401` - 用户名或密码错误

---

## 用户模块 (`/api/user`)

| 方法 | 路径                          | 功能             | 认证 | 请求参数                                               | 响应                   |
| ---- | ----------------------------- | ---------------- | ---- | ------------------------------------------------------ | ---------------------- |
| GET  | `/api/user/me`              | 获取当前用户信息 | JWT  | -                                                      | `user`               |
| PUT  | `/api/user/profile`         | 更新用户资料     | JWT  | `username`, `description`, `avatar` (JSON, 可选) | `user`               |
| POST | `/api/user/change-password` | 修改密码         | JWT  | `oldPassword`, `newPassword` (JSON)                | `message`            |
| POST | `/api/user/verify-password` | 验证当前密码     | JWT  | `password` (JSON)                                    | `valid`, `message` |
| POST | `/api/user/avatar`          | 上传头像         | JWT  | `avatar` (FormData)                                  | `user`               |

### 详细说明

#### 1. 获取当前用户 `GET /api/user/me`

**请求头：**

```
Authorization: Bearer <access_token>
```

**成功响应 (200)：**

```json
{
    "user": {
        "id": 1,
        "username": "...",
        "email": "...",
        "avatar": "...",
        "description": "...",
        "last_login": "ISO datetime",
        "created_at": "ISO datetime"
    }
}
```

---

#### 2. 更新用户资料 `PUT /api/user/profile`

**请求头：**

```
Authorization: Bearer <access_token>
```

**请求体：**

```json
{
    "username": "string (可选)",
    "description": "string (可选)",
    "avatar": "string (可选)"
}
```

**成功响应 (200)：**

```json
{
    "message": "更新成功",
    "user": { ... }
}
```

**错误响应：**

- `400` - 参数验证失败
- `409` - 用户名已被使用

---

#### 3. 修改密码 `POST /api/user/change-password`

**请求头：**

```
Authorization: Bearer <access_token>
```

**请求体：**

```json
{
    "oldPassword": "string",
    "newPassword": "string (至少6字符)"
}
```

**成功响应 (200)：**

```json
{
    "message": "密码修改成功"
}
```

**错误响应：**

- `400` - 参数为空或新密码过短
- `401` - 原密码错误

---

#### 4. 验证密码 `POST /api/user/verify-password`

**请求头：**

```
Authorization: Bearer <access_token>
```

**请求体：**

```json
{
    "password": "string"
}
```

**成功响应 (200)：**

```json
{
    "valid": true,
    "message": "密码正确"
}
```

---

#### 5. 上传头像 `POST /api/user/avatar`

**请求头：**

```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**请求体：** `multipart/form-data`

- `avatar`: 图片文件 (PNG, JPG, JPEG, GIF, WebP)

**成功响应 (200)：**

```json
{
    "message": "头像上传成功",
    "user": { ... }
}
```

**错误响应：**

- `400` - 没有上传文件 / 不支持的文件类型

---

## 项目模块 (`/api/projects`)

| 方法   | 路径                   | 功能              | 认证 | 请求参数                                           | 响应                     |
| ------ | ---------------------- | ----------------- | ---- | -------------------------------------------------- | ------------------------ |
| GET    | `/api/projects`      | 获取用户所有项目  | JWT  | `include_deleted` (Query, 可选)                  | `projects`, `total`  |
| POST   | `/api/projects`      | 创建新项目        | JWT  | `name`, `description` (JSON)                   | `project`              |
| GET    | `/api/projects/<id>` | 获取单个项目详情  | JWT  | `include_resources` (Query, 可选)                | `project`              |
| PUT    | `/api/projects/<id>` | 更新项目          | JWT  | `name`, `description`, `status` (JSON, 可选) | `project`              |
| DELETE | `/api/projects/<id>` | 删除项目 (软删除) | JWT  | -                                                  | `message`, `project` |

### 详细说明

#### 1. 获取用户所有项目 `GET /api/projects`

**查询参数：**

- `include_deleted` (可选): `true`/`false`，是否包含已删除项目，默认 `false`

**成功响应 (200)：**

```json
{
    "projects": [
        {
            "id": 1,
            "name": "项目名称",
            "description": "项目描述",
            "status": "active",
            "created_at": "2026-01-12T10:00:00",
            "updated_at": "2026-01-12T10:00:00"
        }
    ],
    "total": 1
}
```

---

#### 2. 创建新项目 `POST /api/projects`

**请求体：**

```json
{
    "name": "string (必填, 最大128字符)",
    "description": "string (可选)"
}
```

**成功响应 (201)：**

```json
{
    "message": "项目创建成功",
    "project": { ... }
}
```

**错误响应：**

- `400` - 项目名称为空或超长

---

#### 3. 获取单个项目 `GET /api/projects/<id>`

**查询参数：**

- `include_resources` (可选): `true`/`false`，是否包含项目资源列表，默认 `false`

**成功响应 (200)：**

```json
{
    "project": {
        "id": 1,
        "name": "项目名称",
        "description": "项目描述",
        "status": "active",
        "resources": [...],
        "created_at": "2026-01-12T10:00:00",
        "updated_at": "2026-01-12T10:00:00"
    }
}
```

**错误响应：**

- `404` - 项目不存在或无权访问

---

#### 4. 更新项目 `PUT /api/projects/<id>`

**请求体：**

```json
{
    "name": "string (可选)",
    "description": "string (可选)",
    "status": "active | archived (可选)"
}
```

**成功响应 (200)：**

```json
{
    "message": "项目更新成功",
    "project": { ... }
}
```

**错误响应：**

- `400` - 参数验证失败
- `404` - 项目不存在或无权访问

---

#### 5. 删除项目 `DELETE /api/projects/<id>`

执行软删除，项目标记为已删除但不会物理删除。

**成功响应 (200)：**

```json
{
    "message": "项目删除成功",
    "project": { ... }
}
```

**错误响应：**

- `404` - 项目不存在或无权访问

---

## 资源模块 (`/api/projects/<project_id>/resources`)

| 方法   | 路径                                                   | 功能             | 认证 | 请求参数            | 响应                     |
| ------ | ------------------------------------------------------ | ---------------- | ---- | ------------------- | ------------------------ |
| GET    | `/api/projects/<project_id>/resources`               | 获取项目所有资源 | JWT  | -                   | `resources`, `total` |
| POST   | `/api/projects/<project_id>/resources`               | 上传文件资源     | JWT  | `file` (FormData) | `resource`             |
| GET    | `/api/projects/<project_id>/resources/<resource_id>` | 获取单个资源详情 | JWT  | -                   | `resource`             |
| DELETE | `/api/projects/<project_id>/resources/<resource_id>` | 删除资源文件     | JWT  | -                   | `message`              |

### 详细说明

#### 1. 获取项目所有资源 `GET /api/projects/<project_id>/resources`

**成功响应 (200)：**

```json
{
    "resources": [
        {
            "id": 1,
            "filename": "文档.docx",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "file_size": 12345,
            "parsing_status": "pending",
            "uploaded_at": "2026-01-12T10:00:00"
        }
    ],
    "total": 1
}
```

**错误响应：**

- `404` - 项目不存在或无权访问

---

#### 2. 上传文件资源 `POST /api/projects/<project_id>/resources`

**请求体：** `multipart/form-data`

- `file`: 上传的文件

**支持的文件类型：**

- 文档: `.txt`, `.pdf`, `.doc`, `.docx`, `.md`
- 表格: `.xls`, `.xlsx`
- 演示文稿: `.ppt`, `.pptx`
- 图片: `.png`, `.jpg`, `.jpeg`, `.gif`

**成功响应 (201)：**

```json
{
    "message": "文件上传成功",
    "resource": {
        "id": 1,
        "filename": "原始文件名.docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size": 12345,
        "parsing_status": "pending",
        "uploaded_at": "2026-01-12T10:00:00"
    }
}
```

**错误响应：**

- `400` - 没有上传文件 / 不支持的文件类型
- `404` - 项目不存在或无权访问
- `500` - 文件上传失败

---

#### 3. 获取单个资源 `GET /api/projects/<project_id>/resources/<resource_id>`

**成功响应 (200)：**

```json
{
    "resource": {
        "id": 1,
        "filename": "文档.docx",
        "mime_type": "...",
        "file_size": 12345,
        "parsing_status": "pending",
        "uploaded_at": "2026-01-12T10:00:00"
    }
}
```

**错误响应：**

- `404` - 项目或资源不存在

---

#### 4. 删除资源文件 `DELETE /api/projects/<project_id>/resources/<resource_id>`

同时删除数据库记录和物理文件。

**成功响应 (200)：**

```json
{
    "message": "资源删除成功"
}
```

**错误响应：**

- `404` - 项目或资源不存在
- `500` - 删除失败

---

## 通用说明

### 认证方式

需要认证的接口使用 JWT (JSON Web Token) 进行身份验证。

**请求头格式：**

```
Authorization: Bearer <access_token>
```

### 错误响应格式

所有错误响应均采用统一格式：

```json
{
    "error": "错误描述信息"
}
```

### 支持的 MIME 类型

后端自动识别以下文件类型：

| 扩展名         | MIME 类型                                                                     |
| -------------- | ----------------------------------------------------------------------------- |
| `.docx`      | `application/vnd.openxmlformats-officedocument.wordprocessingml.document`   |
| `.xlsx`      | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`         |
| `.pptx`      | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `.doc`       | `application/msword`                                                        |
| `.xls`       | `application/vnd.ms-excel`                                                  |
| `.ppt`       | `application/vnd.ms-powerpoint`                                             |
| `.md`        | `text/markdown`                                                             |
| `.pdf`       | `application/pdf`                                                           |
| `.txt`       | `text/plain`                                                                |
| `.png`       | `image/png`                                                                 |
| `.jpg/.jpeg` | `image/jpeg`                                                                |
| `.gif`       | `image/gif`                                                                 |

---

## API 统计

| 模块           | API 数量     |
| -------------- | ------------ |
| 认证模块       | 2            |
| 用户模块       | 5            |
| 项目模块       | 5            |
| 资源模块       | 4            |
| AI模块         | 3            |
| **总计** | **19** |

---

## AI 模块 (`/api/ai`)

AI模块采用统一接口设计，通过单一问答入口处理所有AI交互，支持RAG增强和Agent工具调用。

**重要说明**：RAG知识库的索引和移除已自动集成到资源上传/删除API中，无需手动调用索引接口。

**完整文档参考**：

- `doc/AI模块开发文档.md` - 完整技术文档（包含架构、API、RAG、Agent工具等）
- `doc/Agent工具前端对接指南.md` - Agent工具的前端对接详细规范（推荐前端开发阅读）

| 方法 | 路径                                           | 功能           | 认证 | 说明                            |
| ---- | ---------------------------------------------- | -------------- | ---- | ------------------------------- |
| POST | `/api/ai/chat`                               | 统一问答接口   | JWT  | 核心接口，支持Simple和Agent模式 |
| GET  | `/api/ai/knowledge-base/<project_id>/info`   | 获取知识库状态 | JWT  | 调试用，查看项目知识库信息      |
| POST | `/api/ai/knowledge-base/<project_id>/search` | 搜索知识库     | JWT  | 调试用，手动测试知识库检索      |

### RAG自动集成说明

资源上传时会自动索引到知识库：

- **触发时机**：上传支持的文件类型（.txt, .md, .pdf, .docx）时自动索引
- **使用接口**：`POST /api/projects/<project_id>/resources`
- **删除时机**：删除资源时自动从知识库移除
- **删除接口**：`DELETE /api/projects/<project_id>/resources/<resource_id>`

### 核心概念

#### AIResponse 统一响应格式

所有AI响应采用统一的POJO格式，包含说明内容和可选的文件操作指令：

```json
{
    "explanation": "AI的说明性回复内容",
    "operations": [
        {
            "type": "CONTENT_EXPAND",
            "target": "section_id 或 null",
            "content": "操作的具体内容",
            "position": "after",
            "metadata": {}
        }
    ],
    "knowledge_used": true,
    "sources": [
        {
            "resource_id": 1,
            "filename": "参考文档.pdf",
            "relevance": 0.85
        }
    ],
    "metadata": {
        "model": "glm-4-flash",
        "tokens_used": 150
    }
}
```

#### 文件操作类型 (OperationType)

| 类型                 | 说明     | 用途                        |
| -------------------- | -------- | --------------------------- |
| `OUTLINE_GENERATE` | 生成大纲 | 为文档生成结构化大纲        |
| `CONTENT_EXPAND`   | 内容扩写 | 扩展指定内容段落            |
| `SUMMARIZE`        | 生成摘要 | 提取内容要点和摘要          |
| `STYLE_TRANSFER`   | 风格迁移 | 转换文本风格（正式/口语等） |
| `GRAMMAR_CHECK`    | 语法检查 | 检查并修正语法错误          |
| `FORMAT_CONVERT`   | 格式转换 | 转换文档格式                |
| `TRANSLATION`      | 翻译     | 多语言翻译                  |
| `CONTENT_INSERT`   | 内容插入 | 在指定位置插入新内容        |
| `CONTENT_REPLACE`  | 内容替换 | 替换指定内容                |
| `CONTENT_DELETE`   | 内容删除 | 删除指定内容                |

### 详细说明

#### 1. 统一问答接口 `POST /api/ai/chat`

核心问答接口，支持普通对话、RAG增强问答、agnet操作。

**请求体：**

```json
{
    "message": "用户消息（必需）",
    "project_id": 1,
    "mode": "simple",
    "document_content": "当前编辑器内容（可选）",
    "document_id": "文档ID（可选）",
    "selected_text": "选中的文本（可选）",
    "session_id": "会话ID（可选，用于多轮对话）",
    "stream": false
}
```

**参数说明：**

- `message`: 用户输入的问题或指令
- `project_id`: 项目ID，用于RAG知识库检索
- `mode`: 模式，`simple`（默认）或 `agent`
  - `simple`: 普通问答模式，适合知识查询
  - `agent`: 智能Agent模式，可使用7种文档工具进行操作
- `document_content`: 当前文档内容，用于上下文理解
- `document_id`: 文档ID
- `selected_text`: 选中的文本
- `session_id`: 会话ID，用于多轮对话
- `stream`: 是否使用流式响应（暂不支持）

**成功响应 (200)：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "message": "AI的回复说明",
        "operations": [
            {
                "operation_type": "expand_content",
                "target_file": "doc_123",
                "content": "扩展后的内容...",
                "position": {"start": 0, "end": 100},
                "metadata": {"ratio": 2.5}
            }
        ],
        "sources": [
            {
                "text": "来源文本片段...",
                "score": 0.85,
                "doc_id": "resource_5",
                "metadata": {"resource_id": 5, "filename": "参考.pdf"}
            }
        ],
        "session_id": "会话ID",
        "tokens_used": 280,
        "requires_confirmation": false
    }
}
```

**操作类型说明：**

| 操作类型             | 说明     | 使用场景       |
| -------------------- | -------- | -------------- |
| `none`             | 无操作   | 普通问答       |
| `generate_outline` | 生成大纲 | 创建文档结构   |
| `expand_content`   | 扩写内容 | 扩展段落       |
| `summarize`        | 生成摘要 | 提炼要点       |
| `style_transfer`   | 风格迁移 | 改变写作风格   |
| `grammar_check`    | 语法检查 | 检查并修正     |
| `insert_text`      | 插入文本 | 在指定位置插入 |
| `replace_text`     | 替换文本 | 替换选中内容   |

**Agent模式可用工具：**

1. `read_document` - 读取文档内容
2. `write_document` - 覆写整个文档
3. `edit_document` - 编辑部分内容
4. `search_document` - 搜索文档
5. `generate_outline` - 生成大纲
6. `expand_content` - 扩写内容
7. `summarize` - 生成摘要

**使用示例：**

普通问答（Simple模式）：

```json
{
    "message": "什么是微服务架构？",
    "project_id": 1,
    "mode": "simple"
}
```

生成大纲（Agent模式）：

```json
{
    "message": "请为这篇文章生成详细大纲",
    "project_id": 1,
    "mode": "agent",
    "document_content": "# 文章标题\n\n文章内容..."
}
```

内容扩写（Agent模式）：

```json
{
    "message": "请扩写这段内容，增加更多细节和例子",
    "project_id": 1,
    "mode": "agent",
    "document_content": "完整文档内容",
    "selected_text": "待扩写的段落"
}
```

---

#### 2. 获取知识库状态 `GET /api/ai/knowledge-base/<project_id>/info`

**说明**：调试接口，查询项目知识库的索引状态。

**成功响应 (200)：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "project_id": 1,
        "collection_name": "project_1_kb",
        "vector_count": 120,
        "indexed_resources": [1, 2, 5, 8]
    }
}
```

---

#### 3. 搜索知识库 `POST /api/ai/knowledge-base/<project_id>/search`

**说明**：调试接口，手动测试知识库检索。正常使用时，检索功能已集成在chat接口中自动执行。

**请求体：**

```json
{
    "query": "搜索内容",
    "top_k": 5
}
```

**成功响应 (200)：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "results": [
            {
                "text": "匹配的文本片段...",
                "score": 0.92,
                "resource_id": 5,
                "metadata": {"filename": "文档.pdf"}
            }
        ]
    }
}
```

---
