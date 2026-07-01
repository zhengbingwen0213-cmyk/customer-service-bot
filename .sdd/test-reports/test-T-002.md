# 测试报告：T-002 客服工作台 Mock

**测试时间**：2026-05-23 18:18 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户进入客服工作台，看到待接、处理中、已完成、QA 数量和文档数量等概览卡片。 | PASS | `frontend/src/pages/DashboardPage.vue:35` 根据 `open_ticket_count`、`processing_ticket_count`、`completed_ticket_count`、`qa_count`、`document_count` 生成概览卡片；Mock 数据在 `frontend/src/mocks/dashboard.ts:35` 提供对应字段。 |
| 2 | 用户在待处理工单快捷区看到少量工单卡片，点击工单入口后页面能跳转到工单详情 Mock 页面。 | PASS | `frontend/src/pages/DashboardPage.vue:177` 渲染待处理工单快捷区，`frontend/src/pages/DashboardPage.vue:208` 将工单入口指向 `/tickets/${ticket.id}`；`frontend/src/router/index.ts:42` 定义 `tickets/:ticketId` 并指向 Mock 占位详情页。 |
| 3 | 用户在 AI 快捷问答入口输入问题并点击发送，页面展示 Mock AI 回答气泡和引用来源占位。 | PASS | `frontend/src/pages/DashboardPage.vue:127` 处理发送，`frontend/src/pages/DashboardPage.vue:145` 将 Mock 回答加入消息流；`frontend/src/pages/DashboardPage.vue:253` 展示引用来源；Mock 回答和引用在 `frontend/src/mocks/assistant.ts:62`、`frontend/src/mocks/assistant.ts:70`。 |
| 4 | 用户点击知识库快捷入口，页面能跳转到 QA 库管理或文档入库 Mock 页面；本任务不要求真实模型、真实后端或数据库。 | PASS | `frontend/src/pages/DashboardPage.vue:216` 提供知识库快捷入口，`frontend/src/pages/DashboardPage.vue:217` 跳转 QA 库，`frontend/src/pages/DashboardPage.vue:221` 跳转文档入库；`frontend/src/router/index.ts:69` 和 `frontend/src/router/index.ts:78` 均指向 Mock 占位页。 |

## 技术检查

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | Frontend typecheck passes | PASS | 在 `frontend/` 执行 `npm run type-check`，退出码 0。 |
| 2 | Frontend lint passes | PASS | 在 `frontend/` 执行 `npm run lint`，退出码 0。 |
| 3 | Frontend build passes | PASS | 用户要求的附加检查：在 `frontend/` 执行 `npm run build`，退出码 0，Vite build 成功。 |
| 4 | Mock dashboard summary、dashboard tickets、assistant ask 数据字段与 docs/api-contracts.md 一致 | PASS | 契约定义见 `docs/api-contracts.md:350`、`docs/api-contracts.md:383`、`docs/api-contracts.md:725`；类型和 Mock 返回字段见 `frontend/src/types/dashboard.ts:4`、`frontend/src/types/dashboard.ts:13`、`frontend/src/types/assistant.ts:11`、`frontend/src/types/assistant.ts:27`、`frontend/src/mocks/dashboard.ts:81`、`frontend/src/mocks/dashboard.ts:94`、`frontend/src/mocks/assistant.ts:25`。未发现 Mock 字段溢出。 |
| 5 | P02 不展示模型版本、请求号、原始上下文或内部链路 | PASS | `frontend/src/pages/DashboardPage.vue` 仅展示概览、工单、业务回答和引用来源；静态搜索未发现 `model_version`、`request_id`、`trace_id`、原始上下文或内部链路展示。 |
| 6 | Mock 阶段没有调用真实后端、真实模型、真实数据库；没有写真实密钥 | PASS | `frontend/src/services/dashboard.ts:1`、`frontend/src/services/assistant.ts:1` 只导入 `@/mocks`，不调用 `api.ts`、`fetch`、真实模型或数据库；`frontend/.env` 为 `VITE_USE_MOCK=true`；静态搜索未发现真实 API Key、Token、Secret 或外部服务凭证。 |

## 验证边界

- 本轮按用户要求未启动本地预览服务，未使用浏览器，未做真实后端、真实模型或真实数据库联调。
- T-002 为 `type=frontend` 且 `frontendIntegration.required=false`，因此按 Mock 阶段边界执行静态代码分析和构建验证。
