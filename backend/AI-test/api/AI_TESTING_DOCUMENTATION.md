# AI 模块接口测试文档 ✅

## 概要 ✨
该文档说明用于验证后端 AI 相关接口（项目管理、资源上传、文件索引、Simple/Agent 聊天、知识库搜索）的自动化测试流程、判定依据与可复现步骤。目的是保证 RAG（检索增强生成）与 Chat 接口在代码变更或部署后能正确工作。

---

## 环境与前置条件 🔧
- 代码位置: `backend/`。
- 测试脚本: `test/test_ai_endpoints.py`（使用管理员 Token 进行快速测试）。
- 管理员 Token（开发环境）: `dev-admin-token-2026-xingyun`。
- 依赖服务:
  - Flask 后端（默认 http://127.0.0.1:5000）
  - 向量数据库（Qdrant）和索引服务（本地或容器）
  - Embedding/AI 模型服务（用于向量化与生成响应）
- 运行命令（在虚拟环境中）:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test/test_ai_endpoints.py
```

> 注意: 测试使用管理员 Token 以简化权限相关验证（已在 `auth_decorator.py` 中支持 `jwt_or_admin_required`）。

---

## 覆盖的测试用例（简要） 📋
- 创建项目
  - 目标: 验证 `POST /api/projects` 能成功创建项目并返回 `201` 与 `project.id`。
  - 判定依据: HTTP 201，返回 JSON 包含 `project` 且具有 `id`。

- 资源上传（新增）
  - 目标: 验证 `POST /api/projects/{project_id}/resources` 接受文件上传并触发索引。
  - 判定依据: HTTP 201，返回 `resource.id`；索引成功后 `parsing_status` 更新为 `completed` 或 `indexed_resources` 能列出该资源。
  - 测试文件: `AI技术介绍.txt`, `机器学习实践.md`（以 `text/plain` / `text/markdown` 形式上传）

- AI 聊天 - Simple 模式
  - 目标: 验证 `POST /api/ai/chat` 在 `mode: "simple"` 下返回 `message`。
  - 判定依据: HTTP 200，返回 `data.message`，且 `tokens_used` / `sources` 字段存在。

- AI 聊天 - Agent 模式
  - 目标: 验证 `mode: "agent"` 时，能进行大纲生成、扩写和摘要等操作，并返回 `operations`（如存在）与 `message`。
  - 判定依据: HTTP 200，返回 `data.operations` 或 `data.message`；operations 的 `operation_type` 与请求一致。

- 知识库信息查询
  - 目标: 验证 `GET /api/ai/knowledge-base/{project_id}/info` 能返回索引统计信息。
  - 判定依据: HTTP 200，返回 `vector_count` 或 `indexed_resources`（包含已上传资源 id）。

- 知识库搜索
  - 目标: 验证 `POST /api/ai/knowledge-base/{project_id}/search` 能基于上传文档返回检索结果。
  - 判定依据: HTTP 200，`data.results` 非空，结果内含 `score` 字段且 top score > 0（经验阈值）。

---

## 验证细节与判定依据（更具体） 🔍
- HTTP 状态码
  - 创建/上传: 应为 `201 Created`。
  - 查询/搜索: 应为 `200 OK`。
  - 错误情形: 清晰的错误 JSON，含 `error` 或 `msg` 字段。

- 响应字段检查
  - `project` 对象含 `id`、`name` 等基本字段。
  - `resource` 对象含 `id`、`filename`、`file_size`、`parsing_status`。
  - `ai/chat` 返回 `data.message`（文本）、`data.tokens_used`（数值）、`data.sources`（数组）或 `data.operations`（agent 模式）。
  - `knowledge-base/search` 返回 `results` 数组，每项含 `id`/`score`/`metadata`。

- 索引成功判定
  - 测试脚本通过 `knowledge-base/info` 或 `search` 的返回值判断资源是否已被索引（若 `indexed_resources` 中含资源 id 即视为完成）。
  - 当前测试使用短等待（5s），推荐改为轮询 `knowledge-base/info` 直到 `vector_count` 增加或超时。

---

## 日志与可观测性（如何调试） 🧾
- 测试脚本会打印每个请求的 **方法 / URL / Headers / Body / Files**，以及响应的 **状态 / headers / body**（`VERBOSE=True`）。
- 失败场景示例:
  - 错误 `"Not enough segments"` —— 常见于认证失败（例如仍使用 `@jwt_required()` 而非 `@jwt_or_admin_required` 或 Token 未正确传递）。
  - 500 错误 —— 查看后端日志（Flask 控制台或 `logs`）并检查数据库事务回滚信息。

> 快速排查建议: 若上传返回 422/401 等，先检查请求 Headers 是否包含 `Authorization: Bearer <token>`，并确认后端资源路由已经使用 `jwt_or_admin_required`。

---

## 运行与复现步骤（收敛版） ▶️
1. 启动后端与依赖服务（Qdrant、Embedding/AI 服务）。
2. 激活虚拟环境并运行测试：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test/test_ai_endpoints.py
```

3. 等待脚本完成，查看终端输出的请求/响应日志。
4. 检查生成的报告文件：`AI_ENDPOINTS_TEST_REPORT_{YYYYMMDD_HHMMSS}.json`（位于 `backend/`）。

---

## 证据示例（来自最近一次测试） 📑
附带测试报告：`AI_ENDPOINTS_TEST_REPORT_20260122_214243.json`（已上传）。摘要说明：
- 总计 12 个测试用例，全部通过（100%）。
- 资源上传成功并被索引（`indexed_resources` 包含 3, 4）。
- 知识库搜索针对关键词返回 3 个结果，top score 在 0.51–0.59 区间。

以上数据证明：资源上传 → 索引 → RAG 检索 → AI 响应的整体链路在该运行中工作正常。

---

## 常见改进建议 & 下一步 🛠️
- 将固定等待替换为轮询 `knowledge-base/info` 来确认索引完成（减少 flakiness）。
- 增加更多文件格式（PDF、DOCX）与更大文件的测试覆盖。
- 在 CI 中加入本脚本（或调用子集），并在失败时自动上传报告。
- 增加断言模式（严格检查 `tokens_used` 值范围、`score` 阈值）用于回归检测。

---

## 相关文件与位置 🗂️
- 测试脚本: `test/test_ai_endpoints.py`
- 资源路由: `routes/resources.py`（已使用 `jwt_or_admin_required`）
- 认证装饰器: `auth_decorator.py`
- 测试报告: `backend/AI_ENDPOINTS_TEST_REPORT_*.json`

---

如需，我可以：
- 把这份文档保存为 `backend/AI_TESTING_DOCUMENTATION.md`（已完成）并提交一个 PR；
- 或者把脚本进一步改成 pytest 风格并加入 CI 配置（GitHub Actions）。

需要我继续做哪项？ ✅