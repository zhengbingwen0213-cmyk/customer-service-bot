# 测试报告：T-011 工单池查询、筛选与接取真实闭环

**测试时间**：2026-05-24 14:29 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户在工单池页面选择状态、优先级或输入关键词，VITE_USE_MOCK=false 下页面通过真实后端 API 展示匹配工单。 | PASS | 后端 8099 使用 `PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 启动，前端 5199 使用 `VITE_USE_MOCK=false VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8099 npm run dev -- --host 127.0.0.1 --port 5199` 启动。Playwright 网络记录显示真实请求：`GET /api/tickets?scope=pool&status=open&page=1&page_size=20` 返回 TK-1002/TK-1001，`priority=high` 返回 TK-1001，`keyword=报表` 返回 TK-1002，`status=processing` 返回空列表和 `total=0`。后端日志同步记录相同 `/api/tickets` 请求。 |
| 2 | 用户点击待接工单的接取按钮，页面显示接取成功反馈，该工单从工单池列表中移除。 | PASS | 页面点击 TK-1002 接取按钮后，网络记录 `POST /api/tickets/TK-1002/claim => 200`，响应 ticket 为 `status=processing`、`assignee_id=user_001`；页面显示 `接取成功`，当前关键词筛选列表变为 `暂无工单`、`共 0 条记录`。 |
| 3 | 用户点击已被接取的工单时，页面显示清晰的失败提示，不会误显示接取成功。 | PASS | 使用外部真实 API 先接取 TK-1001，保留页面旧列表后点击 TK-1001 接取按钮；Playwright 网络记录 `POST /api/tickets/TK-1001/claim => 400`，响应 `{"code":400,"message":"工单已被接取","data":null}`；页面显示 alert `工单已被接取`，未显示 `接取成功`。 |
| 4 | 页面无 Mock-only 文案、Mock 账号提示或 [Mock] 标签。 | PASS | Playwright 页面文本检查 `/Mock|mock|模拟账号|Mock 账号|演示账号|\\[Mock\\]/` 为 false；静态搜索 `frontend/src/pages/TicketPoolPage.vue` 未发现 Mock-only 标签或文案。 |

## 技术检查

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | GET /api/tickets 支持 scope=pool、status、priority、keyword、page、page_size，响应符合 docs/api-contracts.md | PASS | `backend/src/api/routes/tickets.py:29` 到 `backend/src/api/routes/tickets.py:59` 声明并透传这些查询参数；真实 API 脚本验证分页、状态、优先级、关键词、非法状态 400 和 TicketSummary 字段集合，13 项接口断言通过。 |
| 2 | POST /api/tickets/{ticket_id}/claim 实现待接取到处理中的状态流转，并绑定当前账号 | PASS | `backend/src/api/routes/tickets.py:62` 到 `backend/src/api/routes/tickets.py:86` 校验 `employee_id` 与当前用户一致；`backend/src/services/ticket.py:66` 到 `backend/src/services/ticket.py:85` 将 open 工单改为 processing 并写入当前用户。真实 API 返回 `assignee_id=user_001`、`assignee_name=客服一组员工`。 |
| 3 | 无凭证或无效凭证访问工单接口返回 401 统一错误格式 | PASS | 真实 API 验证：无凭证 `GET /api/tickets?scope=pool` 和无效 Bearer `POST /api/tickets/TK-1001/claim` 均返回 `{"code":401,"message":"登录状态已失效","data":null}`。 |
| 4 | 前端 tickets service 在 VITE_USE_MOCK=false 时不走 frontend/src/mocks/* 工单池分支 | PASS | `frontend/src/services/tickets.ts:31` 到 `frontend/src/services/tickets.ts:40`、`frontend/src/services/tickets.ts:55` 到 `frontend/src/services/tickets.ts:61` 仅在 `isMockApiEnabled()` 为 true 时调用 mock；`frontend/src/utils/runtime.ts` 中 `VITE_USE_MOCK === 'false'` 会关闭 Mock。真实浏览器网络记录命中 `/api/tickets` 和 `/api/tickets/{id}/claim`。 |
| 5 | 浏览器或等价测试证明请求命中真实后端 API，而不是 Mock | PASS | Playwright 网络记录包含 `GET http://127.0.0.1:5199/api/tickets...` 和 `POST http://127.0.0.1:5199/api/tickets/.../claim`；后端 8099 日志记录同一批 `GET /api/tickets`、`POST /api/tickets/TK-1002/claim 200`、`POST /api/tickets/TK-1001/claim 400`。 |
| 6 | 后端 API 单元测试和集成测试通过 | PASS | `./.venv/bin/python -m pytest backend/tests` 结果：`16 passed, 11 warnings`。 |
| 7 | Frontend typecheck、lint、build passes | PASS | `npm run type-check`、`npm run lint`、`npm run build` 均退出码 0；build 输出 `125 modules transformed`、`built in 510ms`。 |
| 8 | Backend ruff、mypy、pytest passes | PASS | `./.venv/bin/python -m ruff check backend/src backend/tests` 输出 `All checks passed!`；`./.venv/bin/python -m mypy backend/src backend/tests` 输出 `Success: no issues found in 39 source files`；pytest 通过。 |

## 规则文件与联调附加检查

- `frontend/vite.config.ts:18` 到 `frontend/vite.config.ts:30` 配置 `/api` 代理，默认 `VITE_BACKEND_PROXY_TARGET || http://localhost:8099`，并配置 `/ws` 的 `ws: true`。
- `frontend/.env` 中 `VITE_API_BASE_URL=/api` 是相对路径；本轮前端启动通过 shell 覆盖 `VITE_USE_MOCK=false`。
- 后端 CORS 预检 `Origin: http://127.0.0.1:5199` 返回 200，`access-control-allow-origin=http://127.0.0.1:5199`。
- 测试数据库隔离：`backend/tests/test_tickets.py` 使用 `tmp_path` 临时 SQLite 和 `app.dependency_overrides[get_db]`；静态搜索未发现测试对运行时库执行 `drop_all`。pytest 后真实库仍有 `users=1`、`customers=6`、`tickets=6`，最终已重新执行 `scripts/init_db.py` 恢复 TK-1001/TK-1002 为 open、未分配。
- 敏感信息检查：Developer 声明文件及 `.sdd/experience.md` 的密钥/Token/Secret 模式扫描结果为 0。

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 浏览器控制台存在外部字体资源网络波动和 favicon 404；未影响本任务真实 API、页面交互和验收结果。 | 前端静态资源 | 后续如需要可单独补 favicon 或本地化字体资源。 |
