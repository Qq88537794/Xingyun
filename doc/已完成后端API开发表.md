# 已完成 API 开发表

本文档记录了后端已实现的所有 API 接口。

---

## 认证模块 (`/api/auth`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 | 响应 |
|------|------|------|------|----------|------|
| POST | `/api/auth/register` | 用户注册 | 否 | `username`, `email`, `password` (JSON) | `user`, `access_token` |
| POST | `/api/auth/login` | 用户登录 | 否 | `username`, `password` (JSON) | `user`, `access_token` |
| GET | `/api/auth/me` | 获取当前用户信息 | JWT | - | `user` |

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

#### 3. 获取当前用户 `GET /api/auth/me`

**请求头：**
```
Authorization: Bearer <access_token>
```

**成功响应 (200)：**
```json
{
    "user": { "id": 1, "username": "...", "email": "..." }
}
```

---

## 项目模块 (`/api/projects`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 | 响应 |
|------|------|------|------|----------|------|
| GET | `/api/projects` | 获取用户所有项目 | JWT | `include_deleted` (Query, 可选) | `projects`, `total` |
| POST | `/api/projects` | 创建新项目 | JWT | `name`, `description` (JSON) | `project` |
| GET | `/api/projects/<id>` | 获取单个项目详情 | JWT | `include_resources` (Query, 可选) | `project` |
| PUT | `/api/projects/<id>` | 更新项目 | JWT | `name`, `description`, `status` (JSON, 可选) | `project` |
| DELETE | `/api/projects/<id>` | 删除项目 (软删除) | JWT | - | `message`, `project` |

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
        "resources": [...],  // 仅当 include_resources=true 时返回
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

| 方法 | 路径 | 功能 | 认证 | 请求参数 | 响应 |
|------|------|------|------|----------|------|
| GET | `/api/projects/<project_id>/resources` | 获取项目所有资源 | JWT | - | `resources`, `total` |
| POST | `/api/projects/<project_id>/resources` | 上传文件资源 | JWT | `file` (FormData) | `resource` |
| GET | `/api/projects/<project_id>/resources/<resource_id>` | 获取单个资源详情 | JWT | - | `resource` |
| DELETE | `/api/projects/<project_id>/resources/<resource_id>` | 删除资源文件 | JWT | - | `message` |

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

| 扩展名 | MIME 类型 |
|--------|----------|
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `.pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `.doc` | `application/msword` |
| `.xls` | `application/vnd.ms-excel` |
| `.ppt` | `application/vnd.ms-powerpoint` |
| `.md` | `text/markdown` |
| `.pdf` | `application/pdf` |
| `.txt` | `text/plain` |
| `.png` | `image/png` |
| `.jpg/.jpeg` | `image/jpeg` |
| `.gif` | `image/gif` |

---

## API 统计

| 模块 | API 数量 |
|------|----------|
| 认证模块 | 3 |
| 项目模块 | 5 |
| 资源模块 | 4 |
| **总计** | **12** |
