# 测试报告：T-006 文档入库与智能问答调试 Mock

**测试时间**：2026-05-24 11:22:27 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户打开文档入库页，看到文档名称、入库状态、切片数量、上传人和更新时间。 | PASS | `frontend/src/pages/DocumentsPage.vue:296-331` 表格列和行渲染覆盖文档名称、入库状态、切片数量、上传人、更新时间；数据由 `frontend/src/mocks/documents.ts:27-55` 提供。 |
| 2 | 用户选择文件并点击上传后，当前页面新增一条 Mock 入库记录，并展示处理中、已完成或失败状态。 | PASS | `frontend/src/pages/DocumentsPage.vue:82-127` 选择文件后调用上传，成功后把返回文档插入当前页面列表；`frontend/src/mocks/documents.ts:173-211` 创建 `processing` 入库记录，初始 Mock 数据包含 `completed`、`processing`、`failed` 三种状态。 |
| 3 | 用户打开智能问答调试页，输入问题并发送，页面展示 Mock 直接答案、反问或生成答案以及引用来源。 | PASS | `frontend/src/pages/AssistantDebugPage.vue:35-69` 发送问题并接收 Mock answer；`frontend/src/mocks/assistant.ts:70-154` 覆盖 `clarification`、`generated`、`qa_direct`；`frontend/src/pages/AssistantDebugPage.vue:235-284` 展示回答类型、回答内容和引用来源。 |
| 4 | 用户连续追问时，页面展示最近上下文效果；本任务不要求真实文件保存、真实 Embedding、真实向量检索或真实模型调用。 | PASS | `frontend/src/pages/AssistantDebugPage.vue:88-96` 仅取最近 3 条上下文发送 Mock；`frontend/src/pages/AssistantDebugPage.vue:262-266` 展示最近上下文数量；`frontend/src/services/documents.ts:17-42` 与 `frontend/src/services/assistant.ts:13-17` 均直接调用 `frontend/src/mocks/`，未调用真实后端、模型、Embedding、向量检索、文件存储或数据库。 |

## 技术检查

| # | 检查 | 结果 | 说明 |
|---|------|------|------|
| 1 | Frontend typecheck passes | PASS | 已执行 `npm run type-check`，退出码 0。 |
| 2 | Frontend lint passes | PASS | 已执行 `npm run lint`，退出码 0。 |
| 3 | Frontend build passes | PASS | 已执行 `npm run build`，退出码 0，Vite 构建成功。 |
| 4 | Mock documents、assistant ask 数据字段与 docs/api-contracts.md 一致 | PASS | `docs/api-contracts.md:194-205`、`1075-1154` 与 `frontend/src/types/documents.ts:1-62`、`frontend/src/mocks/documents.ts:77-110` 字段一致；`docs/api-contracts.md:147-180`、`725-802` 与 `frontend/src/types/assistant.ts:1-39`、`frontend/src/mocks/assistant.ts:15-34` 字段一致。 |
| 5 | P09 不展示模型版本、请求号、原始上下文或内部链路 | PASS | `frontend/src/pages/AssistantDebugPage.vue:197-284` 仅展示回答结果、回答类型、缺失实体、最近上下文数量和引用来源；静态搜索未发现模型版本、请求号、原始上下文、Context JSON、Trace 或内部链路展示。 |
| 6 | 文档状态枚举只使用 processing / completed / failed | PASS | `frontend/src/types/documents.ts:1` 定义仅包含三值；`frontend/src/mocks/documents.ts:69-70` 校验也仅允许三值；页面筛选和文案映射见 `frontend/src/pages/DocumentsPage.vue:200-205`、`282-286`。 |
| 7 | 无 V2+ 功能外溢 | PASS | 静态检查未发现新增文档切片可视化、评测集、参数面板、A/B 实验或质量评分功能。 |
| 8 | 短时预览服务 | PASS | 本任务为 Mock 前端任务，按 Tester 规则未启动 Playwright/E2E，也未启动长期预览服务。 |

## 命令验证

```text
npm run type-check
> vue-tsc --noEmit -p tsconfig.app.json
结果：退出码 0

npm run lint
> eslint . --max-warnings=0
结果：退出码 0

npm run build
> vue-tsc --noEmit -p tsconfig.app.json && vite build
结果：退出码 0，✓ built in 429ms
```
