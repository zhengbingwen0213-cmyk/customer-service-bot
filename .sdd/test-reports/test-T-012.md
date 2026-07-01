# 测试报告：T-012 我的工单与账号数据隔离真实闭环

**测试时间**：2026-05-24 15:11:43 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户打开我的工单页面，VITE_USE_MOCK=false 下页面通过真实后端 API 展示当前账号已接取或已完成的工单。 | PASS | `frontend/.env:2` 为 `VITE_USE_MOCK=false`。Playwright 通过真实前端 `http://127.0.0.1:5199/my-tickets` 进入页面，后端 8099 收到 `GET /api/tickets?scope=mine&page=1&page_size=20`，页面展示 agent01 的 TK-1005、TK-1003、TK-1004、TK-1006，均为 `user_001` 且状态为处理中或已完成。 |
| 2 | 用户切换处理中和已完成筛选，页面列表按当前账号相关工单收敛展示。 | PASS | Playwright 点击“处理中”后请求 `GET /api/tickets?scope=mine&status=processing&page=1&page_size=20`，列表为 TK-1005、TK-1003、TK-1006；点击“已完成”后请求 `GET /api/tickets?scope=mine&status=completed&page=1&page_size=20`，列表仅 TK-1004。 |
| 3 | 用户点击我的工单卡片，页面进入对应工单详情页。 | PASS | Playwright 在已完成列表点击“查看”，请求 `GET /api/tickets/TK-1004` 返回 200，页面 URL 进入 `/tickets/TK-1004`，详情展示 TK-1004 和“企业实名认证驳回咨询”。 |
| 4 | 页面无 Mock-only 文案、Mock 账号提示或 [Mock] 标签。 | PASS | Playwright 检查 `/my-tickets` 与 `/tickets/TK-1004` 页面正文，未发现 `[Mock]`、`Mock`、Mock 账号提示或“演示数据”。`TicketDetailPage.vue:93` 在真实模式直接跳过 Mock 会话/AI 分支，`TicketDetailPage.vue:296` 的 Mock badge 仅在 `isMockMode` 时展示。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | GET /api/tickets 支持 scope=mine 并按当前认证账号过滤，不返回跨员工工单 | PASS | 先登录 agent01 保留旧 token，再登录 agent02；agent01 旧 token 调 `/api/auth/me` 仍解析为 `user_001`，`scope=mine` 返回 TK-1005、TK-1003、TK-1004、TK-1006，不含 TK-2001；agent02 `scope=mine` 仅返回 TK-2001。`backend/src/services/auth.py:28` 为每次登录生成唯一 token，`backend/tests/test_tickets.py:69` 覆盖双账号旧 token 隔离。 |
| 2 | GET /api/tickets/{ticket_id} 对当前账号不可见的工单返回 403 或符合契约的错误 | PASS | agent01 旧 token 请求 `/api/tickets/TK-2001` 返回 HTTP 403、`code=403`、`message=无权查看该工单`；agent02 请求 `/api/tickets/TK-1005` 同样返回 403。 |
| 3 | 前端 tickets service 在 VITE_USE_MOCK=false 时不走 frontend/src/mocks/* 我的工单分支 | PASS | `frontend/src/services/tickets.ts:31`、`:47` 仅在 `isMockApiEnabled()` 为真时调用 `mockGetTickets` / `mockGetTicketDetail`；真实模式走 `api.get('/tickets')` 和 `api.get('/tickets/{id}')`。`TicketDetailPage.vue:93` 真实模式不调用 Mock 消息/AI 分支。 |
| 4 | 浏览器或等价测试证明请求命中真实后端 API，而不是 Mock | PASS | 后端 8099 日志记录真实请求：`GET /api/tickets?scope=mine...`、`GET /api/tickets?scope=mine&status=processing...`、`GET /api/tickets?scope=mine&status=completed...`、`GET /api/tickets/TK-1004`。Playwright 捕获的前端网络响应均为 `/api/tickets*` 200。 |
| 5 | 后端 API 单元测试和集成测试通过 | PASS | `.venv/bin/python -m pytest backend/tests`：16 passed，11 warnings（warnings 来自 pycore/Pydantic deprecation，范围外且不影响本任务）。 |
| 6 | Frontend typecheck、lint、build passes | PASS | `npm run type-check`、`npm run lint`、`npm run build` 均退出码 0；build 输出 `dist/index.html` 与前端资源。 |
| 7 | Backend ruff、mypy、pytest passes | PASS | `.venv/bin/python -m ruff check backend/src backend/tests`：All checks passed；`.venv/bin/python -m mypy backend/src backend/tests`：Success；`.venv/bin/python -m pytest backend/tests`：16 passed。 |

## 上轮 FAIL 复验

| # | 上轮问题 | 本轮结果 | 证据 |
|---|----------|----------|------|
| 1 | agent02 登录后覆盖 agent01 固定 token 映射，agent01 旧 token 查询 `scope=mine` 返回 user_002/TK-2001。 | PASS | 本轮真实接口验证：agent01 旧 token 在 agent02 登录后 `/api/auth/me` 仍为 `user_001`，`scope=mine` 只返回 user_001 的 4 条工单；agent02 只返回 TK-2001。 |
| 2 | `frontend/.env` 默认仍为 `VITE_USE_MOCK=true`。 | PASS | `frontend/.env` 当前为 `VITE_API_BASE_URL=/api`、`VITE_USE_MOCK=false`、`VITE_BACKEND_PROXY_TARGET=http://localhost:8099`。 |

## 环境与联调证据

| 项目 | 结果 | 证据 |
|---|---|---|
| 后端真实启动 | PASS | `cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 启动成功并保持监听。 |
| 前端真实启动 | PASS | `cd frontend && npm run dev -- --host 127.0.0.1 --port 5199` 启动成功，使用 `.env` 默认 `VITE_USE_MOCK=false`。 |
| SQLite seed | PASS | `PYTHONPATH=.. ../.venv/bin/python scripts/init_db.py` 后 `users=2`、`tickets=7`；真实库包含 TK-1003/TK-1004/TK-1005/TK-1006(user_001) 与 TK-2001(user_002)。 |
| Vite 代理 | PASS | `frontend/vite.config.ts:20` 配置 `/api` 代理，`frontend/vite.config.ts:25` 配置 `/ws` 且 `ws: true`；`frontend/.env:1` 使用相对路径 `/api`，默认代理目标为 `http://localhost:8099`。 |
| CORS | PASS | OPTIONS `/api/tickets` 对 `http://localhost:5199`、`http://127.0.0.1:5199`、`http://localhost:5175`、`http://127.0.0.1:5175` 均返回 200 并回显对应 Origin。 |
| 测试数据库隔离 | PASS | `backend/tests/test_auth.py`、`backend/tests/test_tickets.py` 使用 `tmp_path` 测试 SQLite、`create_async_engine` 与 `app.dependency_overrides[get_db]`；pytest 后真实业务库仍有 users/customers/tickets 表和 7 条工单 seed。 |
| 敏感信息与 HTTP 客户端 | PASS | 未在报告或日志中打印真实 token；扫描命中为契约占位、Mock 值、字段名或测试值。`backend/src/services/ai_gateway.py` 使用 `httpx.AsyncClient(trust_env=False)`，未发现裸 `httpx.get/post`。 |
