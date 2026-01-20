# 行云文档 (Xingyun) - 智能文档处理平台

基于 Electron + Vue.js + TipTap 的 AI 驱动文档生成与编辑桌面应用。

## 📖 项目概述

行云文档是一款集自然语言理解、内容生成、多轮交互与图像处理于一体的智能文档平台，旨在提供高效、精准且灵活的文档与图片生成解决方案。

## 🛠️ 技术栈

| 层级                 | 技术                           |
| -------------------- | ------------------------------ |
| **前端框架**   | Electron + Vue.js 3            |
| **富文本编辑** | TipTap                         |
| **状态管理**   | Pinia                          |
| **样式**       | TailwindCSS + Lucide Icons     |
| **后端框架**   | Flask 3.0                      |
| **ORM**        | SQLAlchemy                     |
| **数据库**     | MySQL 8.0+                     |
| **认证**       | Flask-JWT-Extended             |
| **AI模型**     | 智谱AI (GLM-4) / Google Gemini |
| **向量数据库** | Qdrant                         |
| **Embedding**  | BGE-small-zh-v1.5 / 智谱API    |

---

## 🚀 快速开始

### 环境要求

在开始之前，请确保已安装以下软件：

| 软件    | 版本   | 下载地址                           |
| ------- | ------ | ---------------------------------- |
| Node.js | 16.0+  | [nodejs.org](https://nodejs.org/)     |
| Python  | 3.8+   | [python.org](https://www.python.org/) |
| MySQL   | 8.0+   | [mysql.com](https://www.mysql.com/)   |
| Docker  | 20.0+  | [docker.com](https://www.docker.com/) |
| Git     | 最新版 | [git-scm.com](https://git-scm.com/)   |

> 💡 **Docker说明**：AI模块需要Qdrant向量数据库,推荐使用Docker部署

---

### 第一步：克隆项目

```bash
git clone https://github.com/Qq88537794/Xingyun.git
cd Xingyun
```

---

### 第二步：配置数据库

#### 2.1 创建 MySQL 数据库

登录 MySQL 并执行初始化脚本：

```bash
# 登录 MySQL
mysql -u root -p

# 在 MySQL 命令行中执行
source backend/migrations/init_database.sql
```

或者分步执行：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS xingyun 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- 切换到数据库后执行初始化脚本
USE xingyun;
SOURCE backend/migrations/init_database.sql;
```

#### 2.2 配置环境变量

复制环境变量模板并填入你的数据库配置：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# Flask 应用密钥 (建议修改为随机字符串)
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# MySQL 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=xingyun
DB_USER=root
DB_PASSWORD=your_mysql_password

# AI模型配置
LLM_PROVIDER=zhipu              # 或 gemini
ZHIPU_API_KEY=your_zhipu_api_key
GEMINI_API_KEY=your_gemini_api_key

# Embedding配置
EMBEDDING_PROVIDER=zhipu        # zhipu 或 local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# Qdrant向量数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_USE_MEMORY=false         # 生产环境建议使用Docker
```

> ⚠️ **重要提示**：`.env` 文件包含敏感信息，已配置在 `.gitignore` 中，不会被提交到 Git。

---

### 第三步：安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

依赖列表：

- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-JWT-Extended 4.6.0
- Flask-CORS 4.0.0
- PyMySQL 1.1.0
- python-dotenv 1.0.0
- langchain 0.3.18 (AI模块)
- qdrant-client 1.12.1 (向量数据库)
- sentence-transformers 3.3.1 (本地Embedding,可选)

---

### 第四步：配置AI服务

#### 4.1 获取API密钥

**智谱AI (推荐)**：

1. 访问 [open.bigmodel.cn](https://open.bigmodel.cn/)
2. 注册并在控制台创建API Key
3. 将API Key填入 `.env` 文件的 `ZHIPU_API_KEY`

**Google Gemini (可选)**：

1. 访问 [ai.google.dev](https://ai.google.dev/)
2. 获取API Key
3. 将API Key填入 `.env` 文件的 `GEMINI_API_KEY`

#### 4.2 启动Qdrant向量数据库

**使用Docker (推荐)**：

```bash
# 拉取并启动Qdrant
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# 验证运行状态
curl http://localhost:6333
```

**Windows PowerShell**：

```powershell
docker run -d -p 6333:6333 -p 6334:6334 -v "${PWD}\qdrant_storage:/qdrant/storage" qdrant/qdrant
```

> 💡 **内存模式**：如果不想使用Docker,可在 `.env` 中设置 `QDRANT_USE_MEMORY=true`,但数据不会持久化。

#### 4.3 (可选) 配置本地Embedding模型

如果想使用本地Embedding模型而不调用API:

```bash
cd backend
pip install sentence-transformers torch
```

然后在 `.env` 中设置：

```ini
EMBEDDING_PROVIDER=local
```

首次使用会自动下载 `BAAI/bge-small-zh-v1.5` 模型(约400MB)。

---

### 第五步：启动后端服务

```bash
cd backend
python app.py
```

成功启动后将显示：

```
==================================================
Running on: http://127.0.0.1:5000
Upload folder: .../backend/uploads
==================================================
```

---

### 第六步：安装前端依赖

打开新的终端窗口：

```bash
cd frontend
npm install
```

---

### 第七步：启动前端应用

**开发模式**（推荐，支持热重载）：

```bash
npm run electron:dev
```

**生产构建**：

```bash
npm run electron:build
```

---

### 第八步：开始使用

1. 应用启动后，在主界面左下角点击 **"登录/注册"**
2. 注册新账号（需要用户名、邮箱、密码）
3. 登录成功后即可开始使用项目管理、文档编辑和AI助手功能
4. **AI功能**：在编辑器右侧的聊天面板中与AI对话，上传资料后AI会自动学习知识库

---

## 📁 项目结构

```
Xingyun/
├── backend/                    # Python 后端服务
│   ├── models/                 # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── project.py          # 项目模型
│   │   ├── folder.py           # 文件夹模型
│   │   └── resource.py         # 资源模型
│   ├── routes/                 # API 路由
│   │   ├── auth.py             # 认证路由 (/api/auth)
│   │   ├── user.py             # 用户路由 (/api/user)
│   │   ├── projects.py         # 项目路由 (/api/projects)
│   │   ├── folders.py          # 文件夹路由 (/api/folders)
│   │   └── resources.py        # 资源路由
│   ├── migrations/             # 数据库迁移
│   │   └── init_database.sql   # 数据库初始化脚本
│   ├── uploads/                # 文件上传目录
│   ├── app.py                  # 后端入口
│   ├── config.py               # 配置文件
│   ├── requirements.txt        # Python 依赖
│   ├── .env.example            # 环境变量模板
│   └── .env                    # 环境变量 (不提交)
├── frontend/                   # Electron + Vue 前端
│   ├── electron/               # Electron 主进程
│   │   ├── main.js             # 主进程入口
│   │   └── preload.js          # 预加载脚本
│   ├── src/                    # Vue 源代码
│   │   ├── components/         # 组件
│   │   ├── views/              # 页面视图
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── services/           # API 服务
│   │   └── App.vue             # 根组件
│   ├── package.json            # 前端依赖
│   └── vite.config.js          # Vite 配置
├── doc/                        # 项目文档
│   ├── 已完成后端API开发表.md   # 后端 API 文档
│   ├── 已经对接的API开发表.md   # 前后端对接文档
│   └── 数据库表设计文档.md      # 数据库设计文档
├── .gitignore                  # Git 忽略配置
└── README.md                   # 项目说明
```

---

## 🔌 API 接口概览

### 认证模块 `/api/auth`

| 方法 | 路径                   | 功能     |
| ---- | ---------------------- | -------- |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login`    | 用户登录 |

### 用户模块 `/api/user`

| 方法 | 路径                          | 功能             |
| ---- | ----------------------------- | ---------------- |
| GET  | `/api/user/me`              | 获取当前用户信息 |
| PUT  | `/api/user/profile`         | 更新用户资料     |
| POST | `/api/user/change-password` | 修改密码         |
| POST | `/api/user/verify-password` | 验证密码         |
| POST | `/api/user/avatar`          | 上传头像         |

### 项目模块 `/api/projects`

| 方法   | 路径                   | 功能         |
| ------ | ---------------------- | ------------ |
| GET    | `/api/projects`      | 获取项目列表 |
| POST   | `/api/projects`      | 创建项目     |
| GET    | `/api/projects/<id>` | 获取项目详情 |
| PUT    | `/api/projects/<id>` | 更新项目     |
| DELETE | `/api/projects/<id>` | 删除项目     |

### 文件夹模块 `/api/folders`

| 方法   | 路径                  | 功能           |
| ------ | --------------------- | -------------- |
| GET    | `/api/folders`      | 获取文件夹列表 |
| POST   | `/api/folders`      | 创建文件夹     |
| PUT    | `/api/folders/<id>` | 更新文件夹     |
| DELETE | `/api/folders/<id>` | 删除文件夹     |

### 资源模块 `/api/projects/<pid>/resources`

| 方法   | 路径                                    | 功能         |
| ------ | --------------------------------------- | ------------ |
| GET    | `/api/projects/<pid>/resources`       | 获取资源列表 |
| POST   | `/api/projects/<pid>/resources`       | 上传资源     |
| DELETE | `/api/projects/<pid>/resources/<rid>` | 删除资源     |

### AI模块 `/api/ai`

| 方法 | 路径                                    | 功能                         |
| ---- | --------------------------------------- | ---------------------------- |
| POST | `/api/ai/chat`                        | AI对话(支持Simple/Agent模式) |
| GET  | `/api/ai/knowledge-base/<pid>/info`   | 获取知识库状态               |
| POST | `/api/ai/knowledge-base/<pid>/search` | 搜索知识库                   |

> 📚 详细 API 文档请参考 [doc/已完成后端API开发表.md](doc/已完成后端API开发表.md)
> 🤖 AI模块技术文档参考 [doc/AI模块开发文档.md](doc/AI模块开发文档.md)
> 🔧 前端对接参考 [doc/Agent工具前端对接指南.md](doc/Agent工具前端对接指南.md)

---

## ✨ 核心功能

### 已实现 ✅

#### 基础功能

- **用户认证系统** - JWT Token 认证、登录/注册、个人资料管理
- **项目管理** - 创建、编辑、删除项目，支持搜索筛选
- **文件夹管理** - 彩色文件夹分类，支持拖拽操作
- **富文本编辑器** - 基于 TipTap，支持格式化、撤销/重做
- **材料管理** - 上传 DOCX、PDF、TXT、MD 等格式文件

#### AI功能 🤖

- **智能问答系统**

  - Simple模式：普通对话和知识查询
  - Agent模式：支持7种文档操作工具
- **RAG知识库**

  - 自动索引上传的资料（支持PDF、DOCX、TXT、MD）
  - 智能检索和引用来源
  - 基于Qdrant向量数据库
- **Agent工具系统**

  - `read_document` - 读取文档内容
  - `write_document` - 完全覆盖文档
  - `edit_document` - 精确编辑（插入/替换/删除）
  - `search_document` - 搜索文档关键词
  - `generate_outline` - 生成文档大纲
  - `expand_content` - 扩写内容
  - `summarize` - 生成摘要
- **多模型支持**

  - 智谱AI (GLM-4-Flash)
  - Google Gemini (gemini-2.0-flash-exp)
  - 本地/远程Embedding模型

### 待实现 🚧

- 文档导出 (Word、PDF、LaTeX)
- 智能图表生成
- 协同编辑功能
- AI流式响应
- 更多Agent工具

---

## 🐛 常见问题

### 1. 数据库连接失败

**症状**：启动后端时报 `Access denied` 或 `Connection refused`

**解决方案**：

1. 确认 MySQL 服务已启动
2. 检查 `.env` 文件中的数据库配置是否正确
3. 确认数据库用户有访问权限

### 2. 前端无法连接后端

**症状**：登录时显示"网络错误"

**解决方案**：

1. 确认后端服务已启动在 `http://localhost:5000`
2. 检查是否有防火墙阻止连接
3. 查看后端控制台是否有错误日志

### 3. 中文路径导致编码错误

**症状**：`UnicodeEncodeError` 或数据库路径错误

**解决方案**：
将项目移动到不含中文的路径，例如 `C:\Projects\Xingyun`

### 4. 依赖安装失败

**症状**：`pip install` 或 `npm install` 报错

**解决方案**：

```bash
# Python 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Node.js 使用国内镜像
npm install --registry=https://registry.npmmirror.com
```

### 5. AI功能无法使用

**症状**：聊天时显示"AI服务错误"或无响应

**解决方案**：

1. 检查 `.env` 文件中的API Key是否正确配置
2. 确认Qdrant服务正在运行：`curl http://localhost:6333`
3. 查看后端日志中是否有错误信息
4. 测试API连接：

   ```bash
   # 智谱AI
   curl https://open.bigmodel.cn/api/paas/v4/chat/completions \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

### 6. Qdrant连接失败

**症状**："Failed to connect to Qdrant" 或 "Connection refused"

**解决方案**：

```bash
# 检查Docker容器状态
docker ps | grep qdrant

# 如果没有运行，启动Qdrant
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 或者使用内存模式（临时方案）
# 在.env中设置: QDRANT_USE_MEMORY=true
```

### 7. 本地Embedding模型下载慢

**症状**：首次使用时长时间无响应

**解决方案**：

1. 使用API模式：在 `.env` 中设置 `EMBEDDING_PROVIDER=zhipu`
2. 或使用镜像加速：

   ```bash
   export HF_ENDPOINT=https://hf-mirror.com
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5')"
   ```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 📞 联系方式

- **项目地址**：[https://github.com/Qq88537794/Xingyun](https://github.com/Qq88537794/Xingyun)
- **问题反馈**：[Issues](https://github.com/Qq88537794/Xingyun/issues)

---

**星韵文档** - 让文档创作更智能、更高效 ✨
