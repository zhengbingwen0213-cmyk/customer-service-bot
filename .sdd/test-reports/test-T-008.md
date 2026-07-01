# 测试报告：T-008 SQLite Schema、演示数据与本地文件目录

**测试时间**：2026-05-24 11:52:17 CST
**Tester Agent ID**：Codex Tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户后续进入真实联调时，可以使用演示账号看到演示工单、演示 QA 和演示文档记录。 | PASS | 真实 SQLite 库 `backend/data/customer_service.db` 存在；查询到演示账号 `agent01`，`users=1`、`tickets=6`、其中 `assignee_id='user_001'` 的演示工单 `4` 条，`qa_items=3`，`documents=3`，`document_chunks=12`。 |
| 2 | 本任务不触发用户页面验收；数据落盘和检索能力由自动技术检查验证。 | PASS | 未执行页面验收；已执行初始化脚本、真实 DB 查询、FTS5 探针、上传目录写删探针、pytest、ruff、mypy 和短时后端健康检查。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `backend/src/db/models.py` 和 `backend/src/db/session.py` 基于 pycore 数据库模板扩展 | PASS | `backend/src/db/models.py:11` 使用 SQLAlchemy `DeclarativeBase` 模板形态并扩展业务模型；`backend/src/db/session.py:11`-`37` 使用 `create_async_engine`、`async_sessionmaker`、`get_db` / `get_db_context`，与 `pycore/integrations/db/session.py` 模板结构一致。 |
| 2 | 账号、工单、会话消息、QA、文档、文档切片、向量索引和基础记忆表结构覆盖 PRD 数据契约 | PASS | 真实库存在 `users`、`tickets`、`conversation_messages`、`qa_items`、`documents`、`document_chunks`、`vector_indexes`、`customer_memories`；列覆盖 PRD 要求的 ID、状态、时间、来源类型、来源 ID、维度、Embedding 模型等字段。 |
| 3 | `cd backend && PYTHONPATH=.. python3.11 scripts/init_db.py` 执行通过 | PASS | 按指定真实路径执行 `cd backend && PYTHONPATH=.. ../.venv/bin/python scripts/init_db.py`，退出码 0，输出 `SQLite database initialized`。 |
| 4 | 真实 SQLite 数据库文件存在，目标业务表和 seed 数据已落盘，不能只依赖测试夹具 | PASS | `backend/data/customer_service.db` 存在且可直接用 `sqlite3` 查询；seed 计数为 `users=1`、`customers=6`、`tickets=6`、`conversation_messages=7`、`qa_items=3`、`documents=3`、`document_chunks=12`、`vector_indexes=15`、`customer_memories=1`。 |
| 5 | SQLite FTS5 探针通过，QA 或文档关键词索引可创建和查询 | PASS | 真实库中 `qa_fts` 查询 `退款多久到账` 命中 1 条，`document_chunks_fts` 查询 `售后政策及退款流程` 命中 1 条；独立创建 `TEMP` FTS5 探针表并查询命中 1 条。 |
| 6 | `UPLOAD_DIR` 对应目录可创建、可写入、可清理测试文件 | PASS | `backend/uploads` 可创建；写入 `.__sdd_tester_upload_probe.tmp` 后读取内容为 `ok`，随后删除成功。 |
| 7 | `python3.11 -m pytest backend/tests` 通过 | PASS | 执行 `.venv/bin/python -m pytest backend/tests`，结果 `4 passed`。pytest 使用临时 SQLite 文件，未导入运行时 `engine` / `async_session_maker` 执行清表；pytest 后真实库核心表和 seed 仍存在。 |
| 8 | `python3.11 -m ruff check backend/src backend/tests` 通过 | PASS | 执行 `.venv/bin/python -m ruff check backend/src backend/tests`，结果 `All checks passed!`。 |
| 9 | `python3.11 -m mypy backend/src backend/tests` 通过 | PASS | 执行 `.venv/bin/python -m mypy backend/src backend/tests`，结果 `Success: no issues found in 19 source files`。 |

## 附加验证证据

- 短时后端启动检查：`cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 可监听；`GET /health` 返回 200，响应为统一成功格式。
- 外部服务范围：T-008 仅验证 SQLite、SQLite FTS5、本地文件存储；未涉及百炼真实调用或 SQLite 向量插件加载。
