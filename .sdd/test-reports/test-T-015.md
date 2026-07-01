# T-015 文档入库真实闭环验收报告

结论：PASS

验收时间：2026-06-25 19:50-19:54（Asia/Shanghai）

验收对象：`customer-service-bot`

## 环境

- Backend：FastAPI/uvicorn，端口 `127.0.0.1:8099`
- Frontend：Vite，端口 `127.0.0.1:5199`，`VITE_USE_MOCK=false`
- Database：SQLite `backend/data/customer_service.db`
- Upload dir：`backend/uploads`
- 认证：使用 demo 账号登录；报告不记录 access token

## 静态检查

- `docs/api-contracts.md` 3.20-3.23 覆盖 `GET /api/documents`、`POST /api/documents`、`GET /api/documents/{document_id}`、`DELETE /api/documents/{document_id}`。
- `backend/src/api/routes/documents.py` 路由前缀为 `/api/documents`，返回结构使用 `ApiEnvelope`，非法 status 映射 400，缺失文档映射 404。
- `backend/src/services/documents.py` 状态白名单为 `processing/completed/failed`；上传先保存文件和 `processing` 文档，再切片、写 chunks、尝试 embedding，成功后更新为 `completed`，解析失败更新为 `failed`。
- `backend/src/repositories/documents.py` 删除文档前删除 `document_chunk` vector，随后删除 chunks 和 document。
- `backend/src/db/models.py` 对 documents/vector_indexes 有状态/source_type check constraint，`VectorIndex.embedding_vector` 为 nullable JSON 文本。
- `backend/src/db/schema.py` 会对旧 `vector_indexes` 表自动 `ALTER TABLE` 补 `embedding_vector`，并创建 document chunks FTS5 表和触发器。
- `frontend/src/services/documents.ts` 仅当 `isMockApiEnabled()` 为真时调用 `frontend/src/mocks` 文档分支；`VITE_USE_MOCK=false` 时走真实 axios `/documents` API。
- `frontend/src/pages/DocumentsPage.vue` 未发现 `[Mock]`、Mock-only 文案或 Mock 账号提示；页面展示上传、列表、状态筛选、刷新、删除。
- 配置字段通过 settings/env 存在：`DATABASE_PATH`/`DATABASE_URL`、`UPLOAD_DIR`、`DASHSCOPE_API_KEY`、`BAILIAN_BASE_URL`、`BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS`、`SQLITE_VECTOR_EXTENSION_PATH`；未在业务代码中硬编码真实 secret。

## 命令验证

- `.venv/bin/python -m pytest backend/tests -q`
  - 结果：`22 passed`
  - 备注：仅 Pydantic deprecated warnings
- `.venv/bin/python -m ruff check backend/src backend/tests`
  - 结果：`All checks passed!`
- `.venv/bin/python -m mypy backend/src backend/tests`
  - 结果：`Success: no issues found in 50 source files`
- `cd frontend && npm run type-check`
  - 结果：exit 0
- `cd frontend && npm run lint`
  - 结果：exit 0，`eslint . --max-warnings=0`
- `cd frontend && npm run build`
  - 结果：exit 0，Vite build 成功，`125 modules transformed`

## 真实 API 验证

初始化：

- 首次直接运行 `backend/scripts/init_db.py` 因缺少 `pycore` import path 失败。
- 使用 `PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py` 成功初始化 SQLite 和 seed。
- seed 结果：`users=2`、`documents=3`、`document_chunks=12`、`vector_indexes=15`，QA/Document FTS5 probe 均命中。

API 流程一：

- 登录：`POST /api/auth/login` -> 200/200。
- 上传前列表：`GET /api/documents?keyword=T015_UNIQUE_20260625_REAL_LOOP` -> 200/total 0。
- 上传 md：`POST /api/documents` -> 200/200/success，文档 `doc_db2f87e32f47`，状态 `completed`，`chunk_count=1`。
- 详情：`GET /api/documents/doc_db2f87e32f47` -> 200，状态 `completed`，`chunk_count=1`。
- 列表筛选：`GET /api/documents?keyword=T015真实闭环&page=1&page_size=20` -> 200/total 1。
- 非法状态：`GET /api/documents?status=draft` -> 400/400，message `status 参数不合法`。
- 删除：`DELETE /api/documents/doc_db2f87e32f47` -> 200，`deleted=true`。
- 删除后列表：`GET /api/documents?keyword=T015真实闭环` -> 200/total 0。

