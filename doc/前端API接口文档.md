# 行云智能文档工作站 前端 API 接口文档

## 文档说明

本文档详细描述了前端调用的所有后端 API 接口，包括请求方法、参数、响应格式等信息，便于后端开发人员对接。

基础信息

基础 URL: http://localhost:5000/api
认证方式: JWT Bearer Token
内容类型: application/json (文件上传除外)

## 目录

1. 认证模块 (Auth)
2. 项目管理模块 (Projects)
3. 资源管理模块 (Resources)
4. 文件夹管理模块 (Folders)
5. 通用说明

## 认证模块 (Auth)

### 1.1 用户注册

接口地址: POST /api/auth/register

请求头:
Content-Type: application/json

请求参数:
```json
{
  "username": "string",  // 必填，用户名，2-64个字符
  "email": "string",     // 必填，邮箱地址
  "password": "string"   // 必填，密码，至少6个字符
}
```

成功响应: 201 Created
```json
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "avatar": null,
    "settings": null,
    "created_at": "2024-01-01T00:00:00"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

错误响应:

400 Bad Request: 参数验证失败
```json
{
  "error": "用户名、邮箱和密码不能为空"
}
```

409 Conflict: 用户名或邮箱已存在
```json
{
  "error": "用户名已被注册"
}
```

### 1.2 用户登录

接口地址: POST /api/auth/login

请求头:
Content-Type: application/json

请求参数:
```json
{
  "username": "string",  // 必填，用户名或邮箱
  "password": "string"   // 必填，密码
}
```

成功响应: 200 OK
```json
{
  "message": "登录成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "avatar": "/uploads/avatars/1_abc123.jpg",
    "settings": null,
    "created_at": "2024-01-01T00:00:00"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

错误响应:

400 Bad Request: 参数缺失
401 Unauthorized: 用户名或密码错误
```json
{
  "error": "用户名或密码错误"
}
```

### 1.3 获取当前用户信息

接口地址: GET /api/auth/me

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "avatar": "/uploads/avatars/1_abc123.jpg",
    "settings": null,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

错误响应:

401 Unauthorized: Token 无效或过期
404 Not Found: 用户不存在

### 1.4 更新用户资料

接口地址: PUT /api/auth/profile

请求头:
Authorization: Bearer <access_token>
Content-Type: application/json

请求参数:
```json
{
  "username": "string",         // 可选，新用户名，2-64个字符
  "email": "string",            // 可选，新邮箱
  "current_password": "string", // 修改密码时必填，当前密码
  "new_password": "string"      // 可选，新密码，至少6个字符
}
```

成功响应: 200 OK
```json
{
  "message": "个人资料更新成功",
  "user": {
    "id": 1,
    "username": "newusername",
    "email": "newemail@example.com",
    "avatar": "/uploads/avatars/1_abc123.jpg",
    "settings": null,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

错误响应:

400 Bad Request: 参数验证失败
401 Unauthorized: 当前密码错误
409 Conflict: 用户名或邮箱已被使用

### 1.5 验证当前密码

接口地址: POST /api/auth/verify-password

请求头:
Authorization: Bearer <access_token>
Content-Type: application/json

请求参数:
```json
{
  "password": "string"  // 必填，要验证的密码
}
```

成功响应: 200 OK
```json
{
  "valid": true,
  "message": "密码正确"
}
```

或

```json
{
  "valid": false,
  "message": "密码错误"
}
```

错误响应:

400 Bad Request: 密码不能为空
404 Not Found: 用户不存在

### 1.6 上传用户头像

接口地址: POST /api/auth/avatar

请求头:
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

请求参数:
Form Data:
  avatar: File  // 必填，图片文件，支持 PNG、JPG、JPEG、GIF、WebP

成功响应: 200 OK
```json
{
  "message": "头像上传成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "avatar": "/uploads/avatars/1_def456.jpg",
    "settings": null,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

错误响应:

400 Bad Request: 没有上传文件或文件格式不支持
```json
{
  "error": "只支持 PNG、JPG、JPEG、GIF、WebP 格式的图片"
}
```

500 Internal Server Error: 上传失败

## 项目管理模块 (Projects)

### 2.1 获取项目列表

接口地址: GET /api/projects

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "projects": [
    {
      "id": 1,
      "name": "项目名称",
      "description": "项目描述",
      "status": "active",
      "folder_id": null,
      "owner_id": 1,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

错误响应:

401 Unauthorized: Token 无效或过期

### 2.2 获取单个项目详情

接口地址: GET /api/projects/:projectId

请求头:
Authorization: Bearer <access_token>

查询参数:
include_resources: boolean  // 可选，是否包含资源列表，默认 false

成功响应: 200 OK
```json
{
  "project": {
    "id": 1,
    "name": "项目名称",
    "description": "项目描述",
    "status": "active",
    "folder_id": null,
    "owner_id": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "resources": [  // 仅当 include_resources=true 时返回
      {
        "id": 1,
        "filename": "document.pdf",
        "file_path": "/uploads/resources/1_abc123.pdf",
        "file_size": 1024000,
        "file_type": "application/pdf",
        "uploaded_at": "2024-01-01T00:00:00"
      }
    ]
  }
}
```

错误响应:

404 Not Found: 项目不存在或无权访问

### 2.3 创建项目

接口地址: POST /api/projects

请求头:
Authorization: Bearer <access_token>
Content-Type: application/json

请求参数:
```json
{
  "name": "string",        // 必填，项目名称
  "description": "string", // 可选，项目描述
  "folder_id": number      // 可选，所属文件夹ID
}
```

成功响应: 201 Created
```json
{
  "message": "项目创建成功",
  "project": {
    "id": 1,
    "name": "新项目",
    "description": "项目描述",
    "status": "active",
    "folder_id": null,
    "owner_id": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

错误响应:

400 Bad Request: 参数验证失败

### 2.4 更新项目

接口地址: PUT /api/projects/:projectId

请求头:
Authorization: Bearer <access_token>
Content-Type: application/json

请求参数:
```json
{
  "name": "string",        // 可选，项目名称
  "description": "string", // 可选，项目描述
  "status": "string"       // 可选，项目状态 (active/archived)
}
```

成功响应: 200 OK
```json
{
  "message": "项目更新成功",
  "project": {
    "id": 1,
    "name": "更新后的项目名",
    "description": "更新后的描述",
    "status": "active",
    "folder_id": null,
    "owner_id": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-02T00:00:00"
  }
}
```

错误响应:

404 Not Found: 项目不存在或无权访问

### 2.5 删除项目

接口地址: DELETE /api/projects/:projectId

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "message": "项目删除成功"
}
```

错误响应:

404 Not Found: 项目不存在或无权访问

## 资源管理模块 (Resources)

### 3.1 获取项目资源列表

接口地址: GET /api/projects/:projectId/resources

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "resources": [
    {
      "id": 1,
      "project_id": 1,
      "filename": "document.pdf",
      "file_path": "/uploads/resources/1_abc123.pdf",
      "file_size": 1024000,
      "file_type": "application/pdf",
      "uploaded_at": "2024-01-01T00:00:00"
    }
  ]
}
```

错误响应:

404 Not Found: 项目不存在或无权访问

### 3.2 上传资源文件

接口地址: POST /api/projects/:projectId/resources

请求头:
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

请求参数:
Form Data:
  file: File  // 必填，文件对象

成功响应: 201 Created
```json
{
  "message": "资源上传成功",
  "resource": {
    "id": 1,
    "project_id": 1,
    "filename": "document.pdf",
    "file_path": "/uploads/resources/1_abc123.pdf",
    "file_size": 1024000,
    "file_type": "application/pdf",
    "uploaded_at": "2024-01-01T00:00:00"
  }
}
```

错误响应:

400 Bad Request: 没有上传文件或文件格式不支持
404 Not Found: 项目不存在或无权访问
413 Payload Too Large: 文件大小超过限制（100MB）

### 3.3 删除资源

接口地址: DELETE /api/projects/:projectId/resources/:resourceId

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "message": "资源删除成功"
}
```

错误响应:

404 Not Found: 资源不存在或无权访问

## 文件夹管理模块 (Folders)

### 4.1 获取文件夹列表

接口地址: GET /api/folders

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "folders": [
    {
      "id": 1,
      "name": "工作项目",
      "color": "blue",
      "owner_id": 1,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

错误响应:

401 Unauthorized: Token 无效或过期

### 4.2 创建文件夹

接口地址: POST /api/folders

请求头:
Authorization: Bearer <access_token>
Content-Type: application/json

请求参数:
```json
{
  "name": "string",  // 必填，文件夹名称
  "color": "string"  // 可选，文件夹颜色，默认 "blue"
}
```

成功响应: 201 Created
```json
{
  "message": "文件夹创建成功",
  "folder": {
    "id": 1,
    "name": "新文件夹",
    "color": "blue",
    "owner_id": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

错误响应:

400 Bad Request: 文件夹名称不能为空

### 4.3 更新文件夹

接口地址: PUT /api/folders/:folderId

请求头:
Authorization: Bearer <access_token>
Content-Type: application/json

请求参数:
```json
{
  "name": "string",  // 可选，文件夹名称
  "color": "string"  // 可选，文件夹颜色
}
```

成功响应: 200 OK
```json
{
  "message": "文件夹更新成功",
  "folder": {
    "id": 1,
    "name": "更新后的文件夹",
    "color": "green",
    "owner_id": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-02T00:00:00"
  }
}
```

错误响应:

404 Not Found: 文件夹不存在或无权访问

### 4.4 删除文件夹

接口地址: DELETE /api/folders/:folderId

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "message": "文件夹删除成功"
}
```

说明: 删除文件夹时，文件夹内的项目会被移到根目录（folder_id 设为 null）

错误响应:

404 Not Found: 文件夹不存在或无权访问

### 4.5 将项目添加到文件夹

接口地址: POST /api/folders/:folderId/projects/:projectId

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "message": "项目已添加到文件夹"
}
```

错误响应:

404 Not Found: 文件夹或项目不存在或无权访问

### 4.6 从文件夹移除项目

接口地址: DELETE /api/folders/:folderId/projects/:projectId

请求头:
Authorization: Bearer <access_token>

成功响应: 200 OK
```json
{
  "message": "项目已从文件夹移除"
}
```

说明: 移除后项目的 folder_id 会被设为 null，项目会回到根目录

错误响应:

404 Not Found: 文件夹或项目不存在或无权访问

## 通用说明

### 认证机制

所有需要认证的接口都需要在请求头中携带 JWT Token:

Authorization: Bearer <access_token>

Token 在用户登录或注册成功后返回，有效期为 24 小时。

### 错误响应格式

所有错误响应都遵循以下格式:

```json
{
  "error": "错误描述信息"
}
```

### HTTP 状态码

200 OK: 请求成功
201 Created: 资源创建成功
400 Bad Request: 请求参数错误
401 Unauthorized: 未授权或 Token 无效
404 Not Found: 资源不存在
409 Conflict: 资源冲突（如用户名已存在）
413 Payload Too Large: 上传文件过大
500 Internal Server Error: 服务器内部错误

### 文件上传限制

最大文件大小: 100MB
支持的图片格式: PNG, JPG, JPEG, GIF, WebP
支持的文档格式: PDF, DOC, DOCX, TXT, MD, XLSX, XLS, PPTX, PPT

### 静态文件访问

上传的文件可以通过以下 URL 访问:

http://localhost:5000/uploads/<path>

例如:
头像: http://localhost:5000/uploads/avatars/1_abc123.jpg
资源: http://localhost:5000/uploads/resources/1_def456.pdf

### 前端拦截器

前端使用 Axios 拦截器自动处理:

1. 请求拦截器: 自动在请求头中添加 Token
2. 响应拦截器: 自动处理 401 错误，清除本地存储并刷新页面

### WebSocket 连接（预留）

WebSocket 服务用于实时协作功能（当前为预留接口）:

```javascript
// 连接 WebSocket
wsService.connect('ws://localhost:5000/ws')

// 监听消息
wsService.on('message', (data) => {
  console.log('收到消息:', data)
})

// 发送消息
wsService.send({ type: 'edit', content: '...' })
```

## 附录

### 数据模型

User (用户)
```typescript
{
  id: number
  username: string
  email: string
  avatar: string | null
  settings: object | null
  created_at: string (ISO 8601)
}
```

Project (项目)
```typescript
{
  id: number
  name: string
  description: string
  status: 'active' | 'archived'
  folder_id: number | null
  owner_id: number
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

Resource (资源)
```typescript
{
  id: number
  project_id: number
  filename: string
  file_path: string
  file_size: number
  file_type: string
  uploaded_at: string (ISO 8601)
}
```

Folder (文件夹)
```typescript
{
  id: number
  name: string
  color: string
  owner_id: number
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

## 更新日志

v1.0.0 (2024-01-18)

初始版本
完成认证、项目、资源、文件夹模块的接口定义
添加头像上传功能
添加密码验证接口

文档维护者: 开发团队
最后更新: 2024-01-18
