# 开发计划

> 设计阶段与开发阶段的衔接文件。所有开发进度以本文件为准。

## 一、功能清单总览

| 序号 | 功能名称 | 一句话描述 | 对应页面 | 优先级 | 状态 |
|---|---|---|---|---|---|
| F01 | 账号登录与登录态 | 员工通过账号密码进入系统并保持登录态 | P01、P10 | MVP | 待开发 |
| F02 | 客服工作台 | 展示工作概览、待处理工单和 AI 快捷问答入口 | P02 | MVP | 待开发 |
| F03 | 工单池 | 员工查看待接工单、筛选并接取工单 | P03 | MVP | 待开发 |
| F04 | 我的工单 | 员工查看自己已接取和已完成的工单 | P04 | MVP | 待开发 |
| F05 | 工单详情与会话处理 | 员工查看工单、会话记录、AI 建议并完成工单 | P05 | MVP | 待开发 |
| F06 | 知识库总览 | 展示 QA、文档数量和最近知识 | P06 | MVP | 待开发 |
| F07 | QA 库管理 | 支持 QA 新增、编辑、删除、搜索和启停 | P07 | MVP | 待开发 |
| F08 | 文档入库 | 支持文档上传、入库状态查看和删除 | P08 | MVP | 待开发 |
| F09 | 智能问答调试 | 支持问题测试、反问、答案和引用来源展示 | P09 | MVP | 待开发 |
| F10 | 账号与基础设置 | 展示当前账号和基础系统配置状态 | P10 | MVP | 待开发 |

## 二、数据契约摘要

> 完整业务数据契约见 `docs/PRD.md`；接口契约见 `docs/api-contracts.md`。

### 统一响应格式

成功：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

错误：

