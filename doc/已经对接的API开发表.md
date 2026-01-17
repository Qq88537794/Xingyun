# 星韵 (Xingyun) 前后端 API 对接表

> 最后更新时间：2026-01-17

## 已完成对接的 API

| 功能     | 请求方式 | API 路径               | 前端文件           | 后端文件           | 状态      |
| -------- | -------- | ---------------------- | ------------------ | ------------------ | --------- |
| 用户注册 | POST     | `/api/auth/register` | `stores/auth.js` | `routes/auth.py` | ✅ 已完成 |
| 用户登录 | POST     | `/api/auth/login`    | `stores/auth.js` | `routes/auth.py` | ✅ 已完成 |
| 获取当前用户 | GET | `/api/user/me` | `services/auth.js` | `routes/user.py` | ✅ 已完成 |
| 更新用户资料 | PUT | `/api/user/profile` | `stores/auth.js`, `services/auth.js` | `routes/user.py` | ✅ 已完成 |
| 修改密码 | POST | `/api/user/change-password` | `stores/auth.js` | `routes/user.py` | ✅ 已完成 |
| 获取项目列表 | GET | `/api/projects` | `services/projects.js` | `routes/projects.py` | ✅ 已完成 |
| 创建项目 | POST | `/api/projects` | `services/projects.js` | `routes/projects.py` | ✅ 已完成 |
| 更新项目 | PUT | `/api/projects/<id>` | `services/projects.js` | `routes/projects.py` | ✅ 已完成 |
| 删除项目 | DELETE | `/api/projects/<id>` | `services/projects.js` | `routes/projects.py` | ✅ 已完成 |
| 获取资源列表 | GET | `/api/projects/<id>/resources` | `services/resources.js` | `routes/resources.py` | ✅ 已完成 |
| 上传资源 | POST | `/api/projects/<id>/resources` | `services/resources.js` | `routes/resources.py` | ✅ 已完成 |
| 删除资源 | DELETE | `/api/projects/<id>/resources/<rid>` | `services/resources.js` | `routes/resources.py` | ✅ 已完成 |

---

## 对接统计

| 模块 | API 数量 |
|------|----------|
| 认证模块 | 2 |
| 用户模块 | 3 |
| 项目模块 | 4 |
| 资源模块 | 3 |
| **总计** | **12** |

---

## API 详细说明

### 认证模块

#### 1. 用户注册

**请求**

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应 (201)**

```json
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "created_at": "2026-01-14T00:00:00"
  },
  "access_token": "jwt_token_string"
}
```

**错误响应**

| 状态码 | 说明                                                                                             |
| ------ | ------------------------------------------------------------------------------------------------ |
| 400    | 请求数据不能为空 / 用户名、邮箱和密码不能为空 / 用户名长度应为2-64个字符 / 密码长度至少为6个字符 |
| 409    | 用户名已被注册 / 邮箱已被注册                                                                    |
| 500    | 注册失败（服务器错误）                                                                           |

---

#### 2. 用户登录

**请求**

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",  // 可以是用户名或邮箱
  "password": "string"
}
```

**响应 (200)**

```json
{
  "message": "登录成功",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "created_at": "2026-01-14T00:00:00"
  },
  "access_token": "jwt_token_string"
}
```

**错误响应**

| 状态码 | 说明                                    |
| ------ | --------------------------------------- |
| 400    | 请求数据不能为空 / 用户名和密码不能为空 |
| 401    | 用户名或密码错误                        |

---

### 用户模块

#### 3. 获取当前用户信息

**请求**

```http
GET /api/user/me
Authorization: Bearer <token>
```

**响应 (200)**

```json
{
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "avatar": "string",
    "description": "string",
    "last_login": "2026-01-17T00:00:00",
    "created_at": "2026-01-14T00:00:00"
  }
}
```

---

#### 4. 更新用户资料

**请求**

```http
PUT /api/user/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "string",      // 可选
  "description": "string"    // 可选
}
```

**响应 (200)**

```json
{
  "message": "更新成功",
  "user": { ... }
}
```

---

#### 5. 修改密码

**请求**

```http
POST /api/user/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "oldPassword": "string",
  "newPassword": "string"
}
```

**响应 (200)**

```json
{
  "message": "密码修改成功"
}
```

---

### 项目模块

#### 6. 获取项目列表

**请求**

```http
GET /api/projects
Authorization: Bearer <token>
```

**响应 (200)**

```json
{
  "projects": [
    {
      "id": 1,
      "name": "项目名称",
      "description": "项目描述",
      "status": "active",
      "created_at": "2026-01-14T00:00:00"
    }
  ],
  "total": 1
}
```

---

#### 7. 创建项目

**请求**

```http
POST /api/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "项目名称",
  "description": "项目描述（可选）"
}
```

**响应 (201)**

```json
{
  "message": "项目创建成功",
  "project": { ... }
}
```

---

#### 8. 更新项目

**请求**

```http
PUT /api/projects/<id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "新名称",
  "description": "新描述"
}
```

**响应 (200)**

```json
{
  "message": "项目更新成功",
  "project": { ... }
}
```

---

#### 9. 删除项目

**请求**

```http
DELETE /api/projects/<id>
Authorization: Bearer <token>
```

**响应 (200)**

```json
{
  "message": "项目删除成功"
}
```

---

### 资源模块

#### 10. 获取资源列表

**请求**

```http
GET /api/projects/<project_id>/resources
Authorization: Bearer <token>
```

**响应 (200)**

```json
{
  "resources": [
    {
      "id": 1,
      "filename": "文档.docx",
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "file_size": 12345,
      "parsing_status": "pending",
      "uploaded_at": "2026-01-14T00:00:00"
    }
  ],
  "total": 1
}
```

---

#### 11. 上传资源

**请求**

```http
POST /api/projects/<project_id>/resources
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

**响应 (201)**

```json
{
  "message": "文件上传成功",
  "resource": { ... }
}
```

---

#### 12. 删除资源

**请求**

```http
DELETE /api/projects/<project_id>/resources/<resource_id>
Authorization: Bearer <token>
```

**响应 (200)**

```json
{
  "message": "资源删除成功"
}
```

---

## 前端服务文件说明

| 文件路径 | 功能 |
|----------|------|
| `stores/auth.js` | 用户认证（登录、注册、Token管理、更新资料、修改密码） |
| `services/auth.js` | 认证服务封装（登录、注册、获取用户信息、更新资料） |
| `services/projects.js` | 项目 CRUD 操作 |
| `services/resources.js` | 资源上传、列表、删除 |
