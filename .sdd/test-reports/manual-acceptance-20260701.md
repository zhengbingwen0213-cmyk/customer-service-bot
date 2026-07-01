# 2026-07-01 人工验收记录

## 结论

- Status: PASS
- 验收时间：2026-07-01 20:50 CST
- 运行模式：`VITE_USE_MOCK=false`
- 运行库：临时 SQLite `.sdd/tmp/manual-acceptance-20260701/manual-acceptance.db`
- 上传目录：临时目录 `.sdd/tmp/manual-acceptance-20260701/uploads`
- 唯一标记：`MANUAL_ACCEPT_20260701`

## 验收路径

本轮使用真实浏览器按用户路径验收：

1. 登录 `agent01`，并确认 `document.documentElement.dataset.apiMode === "real"`。
2. 查看客服工作台概览，页面无 `[Mock]`、`Mock-only`、Mock 账号提示。
3. 在工作台智能助手执行 quick ask，并看到回答或引用来源。
4. 进入工单池，接取 `TK-1002`。
5. 进入工单详情，查看会话记录，生成并采用 AI 建议。
6. 发送回复并完成工单。
7. 新增唯一标记 QA，并在智能问答调试页命中 QA 答案与引用来源。
8. 上传唯一标记 Markdown 文档，确认入库完成。
9. 在智能问答调试页命中文档答案与文档引用来源。
10. 进入账号与基础设置页，确认页面不展示敏感形态字段。
11. 退出登录并回到登录页。

## 检查点

- `login and dashboard real mode`
- `dashboard summary visible`
- `dashboard: no mock-only text`
- `dashboard quick ask answered`
- `ticket pool visible`
- `ticket claimed`
- `ticket detail visible`
- `conversation visible`
- `ticket detail: no mock-only text`
- `ai suggestion adopted`
- `reply sent`
- `ticket completed`
- `qa created`
- `qa visible in list`
- `assistant qa answer`
- `assistant qa answer: reference visible`
- `document uploaded`
- `document visible`
- `document completed`
- `assistant document answer`
- `assistant document answer: reference visible`
- `settings visible`
- `settings no sensitive-looking terms`
- `logout returns login`

## 网络证据

- API events: 26
- Mock resource events: 0

命中的真实后端接口包括：

- `/api/auth/login`
- `/api/auth/me`
- `/api/auth/logout`
- `/api/dashboard/summary`
- `/api/dashboard/tickets?limit=2`
- `/api/tickets?scope=pool&status=open&page=1&page_size=20`
- `/api/tickets/TK-1002`
- `/api/tickets/TK-1002/claim`
- `/api/tickets/TK-1002/messages`
- `/api/tickets/TK-1002/complete`
- `/api/assistant/ask`
- `/api/knowledge/qa`
- `/api/knowledge/qa?page=1&page_size=20`
- `/api/documents`
- `/api/documents?page=1&page_size=20`
- `/api/settings/account`

## 说明

- 本轮使用临时数据库和临时上传目录，不污染默认演示库。
- 本轮运行时为临时库随机重置本机演示账号密码；未记录或输出密码。
- AI 建议、QA 问答、文档引用均在本轮通过，无 fallback warning。
- 验收结束时 8099 / 5199 均无 listener。