数据库闭环流程二：

- 上传 txt：文档 `doc_710bb7fe8728`，状态 `completed`，`chunk_count=1`。
- 删除前 SQLite 抽查：
  - document 存在，`status=completed`，`chunk_count=1`
  - storage_path 文件存在
  - `document_chunks` 行数 1
  - `vector_indexes` 行数 1
  - `embedding_model=text-embedding-v4`
  - `vector_dimension=1024`
  - `embedding_vector` 可解析为 JSON 数组，长度 1024，元素类型 float
- 检索状态：
  - 百炼 Embedding 可用并写入真实 embedding 数组
  - SQLite 向量插件未配置：`SQLITE_VECTOR_EXTENSION_PATH is not configured`
  - 检索降级为 `fts5`
- 删除前检索：`KnowledgeSearchAdapter.search_documents("T015_DB_UNIQUE_20260625_VECTOR_CHECK")` 命中 `doc_710bb7fe8728`，backend `fts5`。
- 删除：`DELETE /api/documents/doc_710bb7fe8728` -> 200，`deleted=true`。
- 删除后 SQLite 抽查：
  - document 不存在
  - storage 文件不存在
  - chunks 行数 0
  - document_chunk vectors 行数 0
- 删除后检索：同关键词返回空列表。

## 浏览器/P08 验证

- 启动前端：`VITE_USE_MOCK=false npm run dev -- --host 127.0.0.1 --port 5199`。
- 打开 `http://127.0.0.1:5199/documents`，未登录时跳转 `/login?redirect=/documents`。
- 登录后进入 P08：
  - `document.documentElement.dataset.apiMode` 为 `real`
  - `document.body.innerText` 不包含 `Mock` 或 `[Mock]`
  - 页面标题为 `文档入库`
  - 初始 seed 列表展示三类状态：`处理中`、`失败`、`已完成`
- 浏览器网络请求：
  - `POST http://127.0.0.1:5199/api/auth/login` -> 200
  - `GET http://127.0.0.1:5199/api/auth/me` -> 200
  - `GET http://127.0.0.1:5199/api/documents?page=1&page_size=20` -> 200
- P08 页面上传：
  - 通过页面选择 `sdd-t015-ui-upload.md`
  - 点击上传后页面提示 `文档已加入入库任务队列`
  - 新增行 `sdd-t015-ui-upload.md`，状态 `已完成`，切片数 1，总数从 3 到 4
  - 网络请求：`POST http://127.0.0.1:5199/api/documents` -> 200
- P08 页面删除：
  - 点击新增行删除按钮后页面提示 `文档已删除`
  - `sdd-t015-ui-upload.md` 从列表消失，总数回到 3
  - 网络请求：`DELETE http://127.0.0.1:5199/api/documents/doc_936c61ecfb0f` -> 200
- 浏览器控制台：
  - 唯一错误为 `favicon.ico` 404，未影响 P08 验收。

## 清理

- 删除了 API 测试创建的 `doc_db2f87e32f47`、`doc_710bb7fe8728`。
- 通过 P08 页面删除了 UI 测试创建的 `doc_936c61ecfb0f`。
- SQLite 残留检查：
  - `t015_docs_remaining 0`
  - `t015_chunks_remaining 0`
  - `t015_vectors_remaining 0`
- 上传目录残留检查：未发现 `*t015*` 或 `sdd-t015-*` 文件。
- 清理了 `/tmp/sdd-t015-ui-upload.md` 和 Playwright 临时目录 `.playwright-cli`。
- 已关闭 Playwright browser。
- 已停止 uvicorn 和 Vite。
- `lsof -nP -iTCP:8099 -sTCP:LISTEN`：无监听。
- `lsof -nP -iTCP:5199 -sTCP:LISTEN`：无监听。

## 结论

T-015「文档入库真实闭环」验收通过。接口契约、真实前后端联调、文档上传/切片/embedding/检索/删除清理闭环、Mock 关闭行为、配置字段、自动化质量门禁均已独立验证。

降级标注：百炼 Embedding 实际可用并写入 1024 维 JSON embedding；SQLite 向量插件未配置，检索路径降级为 FTS5。
