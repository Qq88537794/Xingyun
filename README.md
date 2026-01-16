# 行云文档 - 智能文档处理平台

基于Electron + Vue.js + TipTap的AI驱动文档生成与编辑桌面应用。

## 项目概述

行云文档是一款集自然语言理解、内容生成、多轮交互与图像处理于一体的智能文档平台，旨在提供高效、精准且灵活的文档与图片生成解决方案。

## 技术栈

### 前端

- **Electron** - 桌面应用框架
- **Vue.js 3** - 渐进式JavaScript框架
- **TipTap** - 富文本编辑器
- **Pinia** - 状态管理
- **TailwindCSS** - CSS框架
- **Lucide Icons** - 图标库

### 后端

- **FastAPI** - Python Web框架 (Flask 3.0)
- **SQLAlchemy** - ORM框架
- **PyMySQL** - MySQL驱动
- **Flask-JWT-Extended** - JWT认证
- **WebSocket** - 实时通信
- **LLM** - 大语言模型（内容生成）
- **RAG** - 检索增强生成

## 核心功能

### ✅ 已实现

1. **用户认证系统** ⭐ 完善

   - 精美的登录/注册页面（集成在桌面页面）
   - 用户个人资料管理（查看、编辑）
   - 修改用户名、邮箱和密码
   - 友好的错误提示模态框
   - JWT Token 认证
   - 自动保存登录状态

2. **项目管理系统** ⭐ 新增

   - 项目创建、编辑、删除
   - 项目列表展示（卡片式布局）
   - 项目状态管理（活跃/归档）
   - 项目搜索和筛选

3. **文件夹管理** ⭐ 新增

   - 创建、编辑、删除文件夹
   - 文件夹颜色标识
   - 项目分类管理
   - 拖拽项目到文件夹
   - 拖拽项目回桌面
   - 文件夹项目计数

4. **拖拽功能** ⭐ 新增

   - 项目拖拽到文件夹
   - 项目拖拽回桌面
   - 拖拽视觉反馈（高亮、透明度）
   - 拖拽状态管理

5. **TipTap富文本编辑器**

   - 撤销/重做功能（Ctrl+Z / Ctrl+Y）
   - 支持标题、粗体、斜体、下划线等格式
   - 支持有序/无序列表
   - 支持插入图片和表格

6. **材料管理**

   - 上传参考材料（DOCX、PDF、TXT、MD、HTML）
   - 材料列表展示和删除
   - 按项目组织材料

7. **AI对话界面**

   - 与AI助手实时对话
   - 消息历史记录
   - 上下文感知对话

8. **文档操作**

   - 新建/打开/保存文档
   - JSON格式文档模型
   - 历史记录和版本控制
   - 自动保存草稿

9. **用户体验优化** ⭐ 新增

   - 友好的错误提示模态框
   - Toast 通知系统
   - 加载状态提示
   - 响应式设计
   - 流畅的动画过渡

10. **WebSocket通信**

    - 与后端实时通信
    - 自动重连机制

### 🚧 待实现

1. **AI功能集成**

   - 基于材料的智能内容生成
   - 大纲自动生成
   - 内容优化和润色
2. **文档导出**

   - 导出为Word（.docx）
   - 导出为PDF
   - 导出为LaTeX
   - 导出为Markdown
3. **图表生成**

   - 流程图（Mermaid.js）
   - 架构图（PlantUML）
   - AI生成图片
4. **高级编辑功能**

   - 协同编辑
   - 评论和批注
   - 模板系统

## 项目结构

