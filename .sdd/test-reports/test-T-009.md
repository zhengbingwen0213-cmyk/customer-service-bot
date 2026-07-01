# 测试报告：T-009 百炼网关、Embedding 网关与向量插件适配

**测试时间**：2026-05-24 12:21:38 CST
**Tester Agent ID**：Codex Tester Agent

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户后续在设置页只能看到模型和检索配置是否可用的状态，不会看到真实 API Key 或可还原密钥片段。 | PASS | `frontend/src/pages/SettingsPage.vue` 仅展示模型名、Embedding 维度和 `api_key_configured` 布尔状态；`backend/src/core/config.py` 对 `dashscope_api_key` 使用 `repr=False`；smoke 输出只包含 live/fallback、模型名和响应结构。密钥扫描显示真实配置只存在于允许的本地 `.env.local`，排除允许的 `.env*` 后未发现真实 Key 的完整值或可还原片段泄露。 |
| 2 | 当向量插件不可用时，用户后续使用问答功能仍能看到清晰的降级状态，而不是静默失败。 | PASS | `backend/src/services/retrieval.py` 在 `SQLITE_VECTOR_EXTENSION_PATH` 未配置时返回 `status=fallback`、`fallback_reason` 和 `keyword_backend`；smoke 实测输出 `SQLite vector plugin: fallback`、`fallback: FTS5 / LIKE`、`reason: SQLITE_VECTOR_EXTENSION_PATH is not configured`。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|------|------|------|
| 1 | 百炼聊天模型配置字段仅从 `DASHSCOPE_API_KEY`、`BAILIAN_BASE_URL`、`BAILIAN_CHAT_MODEL` 读取，代码和文档不硬编码真实密钥 | PASS | `backend/src/services/ai_gateway.py` 的 `is_chat_configured()` 只检查 Key、Base URL、Chat model；`.env.example` 只保留字段名/默认值，未硬编码真实密钥。 |
| 2 | 百炼 Embedding 配置字段仅从 `DASHSCOPE_API_KEY`、`BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS` 读取 | PASS | `is_embedding_configured()` 只检查这三项；Embedding 配置错误提示只列这三项；`backend/tests/test_ai_gateway.py` 覆盖 `BAILIAN_BASE_URL` 为空时 Embedding 仍 configured，并验证错误提示不包含 `BAILIAN_BASE_URL`。`.sdd/experience.md` 已表述 `BAILIAN_BASE_URL` 只能作为百炼网关公共默认 endpoint。 |
| 3 | 禁止使用百炼官方 SDK；必须通过 `httpx.AsyncClient(trust_env=False)` 调用 HTTP / OpenAI 兼容接口 | PASS | `rg` 未发现 `dashscope` SDK、OpenAI SDK 或裸 `httpx.get/post`；`backend/src/services/ai_gateway.py` 使用 `httpx.AsyncClient(trust_env=False)`。 |
| 4 | 如果本地百炼配置可用，聊天模型和 Embedding smoke test 通过；如果不可用，测试报告标记 Mock/fallback 验收，不得宣称真实服务联调通过 | PASS | 本地配置可用。执行 `cd backend && PYTHONPATH=.. ../.venv/bin/python scripts/smoke_ai_gateways.py --strict` 返回 0；输出显示 `Bailian chat: live` 和 `Bailian embedding: live`。 |
| 5 | SQLite 向量插件加载探针可运行；插件不可用时自动降级为 FTS5 / LIKE 检索并在状态中标注 | PASS | smoke 输出 `SQLite vector plugin: fallback` 与 `FTS5 / LIKE`；`backend/tests/test_retrieval_adapter.py` 覆盖缺插件时 FTS5 和 LIKE 降级路径。 |
| 6 | 外部服务调用失败时有清晰错误处理和日志，不得静默吞错 | PASS | `backend/src/services/ai_gateway.py` 对 HTTP 异常、非 JSON、HTTP 4xx/5xx、异常响应结构和维度不匹配均抛出明确错误；测试覆盖 401 和维度不匹配路径。 |
| 7 | `python3.11 -m pytest backend/tests` 通过 | PASS | 执行 `.venv/bin/python -m pytest backend/tests`：`14 passed, 11 warnings in 0.40s`。 |
| 8 | `python3.11 -m ruff check backend/src backend/tests` 通过 | PASS | 执行 `.venv/bin/python -m ruff check backend/src backend/tests backend/scripts/smoke_ai_gateways.py`：`All checks passed!`。 |
| 9 | `python3.11 -m mypy backend/src backend/tests` 通过 | PASS | 执行 `.venv/bin/python -m mypy backend/src backend/tests`：`Success: no issues found in 24 source files`。 |

## 补充验证

- 后端真实路径验证：执行 `cd backend && PYTHONPATH=.. ../.venv/bin/python scripts/init_db.py` 成功，seed counts 为 `users=1`、`tickets=6`、`qa_items=3`、`documents=3`、`document_chunks=12`、`vector_indexes=15`。
- 短时服务启动：执行 `cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099`，`GET /health` 返回 `code=200`；验证后 8099 无残留监听进程。
- pytest 后业务库隔离复查：`backend/data/customer_service.db` 中核心表仍存在，`agent01` seed 用户仍存在，`qa_fts` 和 `document_chunks_fts` 仍存在。
- 测试隔离静态检查：`backend/tests` 未发现对运行时 `engine` / `async_session_maker` 执行 `drop_all` 或清表；检索和 DB 初始化测试使用 `tmp_path` 下独立 SQLite 文件。
- 密钥扫描：扫描项目可读源码、文档和 `.sdd` 产物，排除允许的 `.env*` 本地配置文件后，未发现真实 API Key、Token、Secret 的完整值或可还原片段泄露；命中的 token/password/api_key 字样均为占位、Mock 值、字段名或 pycore 示例。
