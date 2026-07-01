# T-019 E2E 回归与 startup 文档执行计划

> **Planner 结论**：可执行。T-013 到 T-018 均已 PASS，T-019 应定位为最终全链路回归和启动文档收口，不替代前序任务的首次真实联调，不新增 PRD / Plan / api-contracts.md 之外的业务能力。

## 1. 已阅读依据

- `.sdd/tasks.json` 中 T-019 任务块：要求覆盖登录、工作台、工单池接单、工单详情、AI 建议、发送回复、完成工单、QA 维护、文档入库、智能问答调试、settings/logout，并生成 `docs/startup.md`。
- `docs/Plan.md`：阶段 4 只要求跑通“登录 -> 接单 -> AI 建议 -> 回复 -> 完成工单 -> 维护知识 -> 调试验证”并输出 startup 文档；每个功能真实联调应已在阶段 3 完成。
- `docs/api-contracts.md`：最终 E2E 必须使用既有接口清单 `/health`、`/api/auth/*`、`/api/dashboard/*`、`/api/tickets*`、`/api/assistant/ask`、`/api/knowledge/*`、`/api/documents*`、`/api/settings/account`，不得新增接口或扩展业务字段。
- `.sdd/test-reports/test-T-013.md` 到 `test-T-018.md`：前序闭环均 PASS；其中 T-017/T-018 已证明临时 SQLite DB、`VITE_USE_MOCK=false`、无 `/src/mocks` 网络命中是更稳妥的最终回归方式。
- `.sdd/experience.md` T-013 到 T-018：重点经验是临时运行库隔离、测试数据唯一标记与清理、settings 脱敏、mock 动态 import 与浏览器网络检查、SQLite vector 不可用时仅可标注 FTS5 / LIKE fallback。

## 2. 当前 startup 文档状态

- 检查结果：`docs/startup.md` 当前不存在。
- Developer 应创建 `docs/startup.md`，建议章节结构如下：
  - `# 启动指南`
  - `## 环境要求`：Python 3.12、Node.js/npm、SQLite、本地文件写入权限、可选百炼与 Embedding 调用权限、可选 SQLite vector 插件。
  - `## 依赖安装`：后端虚拟环境与 `backend/requirements.txt`，前端 `npm install`。
  - `## 配置字段`：只列字段名和用途，不写真实值；包括 `DATABASE_PATH` / `DATABASE_URL`、`UPLOAD_DIR`、`DASHSCOPE_API_KEY`、`BAILIAN_BASE_URL`、`BAILIAN_CHAT_MODEL`、`BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS`、`SQLITE_VECTOR_EXTENSION_PATH`、`VITE_API_BASE_URL`、`VITE_USE_MOCK`、`VITE_BACKEND_PROXY_TARGET`。
  - `## 初始化数据库`：说明运行 `PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py`，以及该命令会初始化 demo seed、FTS5 索引和上传目录探针。
  - `## 启动后端`：说明从项目根或 backend 目录启动 uvicorn，推荐命令需与现有报告一致。
  - `## 启动前端`：说明 `cd frontend && VITE_USE_MOCK=false npm run dev -- --host 127.0.0.1 --port 5199`；如使用 Vite 代理，`VITE_API_BASE_URL=/api`，`VITE_BACKEND_PROXY_TARGET` 指向后端。
  - `## Mock 模式与真实模式`：说明 `VITE_USE_MOCK=false` 时页面应命中真实 `/api/...`，不得加载 `/src/mocks`；`true` 仅用于前端演示。
  - `## 外部服务与降级`：百炼聊天、百炼 Embedding、SQLite vector 插件的 live / fallback 判定；不可用时只能标注降级，不宣称完整 live。
  - `## 验证命令`：后端 `ruff`、`mypy`、`pytest`；前端 `type-check`、`lint`、`build`；`GET /health`。
  - `## 常见问题`：端口占用、登录态/浏览器缓存、Mock 仍被加载、模型服务不可用、SQLite vector 插件未配置、上传目录不可写、macOS 本地依赖首次启动较慢。
  - `## 安全说明`：不要把真实 Key、Token、Base URL、密码写入 docs、`.sdd` 或测试报告；settings 页面只显示是否配置。

## 3. 最终 E2E 推荐验证策略

### 3.1 运行库选择

- 推荐使用临时 SQLite DB 和临时上传目录，不使用默认 `backend/data/customer_service.db` 作为最终 E2E 写入库。
- 推荐临时路径：
  - DB：`.sdd/tmp/t019-e2e-runtime.db`
  - Upload：`.sdd/tmp/t019-uploads`