```
行云文档/
├── backend/                    # Python后端服务
│   ├── models/                 # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── project.py          # 项目模型
│   │   ├── folder.py           # 文件夹模型
│   │   ├── resource.py         # 资源模型
│   │   └── __init__.py
│   ├── routes/                 # API路由
│   │   ├── auth.py             # 认证路由
│   │   ├── projects.py         # 项目路由
│   │   ├── folders.py          # 文件夹路由
│   │   ├── resources.py        # 资源路由
│   │   └── __init__.py
│   ├── migrations/             # 数据库迁移
│   │   └── add_folders.sql     # 文件夹功能迁移
│   ├── uploads/                # 文件上传目录
│   ├── app.py                  # 后端入口
│   ├── config.py               # 配置文件
│   ├── requirements.txt        # 依赖列表
│   └── start.bat               # Windows启动脚本
├── doc/                        # 项目文档
│   ├── 数据库表设计文档.md      # 数据库设计
│   ├── 已完成后端API开发表.md   # API开发进度
│   └── 已经对接的API开发表.md   # API对接状态
├── frontend/                   # 前端项目 (Electron + Vue)
│   ├── electron/               # Electron主进程
│   │   ├── main.js             # 主进程入口
│   │   └── preload.js          # 预加载脚本
│   ├── src/                    # Vue源代码
│   │   ├── components/         # 组件
│   │   │   ├── ErrorModal.vue  # 错误提示模态框
│   │   │   ├── TopBar.vue      # 顶部导航栏
│   │   │   └── ...
│   │   ├── views/              # 页面视图
│   │   │   ├── ProjectsView.vue # 项目桌面页面
│   │   │   └── EditorView.vue   # 编辑器页面
│   │   ├── stores/             # 状态管理
│   │   │   ├── auth.js         # 认证状态
│   │   │   └── ...
│   │   ├── services/           # API服务
│   │   │   ├── auth.js         # 认证服务
│   │   │   ├── folders.js      # 文件夹服务
│   │   │   └── ...
│   │   ├── composables/        # 组合式函数
│   │   ├── App.vue             # 根组件
│   │   ├── main.js             # 前端入口
│   │   └── style.css           # 全局样式
│   ├── dist/                   # 构建输出
│   ├── package.json            # 前端项目配置
│   ├── vite.config.js          # Vite配置
│   ├── tailwind.config.js      # TailwindCSS配置
│   └── index.html              # HTML模板
└── README.md                   # 项目总文档
```

## 快速开始

### 环境要求

- **Node.js** 16.0+
- **Python** 3.8+
- **MySQL** 8.0+

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/Qq88537794/Xingyun.git
cd Xingyun
```

#### 2. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE xingyun CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

运行初始化脚本：

```bash
mysql -u root -p xingyun < doc/数据库表设计文档.md
```

运行文件夹功能迁移：

```bash
mysql -u root -p xingyun < backend/migrations/add_folders.sql
```

修改 `backend/config.py` 中的数据库配置：

```python
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'YourPassword')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'xingyun')
```

#### 3. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 4. 启动后端服务

```bash
# Windows
start.bat

# Linux/Mac
python app.py
```

后端服务将启动在 `http://localhost:5000`

#### 5. 安装前端依赖

```bash
cd frontend
npm install
```

#### 6. 启动前端应用

开发模式（带热重载）：

```bash
npm run electron:dev
```

构建生产版本：

```bash
npm run electron:build
```

### 首次使用

1. 启动应用后，在桌面页面左下角点击"登录/注册"
2. 注册新账号或使用已有账号登录
3. 登录成功后即可开始使用项目管理和文档编辑功能

## 功能特性详解

### 桌面项目管理

- **项目卡片视图**：以卡片形式展示所有项目，支持快速预览
- **文件夹分类**：创建彩色文件夹对项目进行分类管理
- **拖拽操作**：支持拖拽项目到文件夹或拖回桌面
- **搜索筛选**：快速查找项目
- **项目状态**：标记项目为活跃或归档状态

### 用户认证与个人资料

- **安全登录**：基于 JWT Token 的安全认证机制
- **用户注册**：支持邮箱注册，自动验证用户名和邮箱唯一性
- **个人资料编辑**：修改用户名、邮箱、密码
- **头像管理**：支持自定义用户头像（待实现）
- **友好提示**：所有操作都有清晰的错误提示和成功反馈

### 文件夹管理

- **创建文件夹**：自定义文件夹名称和颜色（6种颜色可选）
- **编辑文件夹**：修改文件夹名称和颜色
- **删除文件夹**：删除文件夹时，其中的项目会保留在根目录
- **项目计数**：实时显示每个文件夹中的项目数量
- **颜色标识**：通过颜色快速识别不同类别的文件夹

### 富文本编辑器

- **格式化工具**：标题、粗体、斜体、下划线、删除线
- **列表支持**：有序列表、无序列表
- **撤销重做**：完整的编辑历史记录（Ctrl+Z / Ctrl+Y）
- **插入元素**：图片、表格、链接
- **实时保存**：自动保存编辑内容

### 材料管理

- **多格式支持**：DOCX、PDF、TXT、MD、HTML
- **拖拽上传**：支持拖拽文件到上传区域
- **材料列表**：查看和管理已上传的参考材料
- **按项目组织**：每个项目独立管理其参考材料

