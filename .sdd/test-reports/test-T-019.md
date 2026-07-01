# T-019 E2E 回归与 startup 文档测试报告

## 结论

- Status: PASS
- 日期：2026-06-30
- 运行模式：`VITE_USE_MOCK=false`
- 浏览器确认：`document.documentElement.dataset.apiMode === "real"`
- 临时运行库：`.sdd/tmp/t019-e2e-runtime.db`
- 临时上传目录：`.sdd/tmp/t019-uploads`
- 唯一标记：`T019_E2E_202606300216`
- 敏感信息：本报告只记录字段名、是否配置、状态、接口路径和 HTTP 状态；未记录真实 API Key、Token、密码、鉴权头、私有服务地址或可还原密钥片段。

## 产出

- 新增 `docs/startup.md`，覆盖环境要求、依赖安装、配置字段、初始化数据库、启动后端、启动前端、Mock/真实模式、外部服务与降级、验证命令、常见问题和安全说明。
- 新增本报告 `.sdd/test-reports/test-T-019.md`。
- 当前仓库 `git ls-files` 为 0，无 tracked baseline，不能用 `git diff` 独立证明变更边界。本轮产出边界通过允许文件清单、实际文件检查、临时资源清理和审查结果佐证：计划内产出为 `docs/startup.md` 与 `.sdd/test-reports/test-T-019.md`，未主动编辑前后端业务代码、接口契约、seed 或 mock 数据。

## 质量审查回补

- Important 问题：`docs/startup.md` 移除明文演示密码后，缺少新开发者可执行的安全登录准备方式。
- 修复：在演示账号附近新增“本机重置演示密码”命令，使用 `read -r -s` 静默输入、短暂环境变量传递和 Python/bcrypt 更新本机 SQLite 开发库中的 `agent01.password_hash`。
- 安全边界：命令不包含具体密码，不输出密码，不写入仓库；文档明确不要提交 `.env.local`、数据库文件或密码。
- 本次未重跑 E2E；原因是此次只修复启动文档可用性和测试报告说明，不修改运行代码、接口、seed、mock 或构建配置。

## 质量门禁

| 命令 | 结果 |
| --- | --- |
| `.venv/bin/python -m ruff check backend/src backend/tests` | PASS，`All checks passed!` |
| `.venv/bin/python -m mypy backend/src backend/tests` | PASS，`Success: no issues found in 58 source files` |
| `.venv/bin/python -m pytest backend/tests -q` | PASS，31 passed；仅有 Pydantic deprecation warnings |
| `cd frontend && npm run type-check` | PASS |
| `cd frontend && npm run lint` | PASS |
| `cd frontend && npm run build` | PASS，Vite build completed |

静态 mock import 检查：

```bash
rg -n "from ['\"]@/mocks|from ['\"]\\.\\./mocks|^import .*mock" frontend/src/services frontend/src/stores frontend/src/pages -g '*.ts' -g '*.vue'
```

结果：无输出。

## 启动与健康检查

临时 `backend/.env.local` 仅覆盖：

- `DATABASE_PATH=.sdd/tmp/t019-e2e-runtime.db`
- `UPLOAD_DIR=.sdd/tmp/t019-uploads`

初始化命令：

```bash
PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py
```

初始化结果：

- seed users: 2
- seed tickets: 7
- seed qa_items: 3
- seed documents: 3
- seed document_chunks: 12
- seed vector_indexes: 15
- FTS5 探针：QA 与文档关键字均可命中

启动命令：

```bash
PYTHONPATH=.:backend .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099 --app-dir backend
cd frontend && VITE_API_BASE_URL=/api VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8099 VITE_USE_MOCK=false npm run dev -- --host 127.0.0.1 --port 5199
```

健康检查：`GET /health` 返回 200。

## 浏览器 E2E 证据

通过 Playwright CLI 从登录页开始执行真实浏览器流程。

覆盖路径：

