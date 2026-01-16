# 文件夹功能设置指南

## 已完成的后端工作

1. ✅ 创建了 Folder 模型 (`backend/models/folder.py`)
2. ✅ 更新了 Project 模型，添加 `folder_id` 字段
3. ✅ 创建了文件夹 API 路由 (`backend/routes/folders.py`)
4. ✅ 注册了文件夹路由
5. ✅ 创建了数据库迁移 SQL (`backend/migrations/add_folders.sql`)
6. ✅ 创建了前端文件夹服务 (`frontend/src/services/folders.js`)
7. ✅ 更新了 ProjectsView 组件的逻辑部分

## 需要执行的步骤

### 1. 运行数据库迁移

在 MySQL 中执行以下命令：

```bash
mysql -u root -p xingyun < backend/migrations/add_folders.sql
```

或者在 MySQL 命令行中：

```sql
USE xingyun;
SOURCE backend/migrations/add_folders.sql;
```

### 2. 重启后端服务

```bash
cd backend
python app.py
```

### 3. 更新前端界面

前端的 ProjectsView.vue 已经添加了文件夹相关的逻辑，但还需要更新模板部分。

需要在模板中添加：
- 左侧文件夹列表侧边栏
- 创建文件夹按钮
- 文件夹编辑/删除功能
- 项目拖拽到文件夹的功能

由于模板部分较长，建议参考 GoodNotes 的设计：
- 左侧显示文件夹列表
- 点击文件夹显示该文件夹内的项目
- 支持拖拽项目到文件夹
- 文件夹可以设置颜色

## API 端点

### 文件夹相关
- `GET /api/folders` - 获取所有文件夹
- `POST /api/folders` - 创建文件夹
- `PUT /api/folders/:id` - 更新文件夹
- `DELETE /api/folders/:id` - 删除文件夹

### 项目-文件夹关联
- `POST /api/folders/:folderId/projects/:projectId` - 将项目添加到文件夹
- `POST /api/folders/projects/:projectId/remove` - 将项目从文件夹移出

## 下一步

如果需要完整的前端界面实现，我可以：
1. 创建一个新的完整的 ProjectsView 组件
2. 或者提供详细的模板代码片段供你手动添加
