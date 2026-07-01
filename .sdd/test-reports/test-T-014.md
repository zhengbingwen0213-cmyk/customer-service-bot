# 测试报告：T-014 知识库总览与 QA 管理真实闭环

**测试时间**：2026-06-25 18:47:30 CST
**Tester Agent ID**：Codex Tester Agent
**项目路径**：`/Users/bingsmacbook/Documents/个人/AI coding2/智能客服/SDD_V7_1/Projects_Repo/customer-service-bot`

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户打开知识库总览，`VITE_USE_MOCK=false` 下页面通过真实后端 API 展示 QA 数量、文档数量、最近更新时间和最近知识。 | PASS | `frontend/.env` 为 `VITE_USE_MOCK=false`、`VITE_API_BASE_URL=/api`；`frontend/src/services/knowledge.ts:30-50` 在非 Mock 时调用 axios 实例。Playwright 打开 `http://127.0.0.1:5199/knowledge`，请求命中 `GET /api/knowledge/overview`、`GET /api/knowledge/recent?limit=5`，均 200；页面显示 QA 数量 3、启用 2、文档数量 3、已完成 1、最近更新和最近知识列表。 |
| 2 | 用户在 QA 库管理页新增一条 QA，保存后列表出现新 QA，并且知识库总览数量随之更新。 | PASS | Playwright 在 P07 新增 `T014-联调新增-QA-20260625`，请求命中 `POST /api/knowledge/qa` 200，随后 `GET /api/knowledge/qa?page=1&page_size=20` 200；列表显示新增 QA、总数 4。返回 P06 后 `GET /api/knowledge/overview`、`GET /api/knowledge/recent?limit=5` 200，页面显示 QA 数量 4、启用 3，最近知识首条为新增 QA。 |
| 3 | 用户编辑、启停或删除 QA 后，当前页面列表展示更新结果。 | PASS | Playwright 编辑同一 QA 为 `T014-联调编辑停用-QA-20260625` 且状态 `disabled`，请求命中 `PUT /api/knowledge/qa/qa_9847ab4208b9` 200，列表显示新问题和“停用”。随后点击删除，命中 `DELETE /api/knowledge/qa/qa_9847ab4208b9` 200，列表恢复 3 条；数据库确认 `T014-%` QA 记录数为 0，关联 `vector_indexes` 记录数为 0。 |
| 4 | 页面无 Mock-only 文案、Mock 账号提示或 `[Mock]` 标签。 | PASS | `rg "\[Mock\]\|Mock-only\|Mock 账号"` 检查 P06/P07 页面未命中；Playwright 快照中 P06/P07 可见文案未出现 `[Mock]`、Mock-only 或 Mock 账号提示。 |

## 技术检查

| 检查项 | 结果 | 证据 |
|---|---|---|
| API 契约 3.14-3.19 | PASS | `backend/src/models/knowledge.py:15-70` 字段对齐 overview/recent/qa/list/create/update/delete 响应；`backend/src/api/routes/knowledge.py:32-149` 提供 `GET /overview`、`GET /recent`、`GET /qa`、`POST /qa`、`PUT /qa/{qa_id}`、`DELETE /qa/{qa_id}`，返回 `ApiEnvelope`。 |
| knowledge route 注册 | PASS | `backend/src/main.py:19` 导入 `knowledge_router`，`backend/src/main.py:46` `server.include_router(knowledge_router)`。 |
| 前端真实 axios | PASS | `frontend/src/services/knowledge.ts:30-104` 仅 `isMockApiEnabled()` 为 true 时走 mock；`frontend/src/utils/runtime.ts:1-3` 明确 `VITE_USE_MOCK=false` 时返回 false；真实分支使用 `api.get/post/put/delete`。 |
| Vite 代理与相对路径 | PASS | `frontend/vite.config.ts:18-30` 配置 `/api` 与 `/ws` 代理，默认目标 `http://localhost:8099`；`frontend/.env:1-3` 使用 `/api` 相对路径和 `VITE_USE_MOCK=false`。 |
| 分层依赖 | PASS | 当前知识库调用链为 Route -> Service -> Repository -> ORM；未发现 Repository 反向依赖 Service/Route，也未发现页面内直接 axios 调用知识库接口。 |
| 无硬编码密钥 | PASS | Developer 修改文件未发现真实 Key/Token；外部服务密钥通过 `backend/src/core/config.py` 字段加载。全仓敏感扫描仅命中 `docs/api-contracts.md` 示例 `Bearer access_token_demo` 和历史测试报告说明，未发现真实可还原密钥。 |
| 百炼 Embedding | PASS / live | 配置探针：`DASHSCOPE_API_KEY configured=True`、`BAILIAN_BASE_URL configured=True`、`BAILIAN_EMBEDDING_MODEL configured=True`、`BAILIAN_EMBEDDING_DIMENSIONS=1024`。真实新增/编辑 QA 过程中生成并更新 `vector_indexes` metadata；删除后关联 vector metadata 被清理。未输出真实 Key。 |
| SQLite vector / FTS5 边界 | PASS / fallback | `SQLITE_VECTOR_EXTENSION_PATH configured=False`，`sqlite_vector_status=fallback`；检索状态为 `keyword_backend=fts5`、`retrieval_mode=fts5`。本轮不宣称 SQLite 向量插件完整联调通过。 |