```json
{
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

分页：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### 核心枚举

| 字段 | 可选值 |
|---|---|
| 工单状态 | `open` / `processing` / `completed` |
| 优先级 | `low` / `medium` / `high` |
| 消息发送方 | `customer` / `employee` / `bot` |
| QA 状态 | `enabled` / `disabled` |
| 文档状态 | `processing` / `completed` / `failed` |
| 回答类型 | `qa_direct` / `clarification` / `generated` |

## 二点五、外部服务与测试权限清单

> 进入多智能体自动化开发前必须确认。真实 Key / Token / Secret 不写入本文档或任何 `docs/**`、`.sdd/**` 可读产物，只记录字段名、用途和配置状态；真实值只能进入 `.env` 等配置文件。

| 服务 | 用途 | 配置项字段 | MVP 必需 | Tester 完整联调权限 | 缺失时策略 | 状态 |
|---|---|---|---|---|---|---|
| 阿里云百炼 | 回答生成、意图判断、模糊反问、问题改写 | `DASHSCOPE_API_KEY`、`BAILIAN_BASE_URL`、`BAILIAN_CHAT_MODEL` | 是 | 测试 Key、可调用额度、网络可访问 | 使用 Mock 回答，只能标记降级验收 | 本地已配置，开发前需实测 |
| 阿里云百炼 Embedding | QA 和文档切片向量生成 | `DASHSCOPE_API_KEY`、`BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS` | 是 | 测试 Key、可调用额度、网络可访问 | 使用关键词检索降级，只能标记降级验收 | 本地已配置，开发前需实测 |
| SQLite | 业务数据存储 | `DATABASE_URL` | 是 | 本地文件读写权限 | 无法启动后端完整业务 | 待初始化 |
| SQLite 向量插件 | 本地向量检索 | `SQLITE_VECTOR_EXTENSION_PATH` | 是 | 本机插件可安装或可加载 | 降级为 FTS5 / LIKE 检索并标注 | 待验证 |
| 本地文件存储 | 文档上传与入库文件保存 | `UPLOAD_DIR` | 是 | 项目运行目录写入权限 | 文档入库只做 Mock 状态 | 待初始化 |

## 三、前端开发清单

| 序号 | 页面名称 | 涉及功能 | Mock 数据来源 | 状态 |
|---|---|---|---|---|
| P01 | 登录页 | F01 | `POST /api/auth/login`、`GET /api/auth/me` | 待开发 |
| P02 | 客服工作台 | F02 | `GET /api/dashboard/summary`、`GET /api/dashboard/tickets`、`POST /api/assistant/ask` | 待开发 |
| P03 | 工单池 | F03 | `GET /api/tickets`、`POST /api/tickets/{ticket_id}/claim` | 待开发 |
| P04 | 我的工单 | F04 | `GET /api/tickets`、`GET /api/tickets/{ticket_id}` | 待开发 |
| P05 | 工单详情 | F05 | `GET /api/tickets/{ticket_id}`、`GET /api/tickets/{ticket_id}/messages`、`POST /api/assistant/ask` | 待开发 |
| P06 | 知识库总览 | F06 | `GET /api/knowledge/overview`、`GET /api/knowledge/recent` | 待开发 |
| P07 | QA 库管理 | F07 | `GET /api/knowledge/qa`、`POST /api/knowledge/qa`、`PUT /api/knowledge/qa/{qa_id}`、`DELETE /api/knowledge/qa/{qa_id}` | 待开发 |
| P08 | 文档入库 | F08 | `GET /api/documents`、`POST /api/documents`、`GET /api/documents/{document_id}`、`DELETE /api/documents/{document_id}` | 待开发 |
| P09 | 智能问答调试 | F09 | `POST /api/assistant/ask`、`GET /api/knowledge/qa`、`GET /api/documents` | 待开发 |
| P10 | 账号与基础设置 | F10 | `GET /api/settings/account`、`POST /api/auth/logout` | 待开发 |

### 前端自动验收标准

- [ ] 所有页面 UI 与 `docs/prototypes/` 原型一致。
- [ ] 所有页面使用 Mock 数据可正常交互。
- [ ] Mock 数据集中放在 `frontend/src/mocks/`。
- [ ] Mock 字段、枚举、嵌套结构与 `docs/api-contracts.md` 完全一致。
- [ ] P05 不出现超出 MVP 的工单动作。
- [ ] P09 不展示模型版本、请求号、原始上下文或内部链路。
- [ ] Agent / Tester 自动验收通过。

> 前端 Mock 页面完成后触发用户门禁，由用户验收 UI/UX 效果；用户确认后再进入后端基础设施开发。

## 四、后端开发清单

| 序号 | 功能名称 | 依赖 | 对应接口 | 状态 |
|---|---|---|---|---|
| B00 | 后端基础设施 | 无 | `GET /health` | 待开发 |
| B01 | 数据库与演示数据 | B00 | 所有业务接口依赖 | 待开发 |
| B02 | 账号登录 | B01 | `POST /api/auth/login`、`GET /api/auth/me`、`POST /api/auth/logout` | 待开发 |
| B03 | 工作台概览 | B01、B02 | `GET /api/dashboard/summary`、`GET /api/dashboard/tickets` | 待开发 |
| B04 | 工单流转 | B01、B02 | `GET /api/tickets`、`GET /api/tickets/{ticket_id}`、`POST /api/tickets/{ticket_id}/claim`、`POST /api/tickets/{ticket_id}/complete` | 待开发 |
| B05 | 会话消息 | B04 | `GET /api/tickets/{ticket_id}/messages`、`POST /api/tickets/{ticket_id}/messages` | 待开发 |
| B06 | QA 库管理 | B01、B02 | `GET /api/knowledge/qa`、`POST /api/knowledge/qa`、`PUT /api/knowledge/qa/{qa_id}`、`DELETE /api/knowledge/qa/{qa_id}` | 待开发 |
| B07 | 文档入库 | B01、B02 | `GET /api/documents`、`POST /api/documents`、`GET /api/documents/{document_id}`、`DELETE /api/documents/{document_id}` | 待开发 |
| B08 | 检索与向量适配 | B06、B07 | Assistant 内部依赖 | 待开发 |
| B09 | AI 问答编排 | B05、B08 | `POST /api/assistant/ask` | 待开发 |
| B10 | 账号设置 | B02 | `GET /api/settings/account` | 待开发 |

### 后端任务验收规则

- 基础设施任务基于 PyCore 框架，禁止重写已有 `config.py`、`server.py`、`logger.py` 的核心能力。
- 后端配置、数据库、日志、中间件应沿用 PyCore 结构扩展。
- B00 / B01 可以自动连续执行，不触发用户门禁；验收标准为静态检查、单元测试和 `GET /health` 通过。
- 涉及前端页面的业务任务必须完成真实联调：后端 API + 前端 `VITE_USE_MOCK=false` 调用真实接口。
- 涉及百炼或 SQLite 向量插件的任务，若外部服务或插件不可用，只能标记降级验收，不能宣称完整联调通过。
- 每个业务功能完成后必须给出前端操作步骤、终端测试指令和预期结果，并等待用户确认再继续下一个功能。

## 五、功能详情

### F01 账号登录与登录态

- 前端：登录页、登录态恢复、退出登录。
- 后端：账号校验、当前用户、退出登录。
- 验收：正确账号进入工作台；错误账号提示；刷新后保持登录；退出后回到登录页。

### F02 客服工作台

- 前端：基础统计、待处理工单、AI 快捷问答入口、知识库快捷入口。
- 后端：工作台统计、快捷工单查询。
- 验收：进入工作台能看到统计与工单；点击工单进入详情；快捷问答返回业务可见答案。

### F03 工单池

- 前端：待接工单列表、关键词/状态/优先级筛选、接取。
- 后端：工单分页查询、接取流转。
- 验收：接取后工单从工单池移入我的工单。

### F04 我的工单

- 前端：我的处理中和已完成工单列表、筛选、进入详情。
- 后端：按当前账号过滤工单。
- 验收：员工只能看到当前账号相关工单。

### F05 工单详情与会话处理

- 前端：工单信息、会话记录、回复编辑器、AI 建议、引用来源、完成工单。
- 后端：工单详情、消息查询与新增、完成工单。
- 验收：员工可采用 AI 建议填入回复，发送消息后会话更新，完成后状态变为已完成。

#### T-013 分层实现思路

- Pydantic 模型：补齐会话消息列表、发送回复请求、发送回复响应、完成工单请求和完成工单响应 DTO，字段严格对齐 `docs/api-contracts.md`。
- Repository：基于现有 `tickets` 与 `conversation_messages` 表，增加按时间顺序查询会话、插入员工回复、提交状态变更的最小数据访问能力。
- Service：复用现有工单可见性逻辑；消息查询只允许当前账号可见的工单；发送回复与完成工单只允许当前账号已接取且未完成的工单；空回复和空摘要返回契约错误。
- Route：新增 `GET /api/tickets/{ticket_id}/messages`、`POST /api/tickets/{ticket_id}/messages`、`POST /api/tickets/{ticket_id}/complete`，保持统一响应格式与 401/403/404/400 错误语义。
- Frontend：仅切换 `frontend/src/services/tickets.ts` 中 P05 相关 service 的真实 API 分支；`TicketDetailPage.vue` 在 `VITE_USE_MOCK=false` 下加载真实消息、发送真实回复，并让完成工单摘要由用户填写。
- 验证：先用后端集成测试覆盖消息顺序、发送回复、完成工单、跨账号 403，再执行真实前后端联调与质量门禁。

### F06 知识库总览

- 前端：QA 数量、文档数量、最近知识列表、入口跳转。
- 后端：知识库统计与最近知识。
- 验收：新增 QA 或文档后，总览统计与最近知识更新。

### F07 QA 库管理

- 前端：QA 列表、搜索、新增、编辑、删除。
- 后端：QA CRUD，并同步生成或更新 Embedding。
- 验收：新增或编辑 QA 后可在智能问答调试中命中。

### F08 文档入库

- 前端：文档列表、上传、状态查看、删除。
- 后端：文件保存、文本抽取、切片、Embedding、入库状态。
- 验收：文档完成入库后可作为回答引用来源。

### F09 智能问答调试

- 前端：输入问题、多轮上下文、回答结果、反问、引用来源。
- 后端：QA 优先命中、模糊反问、文档检索生成。
- 验收：直接问题返回答案，模糊问题返回反问，文档问题返回生成答案与引用。

### F10 账号与基础设置

- 前端：当前账号、模型和数据库配置状态、退出登录。
- 后端：当前账号与系统配置状态。
- 验收：展示当前账号；配置状态只显示是否配置，不展示敏感值。

## 六、开发顺序建议

### 阶段 1：前端 MVP Mock

1. 初始化前端工程与路由布局。
2. 按原型实现 P01 到 P10。
3. 建立 `frontend/src/mocks/`，字段严格对齐 `docs/api-contracts.md`。
4. 完成前端自动验收。
5. 触发用户门禁：用户确认 UI/UX 后进入后端基础设施。

### 阶段 2：后端基础设施

1. 基于 PyCore 初始化 FastAPI 应用、配置、日志、统一响应。
2. 初始化 SQLite schema 与演示数据。
3. 接入健康检查与基础测试。
4. 自动验收：静态检查、单元测试、`GET /health`。

### 阶段 3：逐功能闭环开发

1. F01 账号登录闭环。
2. F03 / F04 / F05 工单与会话闭环。
3. F06 / F07 QA 知识闭环。
4. F08 文档入库闭环。
5. F09 AI 问答闭环。
6. F02 / F10 工作台与设置补齐。

每个功能完成后，前端切到 `VITE_USE_MOCK=false` 调真实后端，并触发用户门禁。

### 阶段 4：E2E 回归与启动文档

1. 跑通“登录 → 接单 → AI 建议 → 回复 → 完成工单 → 维护知识 → 调试验证”。
2. 输出 `docs/startup.md`。
3. 用户做最终业务验收。

## 七、开发前确认项

进入 `/sdd-start` 或“开始开发”前，需要确认：

- Python 指令：项目开发时使用的 Python 命令名称。
- 虚拟环境名称：后端虚拟环境目录名。
- Node.js / npm 可用性：用于 Vue 3 前端开发。
- 百炼 Key 与额度：本地配置已存在，但需开发前实测可调用。
- SQLite 向量插件：确认插件可加载；不可加载时按计划降级。
- 是否允许自动安装项目内依赖：前端和后端依赖由 Agent 在项目内自动安装。

## 八、当前门禁状态

- PRD：已完成。
- 原型：已完成并确认。
- 接口契约：已完成。
- 开发计划：待用户确认。
- 开发：未开始。
