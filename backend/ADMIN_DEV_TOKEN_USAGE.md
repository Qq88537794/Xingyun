# 管理员开发用 Token（ADMIN_DEV_TOKEN）说明文档

## 概要
该文档描述我们为方便本地/开发测试引入的“管理员开发用 Token”（`ADMIN_DEV_TOKEN`）的变更内容、使用方法、对现有认证流程的影响及安全建议。

---

## 一、变更摘要 🔧
- 新建/修改文件:
  - `auth_decorator.py`：新增 `jwt_or_admin_required` 装饰器；新增 `ensure_admin_user()` 与 `get_current_user_id()` 辅助函数。
  - `routes/resources.py`, `routes/projects.py`, `routes/ai_v2.py` 等路由：将原先依赖 `@jwt_required()` 的路由替换为 `@jwt_or_admin_required`，以支持管理员 Token。
  - `test/test_ai_endpoints.py`：测试脚本使用管理员 Token (`ADMIN_TOKEN`) 进行端到端验证（项目创建、文件上传、索引、检索、AI 接口）。

- 目标：在开发/测试环境下，使用一个固定的开发管理员 Token 来简化测试流程（无需先生成 JWT），同时保留正常 JWT 验证逻辑用于真实用户。

---

## 二、工作原理（如何生效） ⚙️
- 装饰器 `jwt_or_admin_required` 在每次请求时检查 `Authorization` header：
  1. 若 header 等于 `Bearer <ADMIN_DEV_TOKEN>`（从环境变量读取），则：
     - 标记 `request.admin_mode = True`
     - 调用 `ensure_admin_user()` 确保名为 `admin_dev` 的用户存在（若不存在则自动创建），并设置 `request.current_user_id` 为该管理员用户的 ID
     - 直接通过授权，执行视图函数
  2. 否则，继续执行标准 JWT 检查（`verify_jwt_in_request()`）；通过则 `request.current_user_id = get_jwt_identity()` 并执行视图
  3. 若两种方式都失败，则返回 401 错误

- `get_current_user_id()`：统一获取当前用户 ID（支持 admin token 或 JWT）—路由中使用它来替代直接调用 `get_jwt_identity()`。

- `ensure_admin_user()`：会在数据库中创建一个用户名为 `admin_dev` 的用户（默认密码 `admin123`，仅用于本地测试），并返回其 user id。

---

## 三、怎么使用（示例） 🧪
1. 在开发环境的 `.env` 中加入：

```
ADMIN_DEV_TOKEN=dev-admin-token-2026-xingyun
```

2. 以 curl 上传文件的示例（项目 ID 假设为 3）：

```bash
curl -H "Authorization: Bearer dev-admin-token-2026-xingyun" \
  -F "file=@AI技术介绍.txt" \
  http://127.0.0.1:5000/api/projects/3/resources
```

3. 使用测试脚本（示例）：
- `test/test_ai_endpoints.py` 已配置 `ADMIN_TOKEN = "dev-admin-token-2026-xingyun"`，直接运行脚本即可：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test/test_ai_endpoints.py
```

---

## 四、对正常用户登录/功能的影响 ✅/⚠️
- 正常用户（使用 JWT）不受影响：
  - 若请求带标准 JWT，则 `jwt_or_admin_required` 会通过 `verify_jwt_in_request()` 继续执行原有验证流程，行为与之前一致。

- 管理员开发 Token 的行为：
  - 使用 `ADMIN_DEV_TOKEN` 的请求会被视为以 `admin_dev` 用户身份进行；因此会绕过需要事先获取 JWT 的步骤（便于自动化测试与本地调试）。
  - 这意味着请求将以 `admin_dev` 的权限执行（请确保 `admin_dev` 的权限范围合适且仅用于开发环境）。

- 潜在副作用：
  - 日志与审计：使用管理员 Token 的操作会以 `admin_dev` 用户身份出现在审计日志中，应注意区分测试活动与真实用户操作。
  - 自动创建用户：首次使用管理员 Token 时会在数据库创建 `admin_dev` 用户（需接受该数据库变更）。

---

## 五、安全注意事项与建议 🔒
- 该 Token 仅应在本地或受控的开发环境中使用；**不要**在生产环境中设置或启用。
- 切勿将 `ADMIN_DEV_TOKEN` 写入版本控制（.env 应列入 .gitignore）；若不慎泄露，应立即更换并在系统中撤销。
- 可选限制：通过环境配置进一步限定该 token 仅在 `FLASK_ENV=development` 时生效，或限制来源 IP 列表以降低风险。
- 建议在密钥管理上与团队约定：周期性更换、记录使用者/用途、并在 CI/CD 的 secret 管理中集中管理（如果需要在 CI 使用，建议生成专用临时 token）。

---

## 六、如何撤销或禁用
- 立即撤销：从环境中删除 `ADMIN_DEV_TOKEN` 并重启后端（或清空其值），`jwt_or_admin_required` 将不再匹配该 header。
- 删除自动创建的测试用户（可选）：在数据库中删除 `admin_dev` 用户或将其禁用。

---

## 七、测试与验证
- 已将测试脚本 `test/test_ai_endpoints.py` 更新为使用 `ADMIN_TOKEN` 以验证：
  - 项目创建、资源上传、索引、AI 问答、知识库检索等流程
- 最近一次测试报告：`backend/AI_ENDPOINTS_TEST_REPORT_20260122_214243.json`（所有用例通过）。

---

## 八、需要注意的问题 / 已知限制
- 如果某些路由仍使用 `@jwt_required()`（遗留），管理员 Token 请求会返回 401 或类似错误；请确保所有需要支持管理员测试的路由已替换为 `@jwt_or_admin_required`。
- admin 用户密码是默认的开发密码（`admin123`），仅用于本地测试；在任何长期环境中应禁用或修改。

---

如需，我可以：
- 把所有受影响的路由列出并创建变更清单 PR；
- 为 CI 创建一个临时的、只能在 CI 环境使用的管理员 token 流程并写入文档。

请选择你接下来想要的操作。