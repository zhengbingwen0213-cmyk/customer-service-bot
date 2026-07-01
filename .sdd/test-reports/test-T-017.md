# T-017 工单详情 AI 建议与引用真实闭环验收报告

- 验收人：Tester 子智能体
- 验收时间：2026-06-29 17:30 Asia/Shanghai
- 工作目录：`/Users/bingsmacbook/Documents/个人/AI coding2/智能客服/SDD_V7_1/Projects_Repo/customer-service-bot`
- 结论：PASS

## 1. 静态检查

- `frontend/src/pages/TicketDetailPage.vue` 在详情和消息加载完成后调用 `loadAssistantSuggestion()`；请求 payload 固定 `scene: 'ticket'`、`ticket_id: ticket.value.id`，并使用 `messages.value.slice(-3)` 构造最近 3 条 `context_messages`。
- `frontend/src/services/assistant.ts` 与 `frontend/src/services/tickets.ts` 均只在 `isMockApiEnabled()` 为真时走 `@/mocks`；`VITE_USE_MOCK=false` 时分别调用真实 `/assistant/ask` 和 `/tickets/{ticket_id}/messages`。
- P05 模板只渲染 `answer_type` 的业务标签、`answer`、`missing_fields`、引用 `title/snippet/type`；未渲染 `answer_id`、`confidence`、`context_messages_used`、模型版本、请求号、prompt、trace、原始上下文、内部链路或引用 score/匹配度。
- 采用建议时前端内部保存 `assistantAnswer.answer_id` 到 `adoptedAssistantAnswerId`，发送回复时写入 `used_assistant_answer_id`；该字段不展示在页面上。
- `backend/tests/test_tickets.py` 已覆盖 `used_assistant_answer_id` 入库，且响应 `message` 不泄露该字段；`backend/src/services/ticket.py` 写入 `ConversationMessage.used_assistant_answer_id`，`_to_ticket_message()` 不返回该字段。

## 2. 质量门禁

全部为本轮新跑结果：

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest backend/tests -q` | PASS，`28 passed`，仅 Pydantic deprecation warnings |
| `.venv/bin/python -m ruff check backend/src backend/tests` | PASS，`All checks passed!` |
| `.venv/bin/python -m mypy backend/src backend/tests` | PASS，`Success: no issues found in 54 source files` |
| `cd frontend && npm run type-check` | PASS |
| `cd frontend && npm run lint` | PASS |
| `cd frontend && npm run build` | PASS，Vite build completed |

## 3. 真实联调环境

- 创建临时运行配置 `backend/.env.local`，仅覆盖 `DATABASE_PATH=backend/data/test-T-017-runtime.db`；联调后已删除。
- 初始化临时 SQLite：`PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py`，seed 成功：users=2、tickets=7、conversation_messages=7、qa_items=3、documents=3、document_chunks=12。
- 启动 backend：`127.0.0.1:8099`；启动 frontend：`127.0.0.1:5199`，显式 `VITE_USE_MOCK=false`。
- 登录使用 demo 账号；未在报告记录 token/key/secret。
- 检索 fallback 标注：本地 SQLite vector extension 未配置，本次文档检索按项目现状使用 FTS5/关键词路径；初始化脚本确认 QA 与 document FTS probe 均有命中。

## 4. 浏览器与网络证据

打开 `/tickets/TK-1005` 后：

- `document.documentElement.dataset.apiMode === 'real'`。
- 页面无 `[Mock]` / `Mock` 文案。
- 页面显示「AI 智能辅助」面板和「采用 AI 建议」入口。
- Network 命中真实 `POST http://127.0.0.1:5199/api/assistant/ask => 200`。
- 请求体为：

```json
{
  "question": "好的，订单号是 20260523001。你们核实一下，如果不行能退款吗？",
  "scene": "ticket",
  "ticket_id": "TK-1005",
  "context_messages": [
    {"sender": "customer", "content": "你好，我刚刚购买了年费会员，但是没有生效。"},
    {"sender": "bot", "content": "您好，系统可能存在网络延迟，请您提供一下订单号。"},
    {"sender": "customer", "content": "好的，订单号是 20260523001。你们核实一下，如果不行能退款吗？"}
  ]
}
```

页面展示结果：

- answer type 标签：`生成建议`。
- answer：展示可采用建议文本。
- 引用来源：显示 `售后政策及退款流程.pdf`、`文档来源`、片段 `售后政策及退款流程：用户支付后未生效时，客服需先核对订单号和支付渠道流水。`
- DOM 正文检查未发现：`answer_id`、`confidence`、`context_messages_used`、`模型版本`、`请求号`、`原始上下文`、`prompt`、`trace`、`内部链路`、`匹配度`、`score`。

采用与发送闭环：

- 点击「采用 AI 建议」后，回复框内容与 AI answer 完全一致。
- 点击「发送」后 Network 命中 `POST http://127.0.0.1:5199/api/tickets/TK-1005/messages => 200`。
- 发送请求体包含 `used_assistant_answer_id` 且非空；报告不记录具体值。
- 发送响应 `data.message` 不包含 `used_assistant_answer_id`。
- 页面会话列表从 3 条变 4 条，最后一条为 `客服一组员工` 的员工回复；回复框清空，并显示 `回复已发送`。
- 临时 DB 查询：`conversation_messages` 中 `ticket_id='TK-1005' and sender='employee'` 计数为 1，且非空 `used_assistant_answer_id` 计数为 1。

失败路径：

- 通过 Playwright route 将 `**/api/assistant/ask` 临时拦截为 500。
- 重新进入 `/tickets/TK-1005` 后，AI 面板状态为 `分析失败`，页面显示失败提示，并保留 `重新生成` 按钮；未静默吞错。

## 5. 清理

- 已关闭 Playwright browser，并取消临时 network route。
- 已停止 backend `8099` 和 frontend `5199`。
- `lsof -iTCP:8099 -sTCP:LISTEN -n -P`：无监听。
- `lsof -iTCP:5199 -sTCP:LISTEN -n -P`：无监听。
- 已删除 `backend/.env.local`、`backend/data/test-T-017-runtime.db`、`.playwright-cli`。
- 测试新增员工回复只存在于已删除的临时 DB；未污染默认运行库。
- 未完成工单；未修改 `.sdd/tasks.json` 或 `.sdd/status.json`。

## 6. 结论

T-017 验收 PASS。P05 在 `VITE_USE_MOCK=false` 下走真实后端 API，AI 建议、引用展示、采用建议、发送回复、`used_assistant_answer_id` 传递、前端字段隐藏和失败提示均满足验收范围；后端与前端质量门禁均通过。
