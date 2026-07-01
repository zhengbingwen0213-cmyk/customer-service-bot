# 测试报告：T-013 工单详情、会话回复与完成工单真实闭环

**测试时间**：2026-06-25 18:19:16 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户打开已接取工单详情页，VITE_USE_MOCK=false 下页面通过真实后端 API 展示工单信息和会话记录。 | PASS | 前端 `.env` 默认真实模式；Playwright 打开 `http://127.0.0.1:5199/tickets/TK-1005` 后展示 TK-1005 基础信息、真实会话记录和当前账号。网络请求命中 `GET /api/tickets/TK-1005` 与 `GET /api/tickets/TK-1005/messages`，均返回 200。 |
| 2 | 用户在回复编辑器输入内容并点击发送，页面会话列表新增员工回复气泡。 | PASS | Playwright 在回复编辑器输入“页面联调回复：已核实订单状态，请稍后刷新会员权益。”并点击发送，页面新增“客服一组员工”回复气泡并显示“回复已发送”。网络请求命中 `POST /api/tickets/TK-1005/messages` 200。 |
| 3 | 用户点击完成工单并填写处理摘要，页面显示工单状态已完成。 | PASS | 页面新增处理摘要输入框；填写“页面联调完成：已回复客户并记录处理结论。”后点击完成工单，页面状态变为“已完成”，显示完成时间并禁用回复编辑器。网络请求命中 `POST /api/tickets/TK-1005/complete` 200。 |
| 4 | 页面无 Mock-only 文案、Mock 账号提示或 [Mock] 标签。 | PASS | Playwright 快照中的 P05 页面无 `[Mock]`、Mock 账号提示或 Mock-only 标签；真实模式下 AI 建议面板不展示，T-017 再补齐 AI 建议与引用真实闭环。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | GET /api/tickets/{ticket_id}、GET /api/tickets/{ticket_id}/messages、POST /api/tickets/{ticket_id}/messages、POST /api/tickets/{ticket_id}/complete 符合 docs/api-contracts.md | PASS | 后端新增 DTO、Repository、Service、Route；curl 验证消息列表、发送回复、完成工单和完成后详情响应均为统一 envelope。 |
| 2 | 只能完成当前账号已接取的工单；无权限返回 403 统一错误格式 | PASS | `backend/tests/test_tickets.py` 覆盖 agent01 访问/完成 TK-2001 返回 403，响应为统一 `{code,message,data}` 格式。 |
| 3 | 会话消息按时间顺序展示，发送方枚举只使用 customer / employee / bot | PASS | 单测断言 TK-1005 初始消息顺序为 customer、bot、customer；新增员工回复 sender 为 employee；Repository 按 `created_at asc, id asc` 排序。 |
| 4 | 前端 tickets service 在 VITE_USE_MOCK=false 时不走 frontend/src/mocks/* 工单详情、消息或完成分支 | PASS | `frontend/src/services/tickets.ts` 中 `getTicketMessages`、`sendTicketMessage`、`completeTicket` 仅在 `isMockApiEnabled()` 为 true 时走 mock，真实模式走 axios API。 |
| 5 | 浏览器或等价测试证明请求命中真实后端 API，而不是 Mock | PASS | Playwright 网络记录：`GET /api/tickets/TK-1005`、`GET /api/tickets/TK-1005/messages`、`POST /api/tickets/TK-1005/messages`、`POST /api/tickets/TK-1005/complete` 均为 200。后端 8099 日志同步记录真实请求。 |
| 6 | 后端 API 单元测试和集成测试通过 | PASS | `./.venv/bin/python -m pytest backend/tests`：16 passed，11 warnings（warnings 为既有 pycore/Pydantic deprecation）。 |
| 7 | Frontend typecheck、lint、build passes | PASS | `npm run type-check`、`npm run lint`、`npm run build` 均通过；build 输出 `dist/index.html` 与前端资源。 |
| 8 | Backend ruff、mypy、pytest passes | PASS | `./.venv/bin/python -m ruff check backend/src backend/tests`：All checks passed；`./.venv/bin/python -m mypy backend/src backend/tests`：Success；pytest 通过。 |

## 环境与联调证据

| 项目 | 结果 | 证据 |
|---|---|---|
| RED 测试 | PASS | 先新增 T-013 后端测试，初次运行 `backend/tests/test_tickets.py` 在 `GET /api/tickets/TK-1005/messages` 返回 404 处失败，确认测试覆盖缺失接口。 |
| 后端真实启动 | PASS | `cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 启动成功；`GET /health` 返回 200。 |
| 前端真实启动 | PASS | `cd frontend && npm run dev -- --host 127.0.0.1 --port 5199` 启动成功，Vite 代理 `/api` 命中后端 8099。 |
| 浏览器真实路径 | PASS | Playwright 页面展示真实工单详情、会话、回复新增和完成状态；网络请求均为 `/api/tickets*`。 |
| 测试数据库隔离 | PASS | 后端测试继续使用 `tmp_path` 临时 SQLite 与 `app.dependency_overrides[get_db]`；pytest 后运行时业务库仍有 users/tickets/conversation_messages 核心数据。 |
| 本地联调数据恢复 | PASS | 浏览器/curl 验证后已删除手工新增回复，并将 TK-1005 恢复为 processing，运行时库保留 3 条原始 TK-1005 会话。 |

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 浏览器直接从登录页点击登录时，后端登录成功且 `/api/auth/me` 成功，但页面未自动跳转；本轮通过写入同源 localStorage 后打开详情页完成 T-013 验证。 | 登录页/路由体验 | 后续可单独检查登录页 redirect 处理，不影响 T-013 的 P05 真实闭环。 |
| 2 | 本地 `.venv` / `node_modules` 带 `com.apple.provenance` 时，ruff、mypy、vue-tsc、uvicorn 首次启动可能很慢或被系统拦截；移除项目本地依赖目录隔离属性后验证通过。 | 本地开发环境 | 若再次出现，可对项目本地 `.venv` 和 `frontend/node_modules` 清理隔离属性或重建依赖。 |