## API 接口文档

### 认证接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/profile` - 获取用户信息
- `PUT /api/auth/profile` - 更新用户信息

### 项目接口

- `GET /api/projects` - 获取所有项目
- `POST /api/projects` - 创建项目
- `PUT /api/projects/:id` - 更新项目
- `DELETE /api/projects/:id` - 删除项目

### 文件夹接口

- `GET /api/folders` - 获取所有文件夹
- `POST /api/folders` - 创建文件夹
- `PUT /api/folders/:id` - 更新文件夹
- `DELETE /api/folders/:id` - 删除文件夹
- `POST /api/folders/:folderId/projects/:projectId` - 将项目添加到文件夹
- `POST /api/folders/projects/:projectId/remove` - 将项目从文件夹移出

### 资源接口

- `GET /api/resources` - 获取资源列表
- `POST /api/resources` - 上传资源
- `DELETE /api/resources/:id` - 删除资源

详细的 API 文档请参考 `doc/已完成后端API开发表.md`。

## 核心概念

### 1. 桌面式项目管理

借鉴 GoodNotes 的设计理念，采用桌面式布局：
- **左侧侧边栏**：显示文件夹列表和用户信息
- **右侧主区域**：显示项目卡片
- **拖拽交互**：直观的拖拽操作体验

### 2. JSON文档模型

整个文档以JSON格式作为唯一真实数据源，所有操作都是对JSON结构的修改。

```json
{
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 1 },
      "content": [{ "type": "text", "text": "标题" }]
    },
    {
      "type": "paragraph",
      "content": [{ "type": "text", "text": "段落内容" }]
    }
  ]
}
```

### 3. AI专家团队（规划中）

采用多个专业AI角色协同工作，而非单一AI模型：

- **AI总指挥** - 任务调度和指令分发
- **内容生成专家** - 文档内容创作
- **格式专家** - 文档排版和美化
- **图表专家** - 图表生成和优化

### 4. WebSocket通信

前端通过WebSocket与后端服务实时通信：

```javascript
// 发送消息到后端
wsService.send({
  type: 'chat',
  message: '帮我生成一份项目报告',
  context: {
    document: editorJSON,
    materials: uploadedFiles
  }
})

// 接收后端响应
wsService.on('message', (data) => {
  if (data.type === 'document_update') {
    editor.commands.setContent(data.content)
  }
})
```

## 开发指南

### 代码规范

- **Python**：遵循 PEP 8 规范
- **JavaScript/Vue**：遵循 ESLint 规范
- **提交信息**：使用语义化提交信息

### 调试技巧

#### 前端调试

在开发模式下，按 `Ctrl+Shift+I` 打开开发者工具。

#### 后端调试

查看后端日志：

```bash
cd backend
python app.py
```

### 常见问题

#### 1. 数据库连接失败

检查 `backend/config.py` 中的数据库配置是否正确，确保 MySQL 服务已启动。

#### 2. 前端无法连接后端

确保后端服务已启动在 `http://localhost:5000`，检查防火墙设置。

#### 3. 文件夹功能不显示

确保已运行数据库迁移脚本 `backend/migrations/add_folders.sql`。

#### 4. 登录后无法加载数据

检查浏览器控制台是否有错误，确认 JWT Token 是否正确保存。

## 项目路线图

### 已完成 ✅

- [x] 用户认证系统
- [x] 项目管理功能
- [x] 文件夹分类管理
- [x] 拖拽交互功能
- [x] 富文本编辑器基础功能
- [x] 材料上传管理
- [x] 友好的错误提示系统

### 进行中 🚧

- [ ] AI 内容生成集成
- [ ] WebSocket 实时通信优化
- [ ] 文档导出功能（Word、PDF）

### 计划中 📋

- [ ] 协同编辑功能
- [ ] 图表智能生成
- [ ] 模板系统
- [ ] 移动端适配
- [ ] 云端同步

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 报告问题

如果发现 Bug 或有功能建议，请在 [Issues](https://github.com/Qq88537794/Xingyun/issues) 中提出。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

感谢所有为本项目做出贡献的开发者！

## 联系方式

- 项目地址：[https://github.com/Qq88537794/Xingyun](https://github.com/Qq88537794/Xingyun)
- 问题反馈：[Issues](https://github.com/Qq88537794/Xingyun/issues)

---

**行云文档** - 让文档创作更智能、更高效 ✨
