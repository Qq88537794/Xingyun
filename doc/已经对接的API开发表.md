# 星韵 (Xingyun) 前后端 API 对接表

> 最后更新时间：2026-01-14

## 已完成对接的 API

| 功能     | 请求方式 | API 路径               | 前端文件           | 后端文件           | 状态      |
| -------- | -------- | ---------------------- | ------------------ | ------------------ | --------- |
| 用户注册 | POST     | `/api/auth/register` | `stores/auth.js` | `routes/auth.py` | ✅ 已完成 |
| 用户登录 | POST     | `/api/auth/login`    | `stores/auth.js` | `routes/auth.py` | ✅ 已完成 |

---

## API 详细说明

### 1. 用户注册

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

### 2. 用户登录

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