- 推荐做法：
  - 创建临时 `backend/.env.local`，仅覆盖 `DATABASE_PATH` 与 `UPLOAD_DIR`，如需覆盖外部服务配置只写字段占位或沿用本机配置，不在报告输出值。
  - 运行 `PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py` 初始化临时库。
  - 回归结束删除 `backend/.env.local`、临时 DB、临时上传目录和浏览器临时目录。
- 如果必须使用默认库，所有新增 QA、文档、回复、完成摘要必须带唯一标记，例如 `T019_E2E_<timestamp>`，并在报告中证明对应 QA、文档、chunks、vectors、文件、员工回复和工单状态已清理或恢复。

### 3.2 唯一标记与清理

- QA 问题、QA 答案、上传文档名、文档正文、工单回复内容、完成摘要统一使用同一个唯一标记。
- 工单流程优先从临时 seed 中选择 `open` 工单接单，避免复用已被前序报告写过的默认运行库状态。
- 清理证明至少包含：
  - 测试 QA 已删除，关联 `vector_indexes` 无残留。
  - 测试文档已删除，关联 `document_chunks`、document vectors 和上传文件无残留。
  - 若完成了测试工单，污染仅存在于临时 DB；若用了默认库，需恢复工单状态并删除测试回复。
  - 端口 `8099`、`5199` 无残留监听。

### 3.3 外部服务 live / fallback 判定

- 百炼聊天：
  - 可用时，P05 AI 建议和 P09 文档生成问答应完成 live 调用。
  - 不可用时，页面必须显示清晰失败或降级提示；测试报告标注为模型服务 fallback / unavailable，不可宣称百炼 live。
- 百炼 Embedding：
  - T-015/T-014 曾实测可写入 embedding；T-019 仍需重新记录 `configured=true/false` 与本轮文档或 QA 入库返回的 `embedding_status`。
  - 不输出真实 Key 或可还原配置值。
- SQLite vector 插件：
  - 当前历史证据为未配置，按 FTS5 / LIKE fallback 验收。
  - 若本轮配置可用，应记录 vector available 与检索模式；若不可用，应明确写 `SQLite vector fallback to FTS5/LIKE`。
- 本地文件存储：
  - 上传目录必须可写；文档删除后物理文件应同步清理。

### 3.4 证明 `VITE_USE_MOCK=false` 下不命中 mocks

- 前端启动必须显式使用 `VITE_USE_MOCK=false`，并在浏览器确认 `document.documentElement.dataset.apiMode === 'real'`。
- 静态检查：
  - 运行 `rg -n "from ['\"]@/mocks|from ['\"]\\.\\./mocks|^import .*mock" frontend/src/services frontend/src/stores frontend/src/pages -g '*.ts' -g '*.vue'`。
  - 预期无顶层静态 mock import；允许 mock 分支内动态 `await import('@/mocks')`，但真实路径不得调用。
- 浏览器网络检查：
  - 捕获全流程 request，包括静态资源请求和 XHR/fetch。
  - 必须证明出现的是 `/api/...` 请求，且未出现 `/src/mocks`、`frontend/src/mocks`、`mocks/*.ts`。
- 页面文案检查：
  - 全流程页面不得出现 `[Mock]`、`Mock-only`、`Mock 账号`。

## 4. 推荐执行步骤

1. Developer 先创建 `docs/startup.md`，只写启动、配置、真实/Mock 模式、降级和 FAQ，不写真实敏感值。
2. Developer 如需自动化最终回归，可新增最小 E2E 辅助脚本或测试记录辅助文件；优先放在 `.sdd/tmp` 或 `.sdd/test-reports` 体系内，避免引入正式业务依赖。
3. Developer 运行后端质量门禁：
   - `.venv/bin/python -m ruff check backend/src backend/tests`
   - `.venv/bin/python -m mypy backend/src backend/tests`
   - `.venv/bin/python -m pytest backend/tests -q`
4. Developer 运行前端质量门禁：
   - `cd frontend && npm run type-check`
   - `cd frontend && npm run lint`
   - `cd frontend && npm run build`
