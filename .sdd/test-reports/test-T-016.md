# T-016 检索与智能问答调试真实闭环验收报告

- 验收人：Tester 子智能体
- 验收时间：2026-06-26 15:00 Asia/Shanghai
- 工作目录：`/Users/bingsmacbook/Documents/个人/AI coding2/智能客服/SDD_V7_1/Projects_Repo/customer-service-bot`
- 结论：PASS

## 1. 静态检查

- API 契约：`docs/api-contracts.md:725-805` 定义 `POST /api/assistant/ask`，覆盖 `quick` / `ticket` / `debug`、`context_messages` 最多 3 轮、`qa_direct` 和 `clarification` 响应。
- 后端路由：`backend/src/api/routes/assistant.py` 注册 `/api/assistant/ask`，需要登录，模型不可用时返回 500 `模型服务暂时不可用`。
- QA 优先与上下文限制：`backend/src/services/assistant.py:18-19` 设置 `QA_DIRECT_THRESHOLD = 0.8`、`MAX_CONTEXT_MESSAGES = 3`；`backend/src/services/assistant.py:58-70` 先查 QA，命中阈值后直接返回 `qa_direct`；`backend/src/services/assistant.py:73-83` 模糊问题返回 `clarification`、`missing_fields`，引用为空；`backend/src/services/assistant.py:86-98` QA 未命中后检索文档并生成 `generated`。
- 百炼网关：`backend/src/services/ai_gateway.py:133-145` 使用现有 `httpx.AsyncClient(trust_env=False)` 发送 `chat/completions` / `embeddings` 请求，未发现 SDK 或环境代理路径。
- 检索降级：`backend/src/services/retrieval.py:120-125` 探测 SQLite 向量插件，不可用时选择 `fts5` 或 `like` 并输出 fallback reason。
- 前端服务：`frontend/src/services/assistant.ts:17-24` 仅在 `isMockApiEnabled()` 为真时走 `mockAskAssistant`，`VITE_USE_MOCK=false` 时调用真实 `api.post('/assistant/ask')`。
- P09 页面：`frontend/src/pages/AssistantDebugPage.vue:50-55` 使用 `scene: 'debug'` 调用真实服务；`frontend/src/pages/AssistantDebugPage.vue:88-95` 构造上下文时 `.slice(-3)`；静态搜索 P09 未发现 Mock-only 文案、`[Mock]`、模型版本、请求号、原始上下文、内部链路、prompt、trace 展示。

## 2. 命令验证

全部为本轮新跑结果：

| 命令 | 结果 |
|---|---|
| `.venv/bin/python -m pytest backend/tests -q` | PASS，`28 passed`，仅 Pydantic deprecation warnings |
| `.venv/bin/python -m ruff check backend/src backend/tests` | PASS，`All checks passed!` |
| `.venv/bin/python -m mypy backend/src backend/tests` | PASS，`Success: no issues found in 54 source files` |
| `cd frontend && npm run type-check` | PASS |
| `cd frontend && npm run lint` | PASS |
| `cd frontend && npm run build` | PASS，Vite build completed |

## 3. API 验证

运行方式：用临时 runtime wrapper 将 SQLite 指向 `.sdd/tmp/t016_runtime.db`，启动 `127.0.0.1:8099`；初始化 demo seed 和 FTS5。登录 demo 账号后仅在脚本内使用 token，报告未记录 token。

| 用例 | 结果 |
|---|---|
| 未登录 `POST /api/assistant/ask` | 401，`{"code":401,"message":"登录状态已失效","data":null}` |
| `quick` / `ticket` / `debug` + `退款多久到账？` | 均 200，`answer_type=qa_direct`，QA reference，score `1.0` |
| `这个超过了怎么办` | 200，`answer_type=clarification`，`missing_fields=["支付渠道"]`，`references=[]` |
| 4 条 `context_messages` + QA 问题 | 200，`context_messages_used=3` |
| `支付后会员未生效且渠道已扣款，客服应该如何人工补单？` | 200，`answer_type=generated`，answer 非空，`reference_types=["document"]`，`references_len=1` |

检索状态实测：

```json
{
  "vector_status": "fallback",
  "vector_available": false,
  "keyword_backend": "fts5",
  "mode": "fts5",
  "fallback_reason": "vector plugin unavailable; using fts5: SQLITE_VECTOR_EXTENSION_PATH is not configured"
}
```

说明：SQLite 向量插件未配置，本次真实运行按预期降级为 FTS5；未假装向量插件成功。

## 4. 浏览器 / P09 验证

运行方式：backend `8099` + frontend `5199`，启动前端时显式设置：

```bash
VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8099/api npm run dev -- --host 127.0.0.1 --port 5199
```

浏览器证据：

- `/assistant` 页面 `document.documentElement.dataset.apiMode` 为 `real`。
- 页面 body 检测：`containsMock=false`，`containsInternal=false`；未展示 `Mock` / `[Mock]` / 模型版本 / 请求号 / 原始上下文 / 内部链路 / prompt / trace。
- UI 输入 `退款多久到账？` 后，Network 命中 `POST http://127.0.0.1:8099/api/assistant/ask`，不是 `frontend/src/mocks/*`。
- 首次 UI 请求体：`{"question":"退款多久到账？","scene":"debug","conversation_id":"debug_session_001","context_messages":[]}`。
- 首次 UI 响应：200，`answer_type=qa_direct`，QA reference，score `1.0`；页面展示「直接答案」「匹配度：100%」「引用来源: QA：退款多久到账？」。
- 连续多轮后最后一次 UI 请求体含 `context_messages` 3 条；响应 `context_messages_used=3`；页面最大可见上下文提示为 3。

非阻塞说明：Playwright UI 登录点击触发了真实 `/api/auth/login` 和 `/api/auth/me` 200，但页面未停留到已登录态；为继续 P09 验证，改用同页面 `fetch` 调真实登录接口写入 localStorage，未输出或记录 token。该现象不在 T-016 验收边界内。

## 5. 清理

- 已关闭 Playwright browser。
- 已停止 backend `8099` 和 frontend `5199`。
- `lsof -nP -iTCP:8099 -sTCP:LISTEN`：无监听。
- `lsof -nP -iTCP:5199 -sTCP:LISTEN`：无监听。
- 已删除本次创建的 `.sdd/tmp/t016_runtime.db*`、`.sdd/tmp/t016_uploads`、临时 runtime wrapper、`.playwright-cli`。
- 未新增业务测试数据；未修改 `.sdd/tasks.json` 或 `.sdd/status.json`。

## 6. 结论

T-016 验收 PASS。后端、前端命令验证通过；API 和 P09 浏览器真实闭环满足 T-016 范围；向量插件不可用已明确标注为 FTS5 fallback。