1. 登录 `agent01`。
2. 工作台加载 summary/tickets，并执行 quick ask。
3. 工单池接取 open 工单 `TK-1002`。
4. 进入工单详情，查看会话记录，生成并采用 AI 建议。
5. 发送带唯一标记的回复，填写处理摘要并完成工单。
6. QA 管理新增唯一标记 QA。
7. 智能问答调试页提问唯一 QA，看到 QA 答案和 `引用来源: QA`。
8. 文档入库上传唯一标记 Markdown 文档，页面显示入库完成。
9. 智能问答调试页提问唯一文档问题，看到 `引用来源: 文档` 和上传文档名。
10. Settings 页面只显示账号与配置状态，未出现敏感值形态。
11. Logout 后回到登录页；旧 token 访问 `/api/auth/me` 返回 401。

关键断言：

- `apiMode=real`
- quick ask 命中 QA 答案：`1-3 个工作日`
- 工单详情：`aiSuggestionAvailable=true`，`aiFallbackVisible=false`
- QA 调试：`containsQaAnswer=true`，`containsQaReference=true`
- 文档上传：`fileVisible=true`，`completedVisible=true`
- 文档调试：`containsDocumentReference=true`，`containsUploadedDocumentName=true`，`containsFallback=false`
- Settings：`leakIndicatorCount=0`
- Logout：`oldTokenStatus=401`
- 全流程页面检查 `[Mock]`、`Mock-only`、`Mock 账号`：均未出现

## 网络请求证据

浏览器请求捕获包含静态资源和 API 请求：

- total events: 694
- API events: 66
- static resource events: 314
- mock resource events: 0

真实后端 API 路径命中：

- `/api/auth/login`
- `/api/auth/me`
- `/api/auth/logout`
- `/api/dashboard/summary`
- `/api/dashboard/tickets`
- `/api/tickets`
- `/api/tickets/TK-1002`
- `/api/tickets/TK-1002/claim`
- `/api/tickets/TK-1002/messages`
- `/api/tickets/TK-1002/complete`
- `/api/assistant/ask`
- `/api/knowledge/qa`
- `/api/documents`
- `/api/settings/account`

静态资源证据包含前端 document、Vite client、`/src/main.ts`、依赖 chunk、字体资源等。未出现：

- `/src/mocks`
- `frontend/src/mocks`
- `mocks/*.ts`

## 外部服务与降级状态

脱敏配置状态：

- 百炼聊天：configured=true，本轮 AI 建议与文档问答无 fallback，按 live 验收。
- 百炼 Embedding：configured=true，本轮 QA 与文档入库产生对应 vector 记录。
- SQLite vector 插件：fallback。
- 检索模式：`retrieval_mode=fts5`，`keyword_backend=fts5`。
- 结论：SQLite vector fallback to FTS5/LIKE；本轮实际 keyword backend 为 FTS5。

临时库唯一标记写入验证：

- T-019 QA count: 1
- T-019 document count: 1
- T-019 document chunk count: 1
- T-019 vector count: 2

## 清理结果

已完成清理：

- Playwright 浏览器会话已关闭。
- 后端 8099 已停止。
- 前端 5199 已停止。
- `backend/.env.local` 已删除。
- `.sdd/tmp/t019-e2e-runtime.db` 及 SQLite sidecar 文件已删除。
- `.sdd/tmp/t019-uploads` 已删除。
- `.sdd/tmp/t019-upload-sample.md` 已删除。
- `.sdd/tmp/t019-e2e.playwright.js` 已删除。
- `.playwright-cli` 临时浏览器记录目录已删除；最终 `find .playwright-cli -maxdepth 2 -type f` 无输出。

端口检查：

- `lsof -nP -iTCP:8099 -sTCP:LISTEN`：无输出。
- `lsof -nP -iTCP:5199 -sTCP:LISTEN`：无输出。

## 风险与说明

- 本轮未新增 PRD / Plan / api-contracts.md 之外的业务能力。
- 本轮使用临时 SQLite DB 和临时上传目录，所有 E2E 写入均随临时资源删除。
- SQLite vector 插件未启用，已按 FTS5 fallback 记录。
- Settings 页面验证只检查页面文本，不记录接口响应中的任何敏感字段值。
- 因仓库没有 tracked baseline，报告不以 Git 作为唯一变更证明；变更边界以本报告列出的产物、清理检查和复审验证为准。