5. Developer 用临时 DB 初始化并启动后端 `8099`，启动前端 `5199` 且 `VITE_USE_MOCK=false`。
6. Developer 或 Tester 执行浏览器最终 E2E：
   - 登录。
   - 查看工作台，并触发 quick ask。
   - 进入工单池，接取一个 open 工单。
   - 进入工单详情，验证会话、AI 建议、引用来源。
   - 采用或手动使用 AI 建议，发送回复。
   - 完成工单。
   - 进入 QA 管理，新增或编辑唯一标记 QA。
   - 进入文档入库，上传唯一标记文档并确认 completed 或清晰失败。
   - 进入智能问答调试，分别验证 QA 命中与文档引用；若外部服务不可用，验证页面降级提示。
   - 进入 settings，确认只显示配置状态不泄密；执行 logout 并确认回到登录页，旧 token 失效。
7. Developer 输出 `.sdd/test-reports/test-T-019.md`，记录命令、浏览器网络证据、live/fallback 状态、清理结果和敏感信息脱敏声明。
8. Tester 独立复验 `docs/startup.md` 与最终 E2E 报告；若发现业务阻断，记录 FAIL 和最小复现，不在 T-019 中扩大业务实现。

## 5. Developer 修改/产出边界

允许：
- 新增 `docs/startup.md`。
- 新增 `.sdd/test-reports/test-T-019.md`。
- 新增必要的临时 E2E 辅助脚本、临时上传样本或浏览器请求记录；建议位于 `.sdd/tmp`，验收后清理。
- 如发现测试辅助脚本值得保留，可放入明确的测试辅助位置，但不得改变业务运行路径。

不应修改：
- `.sdd/tasks.json`
- `.sdd/status.json`
- 既有 PRD、Plan、api-contracts，除非用户另行批准契约变更。
- 前后端业务代码、接口契约、页面功能、mock 数据、seed 数据。

例外：
- 只有最终 E2E 发现阻断级缺陷时，Developer 才应暂停并上报阻断、最小复现和影响范围；是否进入修复任务由上层决定。T-019 默认不承接业务修复。

## 6. Tester 验收清单

- [ ] `docs/startup.md` 存在，章节覆盖环境要求、依赖安装、初始化、后端启动、前端启动、配置字段、Mock/真实模式、外部服务降级、验证命令、FAQ、安全说明。
- [ ] `docs/startup.md` 未包含真实 Key、Token、Base URL、密码或可还原密钥片段。
- [ ] 按 `docs/startup.md` 可启动后端、初始化 SQLite、启动前端。
- [ ] 后端 `ruff`、`mypy`、`pytest` 通过。
- [ ] 前端 `type-check`、`lint`、`build` 通过。
- [ ] 浏览器 E2E 覆盖登录 -> 工作台 -> 工单池接单 -> 工单详情 -> AI 建议 -> 发送回复 -> 完成工单 -> QA 维护 -> 文档入库 -> 智能问答调试 -> settings/logout。
- [ ] 全流程 `VITE_USE_MOCK=false`，`dataset.apiMode=real`。
- [ ] 浏览器网络请求命中真实 `/api/...`，未命中 `/src/mocks`、`frontend/src/mocks` 或 `mocks/*.ts`。
- [ ] 页面无 `[Mock]`、Mock-only、Mock 账号提示。
- [ ] QA 新增/编辑后，P09 能看到对应问答效果；若 Embedding 或模型不可用，页面和报告有清晰降级说明。
- [ ] 文档上传完成后，P09 能看到文档引用来源；若 SQLite vector 插件不可用，报告明确标注 FTS5 / LIKE fallback。
- [ ] settings 只展示账号和配置状态，不展示 Key、Token、Base URL、secret 或 URL 明文。
- [ ] logout 后回到登录页，旧 token 访问主要接口返回 401。
- [ ] 所有 T-019 唯一标记测试数据已清理；若使用临时 DB，则临时 DB 与上传目录已删除。
- [ ] `.sdd/tasks.json`、`.sdd/status.json` 未被本任务修改。

## 7. 主要风险与应对

- 登录 UI 曾在 T-013/T-016/T-014 中出现 Playwright 操作下 localStorage 未保留的非阻塞现象；T-019 需要覆盖真实“从登录页开始”的用户路径，若仍复现，应判为最终 E2E 风险并记录。
- T-018 曾观察到 P05 自动 AI 建议在模型不可用时返回 500；T-019 若目标是完整 live，则需确保百炼聊天可用，否则只能降级验收。
- `getAssistantIntroAnswer()` 仍可能在 mock 分支动态加载；本轮真实路径重点看是否实际请求 `/src/mocks` 或调用 mock intro。
- 默认库容易被完成工单、回复、QA、文档上传污染；优先临时 DB，默认库仅作为迫不得已方案。
- SQLite vector 插件大概率未配置；验收报告必须诚实标注 FTS5 / LIKE fallback。
