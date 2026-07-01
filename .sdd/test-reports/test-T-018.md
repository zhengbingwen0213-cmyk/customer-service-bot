# T-018 复验报告：客服工作台与账号设置补齐真实闭环

结论：PASS

复验时间：2026-06-30 01:20 Asia/Shanghai

## 结论说明

本次针对上轮 FAIL 阻断项做独立复验。`VITE_USE_MOCK=false` 下，浏览器真实模式已不再请求 `/src/mocks/*.ts` 或其他 `frontend/src/mocks` 资源；dashboard、settings、assistant quick、logout 均命中真实 `/api/...`。

后端真实闭环、settings 脱敏、logout 后 token 失效、前端命令验证均通过。本轮验收判定为 PASS。

## 复验覆盖范围

- 重跑静态检查：确认 services/stores/pages 无顶层静态 mock import。
- 重跑后端命令：pytest、ruff、mypy。
- 重跑前端命令：type-check、lint、build。
- 使用临时 SQLite DB 启动 backend 8099。
- 使用 `VITE_USE_MOCK=false` 启动 frontend 5199。
- 使用浏览器登录 `/dashboard`，验证 dashboard summary/tickets、quick ask、settings account、logout。
- 严格检查浏览器静态与非静态网络请求中无 `/src/mocks` 或 `frontend/src/mocks` 命中。
- 保留 settings 脱敏、logout 后旧 token 失效、工单入口等既有通过项证据。

## 静态检查

命令：

```bash
rg -n "from ['\"]@/mocks|from ['\"]\.\./mocks|^import .*mock" frontend/src/services frontend/src/stores frontend/src/pages -g '*.ts' -g '*.vue'
```

结果：无输出。

补充检查：

- `frontend/src/services/auth.ts`
- `frontend/src/services/dashboard.ts`
- `frontend/src/services/assistant.ts`
- `frontend/src/services/settings.ts`
- `frontend/src/services/tickets.ts`
- `frontend/src/services/documents.ts`
- `frontend/src/services/knowledge.ts`

上述服务文件不再顶层静态 import `@/mocks`；mock 分支改为 `await import('@/mocks')` 动态加载。

说明：`frontend/src/services/assistant.ts` 中 `getAssistantIntroAnswer()` 仍会动态加载 mock intro，但 dashboard 页面未调用该函数；本轮 T-018 路径中的 `askAssistant()` 在 real mode 命中 `/assistant/ask`。

## 命令验证

工作目录：`/Users/bingsmacbook/Documents/个人/AI coding2/智能客服/SDD_V7_1/Projects_Repo/customer-service-bot`

- `.venv/bin/python -m pytest backend/tests -q`
  - 结果：PASS，31 passed。
  - 备注：仍有 Pydantic v2 deprecation warnings，不影响本轮功能验收。
- `.venv/bin/python -m ruff check backend/src backend/tests`
  - 结果：PASS，All checks passed。
- `.venv/bin/python -m mypy backend/src backend/tests`
  - 结果：PASS，Success: no issues found in 58 source files。
- `cd frontend && npm run type-check`
  - 结果：PASS。
- `cd frontend && npm run lint`
  - 结果：PASS。
- `cd frontend && npm run build`
  - 结果：PASS，Vite build succeeded，126 modules transformed。

## API 复验

验证方式：使用 `.sdd/tmp/t018-retest.db` 临时 SQLite DB，seed demo data 后启动 backend 8099，通过真实 HTTP 请求验证。未使用默认 `backend/data/customer_service.db`。

临时库初始化证据：

- `db_exists=True`
- seed counts：tickets=7，qa_items=3，documents=3

HTTP 证据：

- 未登录：
  - `GET /api/dashboard/summary` -> 401，`code=401`，`message=登录状态已失效`
  - `GET /api/dashboard/tickets` -> 401，`code=401`
  - `GET /api/settings/account` -> 401，`code=401`
- 登录：
  - `POST /api/auth/login` -> 200，token 存在但未记录 token 值，user=`user_001`
- `GET /api/dashboard/summary`：
  - status=200
  - `open_ticket_count=2`
  - `processing_ticket_count=3`
  - `completed_ticket_count=1`
  - `qa_count=3`
  - `document_count=3`
  - `latest_knowledge_updated_at=2026-05-24T10:15:00+08:00`
- `GET /api/dashboard/tickets?limit=3`：
  - status=200
  - ids=`['TK-1005', 'TK-1003', 'TK-1006']`
  - priorities=`['high', 'high', 'low']`
  - assignees=`['user_001']`
  - statuses=`['processing']`
  - 未返回其他客服 `TK-2001`
- limit 非法值：
  - `limit=0` -> 400，`message=limit 必须为 1 到 20 的整数`
  - `limit=21` -> 400，`message=limit 必须为 1 到 20 的整数`