## 命令验证

| 命令 | 退出码 | 完整输出摘要 |
|---|---:|---|
| `python3.11 --version` | 127 | 本机无 `python3.11` 命令：`zsh:1: command not found: python3.11`。因此使用项目根 `.venv/bin/python` 继续执行等价验证。 |
| `.venv/bin/python --version` | 0 | `Python 3.12.12` |
| `.venv/bin/python -m ruff check backend/src backend/tests` | 0 | `All checks passed!` |
| `.venv/bin/python -m mypy backend/src backend/tests` | 0 | `Success: no issues found in 44 source files` |
| `.venv/bin/python -m pytest backend/tests` | 0 | `18 passed, 11 warnings in 2.12s`；warnings 均为 pycore/Pydantic deprecation，不影响当前任务。 |
| `npm run type-check` | 0 | `vue-tsc --noEmit -p tsconfig.app.json` 通过，无错误输出。 |
| `npm run lint` | 0 | `eslint . --max-warnings=0` 通过，无错误输出。 |
| `npm run build` | 0 | `vue-tsc --noEmit -p tsconfig.app.json && vite build` 通过；`125 modules transformed`，生成 `dist/index.html`、CSS、JS。 |

## 真实联调记录

- 后端启动命令：`cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099`，启动成功并监听 `http://127.0.0.1:8099`。
- 前端启动命令：`cd frontend && npm run dev -- --host 127.0.0.1 --port 5199`，Vite 启动成功并监听 `http://127.0.0.1:5199/`。
- 浏览器网络证据：
  - P06 初始：`GET /api/knowledge/overview` 200，`GET /api/knowledge/recent?limit=5` 200。
  - P07 初始：`GET /api/knowledge/qa?page=1&page_size=20` 200。
  - 新增：`POST /api/knowledge/qa` 200，随后 `GET /api/knowledge/qa?page=1&page_size=20` 200。
  - 编辑/启停：`PUT /api/knowledge/qa/qa_9847ab4208b9` 200，随后列表刷新 200。
  - 删除：`DELETE /api/knowledge/qa/qa_9847ab4208b9` 200，随后列表刷新 200。
  - 清理后 P06：`GET /api/knowledge/overview` 200，`GET /api/knowledge/recent?limit=5` 200，页面恢复 QA 数量 3、启用 2。

## 测试数据库隔离

- pytest 前真实业务库 `backend/data/customer_service.db` 核心 seed：`users=2`、`qa_items=3`、`documents=3`、`tickets=7`；用户包含 `agent01`、`agent02`。
- 静态检查 `backend/tests` 未发现导入运行时 `engine` / `async_session_maker` 后执行 `drop_all` 或清空运行时业务库；`backend/tests/test_knowledge.py:29-46` 使用 `tmp_path` SQLite 和 `app.dependency_overrides[get_db]`。
- pytest 后真实业务库仍为 `users=2`、`qa_items=3`、`documents=3`、`tickets=7`；用户仍包含 `agent01`、`agent02`。
- 联调新增数据已清理：`qa_items WHERE question LIKE 'T014-%'` 为 0，测试 QA 的 `vector_indexes` 为 0。

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|--------------|
| 1 | Playwright CLI 直接操作登录页时，`POST /api/auth/login` 与 `GET /api/auth/me` 均显示 200，但 localStorage 未保留登录态，页面仍停留在 `/login`；使用浏览器上下文调用真实登录 API 写入同一 localStorage 后，P06/P07 正常放行并完成真实联调。后端 curl 登录只输出布尔状态，确认真实登录 API 返回成功且有 token。 | F01 登录页/登录态 | 建议后续单独复查登录页 UI 提交流程或 Playwright CLI 表单交互兼容性；该现象不在 T-014 acceptanceCriteria 内，未作为本任务 FAIL。 |
