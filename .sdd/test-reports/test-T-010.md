# 测试报告：T-010 账号登录与登录态真实闭环

**测试时间**：2026-05-24 13:51 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户在登录页输入测试账号密码并点击登录，在 VITE_USE_MOCK=false 下页面调用真实后端 API 并进入客服工作台。 | PASS | 使用后端 `8099`、前端 `5199` 启动真实联调；浏览器在 `VITE_USE_MOCK=false` 下输入测试账号后进入 `/dashboard`，页面显示“客服工作台”和当前账号。后端日志记录浏览器触发 `POST /api/auth/login 200`、`GET /api/auth/me 200`。 |
| 2 | 用户在登录页输入错误密码并点击登录，页面显示清晰的登录失败提示。 | PASS | 浏览器输入错误密码后仍停留 `/login`，错误区域显示“账号或密码错误”；后端接口返回 `401 / 用户名或密码错误 / data:null`。 |
| 3 | 用户刷新登录后的页面，仍停留在登录后的后台页面；点击退出登录后回到登录页。 | PASS | 浏览器登录后刷新 `/dashboard` 仍显示当前账号；进入 `/settings` 后点击“退出登录”回到 `/login`。后端日志记录 `GET /api/auth/me 200` 与 `POST /api/auth/logout 200`。 |
| 4 | 页面无 Mock-only 文案、Mock 账号提示或 [Mock] 标签。 | PASS | 浏览器检查登录页、工作台、刷新后的工作台、设置页和退出后的登录页可见文本，未出现 `[Mock]`、Mock 账号提示、演示账号或 Mock-only 文案。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | POST /api/auth/login、GET /api/auth/me、POST /api/auth/logout 符合 docs/api-contracts.md | PASS | curl 验证成功登录、当前用户、退出登录响应均为 `{ code, message, data }` envelope；错误密码与退出后查询返回 401 envelope。 |
| 2 | get_current_user 路由级依赖实现，受保护路由无凭证或无效凭证返回 401 统一错误格式 | PASS | `backend/src/api/deps.py` 使用 `HTTPBearer(auto_error=False)` 和 `from src.db.session import get_db`；无凭证 `GET /api/auth/me` 和退出后失效凭证访问均返回 `401 / 登录状态已失效 / data:null`。 |
| 3 | 前端 auth service 在 VITE_USE_MOCK=false 时不走 frontend/src/mocks/* 登录分支 | PASS | `frontend/src/utils/runtime.ts` 仅当 `VITE_USE_MOCK !== 'false'` 启用 Mock；`frontend/src/services/auth.ts` 在 false 时调用 `/auth/login`、`/auth/me`、`/auth/logout`。 |
| 4 | 浏览器或等价测试证明请求命中真实后端 API，而不是 Mock | PASS | 浏览器真实模式完成登录/刷新/设置/退出；后端 8099 日志记录对应 `POST /api/auth/login`、`GET /api/auth/me`、`GET /api/settings/account`、`POST /api/auth/logout` 请求。 |
| 5 | 后端 API 单元测试和集成测试通过 | PASS | `.venv/bin/python -m pytest backend/tests`：`15 passed`。 |
| 6 | Frontend typecheck、lint、build passes | PASS | `npm run type-check`、`npm run lint`、`npm run build` 均返回 0；build 输出 `✓ built`。 |
| 7 | Backend ruff、mypy、pytest passes | PASS | `.venv/bin/python -m ruff check backend/src backend/tests` 返回 `All checks passed!`；`.venv/bin/python -m mypy backend/src backend/tests` 返回 `Success: no issues found in 34 source files`；pytest 通过。 |

## 联调与环境证据

- 后端启动命令：`cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099`，服务启动并保持监听。
- 前端启动命令：`cd frontend && VITE_USE_MOCK=false VITE_API_BASE_URL=/api VITE_BACKEND_PROXY_TARGET=http://localhost:8099 npm run dev -- --host 127.0.0.1 --port 5199`。
- Vite 代理：`frontend/vite.config.ts` 配置 `/api` 代理到 `VITE_BACKEND_PROXY_TARGET`，`/ws` 配置 `ws: true`；`frontend/.env` 中 `VITE_API_BASE_URL=/api` 为相对路径。
- CORS：`http://localhost:5199`、`http://127.0.0.1:5199`、`http://localhost:5175`、`http://127.0.0.1:5175` 的 OPTIONS 预检均返回对应 `access-control-allow-origin`。
- 数据库：`backend/data/customer_service.db` 存在核心表；pytest 前后 `users.username='agent01'` 记录均存在，测试使用临时 SQLite 和 `app.dependency_overrides[get_db]`，未发现运行时库清表风险。
- 密钥安全：未在本报告、`.sdd` 或源码检查输出中复述任何真实 API Key / Token / Secret；扫描命中的 token/password/api_key 文本为契约占位、字段名或既有测试/Mock 说明。

## 超出范围发现（不影响当前任务判定）

无。