- `GET /api/settings/account`：
  - status=200
  - system keys=`['api_key_configured', 'chat_model', 'database', 'embedding_dimensions', 'embedding_model', 'model_provider']`
  - `api_key_configured` 类型为 bool
  - 响应 JSON 未命中敏感标记：`dashscope_api_key`、明文 `api_key` 字段、`token`、`secret`、`base_url`、`http://`、`https://`
- `POST /api/assistant/ask`，payload `scene=quick`：
  - status=200，`code=200`
  - `answer_type=qa_direct`
  - `missing_fields=[]`
  - references 包含 title=`退款多久到账？`
- `POST /api/auth/logout`：
  - status=200，`logged_out=True`
  - logout 后旧 token 访问：
    - `GET /api/dashboard/summary` -> 401
    - `GET /api/settings/account` -> 401

## 浏览器真实模式复验

启动方式：

- backend：8099，临时 SQLite DB。
- frontend：5199，`VITE_USE_MOCK=false npm run dev -- --host 127.0.0.1 --port 5199`。
- browser：Playwright CLI + Chromium。

页面证据：

- 登录后进入 `/dashboard`。
- `document.documentElement.dataset.apiMode` = `real`。
- dashboard 页面无 `[Mock]` 文案。
- dashboard 统计显示：
  - 待接工单 2
  - 处理中 3
  - 已完成 1
  - 知识总数 6
- dashboard 待处理工单显示：
  - `TK-1005 会员支付后未生效`
  - `TK-1003 支付回调延迟问题排查`
- dashboard quick ask 输入“退款多久到账？”后：
  - 页面显示答案“正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。”
  - 页面显示引用来源 `QA · 退款多久到账？`
  - 页面检查：无 `[Mock]`，无 `confidence`，无 `score/匹配度`，无 `context_messages_used/上下文`
- 点击 dashboard 工单“查看”进入 `/tickets/TK-1005`，页面显示 `工单详情 TK-1005` 和 `会员支付后未生效`。
- settings 页面进入 `/settings`：
  - 展示字段：当前账号、登录名、数据库、模型服务、聊天模型、Embedding 模型、Embedding 维度、API Key 配置。
  - 页面敏感词扫描未命中 `token`、`secret`、`base_url`、`dashscope`、`http://`、`https://`。
- 点击退出后回到 `/login`。

浏览器 API 请求证据：

- `[POST] /api/auth/login => 200`
- `[GET] /api/dashboard/summary => 200`
- `[GET] /api/dashboard/tickets?limit=2 => 200`
- `[GET] /api/auth/me => 200`
- `[POST] /api/assistant/ask => 200`（dashboard quick ask）
- `[GET] /api/tickets/TK-1005 => 200`
- `[GET] /api/tickets/TK-1005/messages => 200`
- `[GET] /api/settings/account => 200`
- `[POST] /api/auth/logout => 200`

严格 mocks 网络检查：

检查命令等价逻辑：`playwright requests --static | rg -n "api/|src/mocks|frontend/src/mocks|mocks"`。

结果只出现 `/api/...` 请求，未出现 `/src/mocks/*.ts`、`frontend/src/mocks` 或其他 mocks 命中。

清晰标记：

- dashboard/settings 前：`NO_MOCK_REQUESTS_FOUND`
- logout 后：`NO_MOCK_REQUESTS_FOUND_AFTER_LOGOUT`

## 风险或降级说明

- 工单详情页进入 `/tickets/TK-1005` 后，页面自动触发的 AI 智能辅助生成路径出现一次 `/api/assistant/ask => 500`，页面显示“模型服务暂时不可用”。
  - 该请求属于工单详情页生成式 AI 分析路径，不是 T-018 P02 dashboard quick ask 的通过条件。
  - dashboard quick ask 已通过 QA 直答返回 200。
  - 当前环境 API Key 未配置时，该降级路径清晰可见，没有伪造通过。
- pytest 仍有 Pydantic v2 deprecation warnings，属于后续依赖升级风险，不影响本轮验收结论。
- `getAssistantIntroAnswer()` 仍是 mock intro 动态 import，但本轮 T-018 real-mode 页面路径未调用它；dashboard 页面也未引用 `mockGetAssistantIntroAnswer`。

## 清理证明

- 已关闭 Playwright 浏览器：`Browser 'default' closed`。
- 已停止 frontend dev server。
- 已停止 backend 8099 server，日志显示 `API server stopped`。
- 已删除临时 SQLite：`.sdd/tmp/t018-retest.db`，检查结果 `temp_db_removed`。
- 已删除临时上传目录和临时请求记录。
- 端口检查：
  - `lsof -nP -iTCP:8099 -sTCP:LISTEN` 无输出。
  - `lsof -nP -iTCP:5199 -sTCP:LISTEN` 无输出。

## 未修改项

- 未修改业务实现代码。
- 未修改 `.sdd/tasks.json`。
- 未修改 `.sdd/status.json`。
- 报告中未记录真实 Key、Token、Base URL 或可还原片段。
