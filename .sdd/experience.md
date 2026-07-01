# 项目经验

> 当前项目长期有效的经验。
> Developer / Tester / Bugfix 在任务完成后维护本文件。

---

## Harness 系统经验摘要

新项目开始时，Developer / Tester / Bugfix 需要同时参考：

- 当前项目经验：`.sdd/experience.md`
- 系统级经验：`<SDD_V6>/memory/harness-experience.md`

---

（项目经验将在开发过程中追加）

### T-001: 前端工程、路由布局与登录设置 Mock
- **陷阱**：项目初始没有 `frontend/` 工程，Vue SFC 的 ESLint flat config 如果未显式配置 `vue-eslint-parser` + TypeScript parser，会把 `<script setup lang="ts">` 中的类型语法解析失败。
- **经验**：前端 Mock 阶段也要先按 `docs/api-contracts.md` 拆分 endpoint DTO；Mock 内部实体可以包含密码、权限标签等模拟字段，但 handler 返回前必须显式映射为契约字段。
- **避坑**：P10 展示配置状态时只能显示 `api_key_configured` 这类布尔状态和模型/数据库名称，不能展示真实 Key、Base URL 或内部链路。

### T-001 修复轮次 1: 设置页 Mock 字段收敛
- **陷阱**：页面组件里的 fallback 文案也会形成业务 Mock 值，容易绕过 `frontend/src/mocks/` 与 `docs/api-contracts.md` 的字段边界。
- **经验**：设置页应只在 `getAccountSettings()` 返回成功后展示账号与系统配置；契约外的权限标签、账号状态等展示字段必须删除或先进入接口契约。
- **避坑**：修复前端 Mock 字段问题时，要同时检查页面模板、Mock 内部实体、DTO mapper 和 service 返回类型，避免只删页面展示但保留契约外字段。
- **[SYSTEM] 建议回传系统级经验**：Mock 阶段页面不得硬编码业务演示值；界面展示字段必须来自 `frontend/src/mocks/` 返回的 endpoint DTO，新增展示字段必须先更新 `docs/api-contracts.md`。

### T-001 修复轮次 2: 顶部账号区 Mock 数据收敛
- **陷阱**：全局布局的顶部账号区也属于业务展示面，不能用业务 Mock 姓名作为兜底值。
- **经验**：账号名称只能来自 auth store 中的当前用户；用户未加载时应不渲染具体名称或使用非业务占位。
- **避坑**：修复 Mock 数据集中管理问题时，必须全局搜索组件、页面、布局中的示例账号名、模型名、数据库名和权限文案，确认业务演示值只存在于 `frontend/src/mocks/`。
- **[SYSTEM] 建议回传系统级经验**：Mock 数据集中管理验收应覆盖全局布局、导航和顶部账号区；组件内不得保留业务 Mock fallback。

### T-002: 客服工作台 Mock
- **陷阱**：P02 原型的“知识总数”与任务验收中的 QA 数量、文档数量不是一一对应卡片关系，直接只展示总数会漏掉文档数量验收点。
- **经验**：工作台 Mock 应以 `GET /api/dashboard/summary` 的 DTO 字段为准，页面可在“知识总数”卡片中同时展示 QA 与文档拆分，既贴近原型又覆盖验收字段。
- **避坑**：AI 快捷问答页面只展示回答正文和引用来源，不要把 `answer_id`、置信度、上下文使用数等契约字段直接暴露到 P02 页面。

### T-003: 工单池与我的工单 Mock
- **陷阱**：`exactOptionalPropertyTypes` 开启时，前端请求对象不能把 `undefined` 显式写进可选字段，否则 `vue-tsc` 会报类型不兼容。
- **经验**：tickets 功能域要按 `GET /api/tickets`、`GET /api/tickets/{ticket_id}`、`POST /api/tickets/{ticket_id}/claim` 分别定义响应 DTO，并由 Mock mapper 显式构造返回体；列表页需要的 `customer_name` 与详情页的 `customer` 不能混用。
- **避坑**：构造筛选请求时先创建基础对象，再只在筛选值存在时写入 `status`、`priority`；Mock 工单内部实体可以复用详情字段，但返回列表、详情、接取响应前必须分别 map。

### T-004: 工单详情与会话处理 Mock
- **陷阱**：工单详情页容易直接复用详情实体承接会话、发送回复和完成工单响应，导致 endpoint DTO 混在一起。
- **经验**：P05 需要把 `ticket detail`、`messages`、`send message`、`complete` 拆成独立类型和 Mock mapper；发送回复的 `used_assistant_answer_id` 只进入请求，不应泄露到消息 DTO。
- **避坑**：AI 建议面板只展示建议正文与引用来源，不展示 answer_id、confidence、context_messages_used、模型版本或内部链路；快捷操作只保留采用建议、查看引用、发送回复和完成工单。

### T-005: 知识库总览与 QA 管理 Mock
- **陷阱**：P07 原型中的状态文案包含已发布、草稿、已归档，但任务和接口契约只允许 `enabled` / `disabled`，不能按原型扩展状态枚举。
- **经验**：知识库 Mock 需要把 overview、recent、QA list、create、update、delete 拆成独立 DTO 和 handler；recent 列表的 QA 与文档也要按契约字段显式映射。
- **避坑**：涉及 QA 状态时，页面展示可用“启用/停用”，但类型、Mock 数据和请求响应只能使用 `enabled` / `disabled`；不要加入审核流、批量导入导出、版本历史或质量评分。

### T-006: 文档入库与智能问答调试 Mock
- **陷阱**：P08 原型表格里有格式、上传时间等展示项，但 T-006 验收和 `docs/api-contracts.md` 要求文档名称、入库状态、切片数量、上传人、更新时间，不能为贴原型向 Mock 增加契约外字段。
- **经验**：documents 功能域需要把列表、上传、详情、删除响应拆成独立 DTO，并由 Mock handler 显式 map；P09 可以展示回答类型、回答正文、缺失实体、引用来源和最近上下文数量，但不要展示 answer_id、请求号、模型版本、原始上下文或内部链路。
- **避坑**：智能问答调试页的连续追问效果应通过 `context_messages` 请求和 `context_messages_used` 业务字段表达，页面不要输出 Context JSON、Trace、原始上下文或模型内部调试字段。

### T-007: 后端基础设施与健康检查
- **陷阱**：PyCore `APIServer` 会默认注册 `/health`，返回格式与本项目 `docs/api-contracts.md` 不一致；项目入口需要在保留 `APIServer` 创建应用的前提下移除默认健康检查，再注册契约版路由。
- **经验**：后端配置可通过项目级 `.env` / `.env.local` 解析后交给 `pycore.core.ConfigManager.load_from_dict()`，同时保持 `use_env` 不介入业务配置，避免进程环境变量覆盖文件配置。
- **避坑**：导入 `pycore.core.get_logger()` 会配置默认日志器；应先完成项目日志配置，再延迟创建 PyCore `APIRouter` 和获取 logger，避免测试或短时启动产生非预期日志文件。

### T-008: SQLite Schema、演示数据与本地文件目录
- **陷阱**：`cd backend && PYTHONPATH=.. ../.venv/bin/python scripts/init_db.py` 直接执行脚本时，Python 默认只把 `backend/scripts` 放进 `sys.path`，需要把 `backend/` 作为包根加入路径后继续使用 `src.*` 导入；不要把 `backend/src` 加入路径后改成裸导入。
- **经验**：SQLite FTS5 虚拟表和触发器不适合塞进 ORM 模型，放在独立 schema helper 中更容易让运行时初始化和临时测试库复用；测试库必须使用临时 SQLite 文件，真实业务库在 pytest 后再单独复查。
- **避坑**：中文 FTS5 探针要使用 seed 中可被 tokenizer 命中的完整短语；上传目录验证应创建、读取并删除探针文件，避免留下测试垃圾。

### T-009: 百炼网关、Embedding 网关与向量插件适配
- **陷阱**：百炼 OpenAI 兼容接口返回结构需要按真实响应确认，不能凭 SDK 或旧 DashScope 结构假设；本机未配置 `SQLITE_VECTOR_EXTENSION_PATH` 时，向量插件探针必须把状态标为降级而不是静默跳过。
- **经验**：百炼 Chat 使用 `BAILIAN_BASE_URL` 指向 OpenAI 兼容网关；Embedding 完整性必需项仅为 `DASHSCOPE_API_KEY`、`BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS`，HTTP 调用可复用网关公共默认 endpoint，并需要校验返回向量维度是否等于 `BAILIAN_EMBEDDING_DIMENSIONS`。
- **避坑**：smoke 脚本只能输出 live/fallback、模型名、响应结构和 usage keys，不输出 API Key、Authorization header、Base URL 或任何可还原密钥片段；SQLite 向量插件不可用时检索适配层要显式报告 FTS5 / LIKE fallback。

### T-009 修复轮次 1: Embedding 配置字段收敛
- **陷阱**：公共 HTTP endpoint 容易被误写进 Embedding 必需配置清单，导致配置状态、错误提示和经验记录偏离任务验收字段。
- **经验**：Embedding 配置完整性检查和错误提示只能列 `DASHSCOPE_API_KEY`、`BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS`；`BAILIAN_BASE_URL` 只能作为百炼网关公共默认 endpoint。
- **避坑**：修复外部服务配置问题时，要同步检查代码状态判断、异常文案、smoke 状态说明和 `.sdd/experience.md`，且不要在任何可读产物中写真实密钥。
- **[SYSTEM] 建议回传系统级经验**：外部服务配置字段清单属于验收契约，公共 endpoint 字段不能被下沉为某个子服务的必需配置。

### T-010: 账号登录与登录态真实闭环
- **陷阱**：真实 Auth token 如果与既有 Mock 页面 token 不一致，登录成功进入 Dashboard 后，尚未切真实的 Mock 页面会把用户判定为未登录并跳回登录页。
- **经验**：第一个真实业务闭环要兼容前端已完成的 Mock 页面；Auth 后端返回契约示例 token，既能命中真实 `/api/auth/*`，也能让未纳入本任务的 Mock 页面继续可用。
- **避坑**：全局 401 拦截器不能处理 `/auth/login` 的错误密码响应，否则登录页错误提示会被重定向刷新掉；登录接口的 401 应交给页面展示清晰失败提示。

### T-011: 工单池查询、筛选与接取真实闭环
- **陷阱**：用并发命令验证“接取后列表移除”时，查询可能和接取同时发出，导致查询结果仍是接取前状态；真实验证这类状态流转必须顺序执行。
- **经验**：P03 退出 Mock 时只需要让 `getTickets` 和 `claimTicket` 在 `VITE_USE_MOCK=false` 下走真实 API，其它工单详情/会话接口应留给后续任务，避免越界实现 T-012 或 P05。
- **避坑**：接取接口不能信任前端传入的 `employee_id` 作为最终归属，必须校验并绑定当前 Bearer token 对应账号；验证完成后要重新执行 `scripts/init_db.py` 恢复可重复 seed 状态。

### T-012: 我的工单与账号数据隔离真实闭环
- **陷阱**：详情入口切到真实接口后，既有 P05 页面仍可能继续加载 Mock 会话、AI 建议、回复和完成工单，容易越界实现后续任务并在真实模式混入 Mock-only 展示。
- **经验**：`scope=mine` 要在后端按当前认证账号过滤，并在 seed 中保留最小跨员工工单作为隔离验证样本；前端 tickets service 需要按 endpoint 分别判断 `VITE_USE_MOCK`，列表和详情入口在真实模式都必须走 axios API。
- **避坑**：T-012 只打开详情入口和基础工单信息；真实模式下不要触发 P05 会话、回复、完成工单等尚未闭环的 Mock 分支。

### T-012 修复轮次 1: 双账号 token 隔离与真实 API 默认环境
- **陷阱**：业务查询层按 `assignee_id` 过滤仍不够；如果登录返回固定 token，后登录账号会覆盖 token 到用户的映射，旧 token 的 `/me` 和 `scope=mine` 都会漂移到新账号。
- **经验**：登录必须生成会话级唯一 token，并在 token store 中按 token 独立映射 user_id；隔离测试要保留账号 A 的旧 token，再登录账号 B 后复查账号 A 的 `/api/auth/me` 和 `/api/tickets?scope=mine`。
- **避坑**：退出 Mock 的集成任务要同步检查 `frontend/.env` 默认值，确保 `VITE_API_BASE_URL=/api`、`VITE_USE_MOCK=false`、`VITE_BACKEND_PROXY_TARGET=http://localhost:8099` 一起成立。

### T-013: 工单详情、会话回复与完成工单真实闭环
- **陷阱**：T-012 为了避免越界，在真实模式下跳过了 P05 会话、回复和完成工单区域；退出 Mock 时不能只切 service，还要恢复页面真实模式下的会话面板和完成入口。
- **经验**：工单详情读权限和工单处理写权限要分开：open 无归属工单可读，但发送回复和完成工单只允许当前账号已接取且状态为 processing 的工单。
- **避坑**：真实联调会写入本地 SQLite，验证完成后要清理手工回复和完成状态，避免污染后续任务的演示 seed；AI 建议和引用来源继续留给 T-017，不在 T-013 提前接真实问答。

### T-014: 知识库总览与 QA 管理真实闭环
- **陷阱**：知识库闭环不只是 QA CRUD；P06 总览、最近知识、P07 列表和 `VectorIndex` metadata 必须一起更新，否则页面看起来可用但检索状态会留下脏索引。
- **经验**：Embedding 结果应区分 live 与 fallback；只有百炼 Embedding 调用成功并返回期望维度时才标记 `completed`，配置缺失或调用失败时 QA CRUD 仍可成功但必须返回 `fallback`。
- **避坑**：真实联调新增 QA 后要同时检查 P07 列表、P06 数量和最近知识，再清理测试 QA 与关联 `vector_indexes`；SQLite vector 插件不可用时只可宣称 FTS5/LIKE 降级，不可宣称完整向量插件联调。

### T-015: 文档入库真实闭环
- **陷阱**：文档入库验收中的“Embedding 写入 SQLite”不能只保存 `embedding_model` 和 `vector_dimension` 元数据；Tester 会按真实向量值是否可读回判断闭环。
- **经验**：`VectorIndex` 需要保留可空的 embedding JSON 字段，QA 等历史 metadata 可继续为空；文档 chunk embedding 成功时按 chunk 顺序序列化写入 SQLite，Embedding 失败时仍保存 chunks 并走 FTS5/LIKE fallback。
- **避坑**：为既有 SQLite 表新增列时，`Base.metadata.create_all()` 不会自动迁移，初始化路径要通过 `PRAGMA table_info` + `ALTER TABLE` 做轻量兼容；真实联调上传文档后必须同时验证物理文件、chunks、vectors、检索命中和删除后全部清理。

### T-016: 检索与智能问答调试真实闭环
- **陷阱**：FTS5 的 `bm25` 分数适合排序，不适合作为 QA direct 的业务相似度阈值；直接拿它判断 `>= 0.8` 会让中文短句命中不可控。
- **经验**：QA 优先命中需要在 FTS5/LIKE 召回后再做确定性词面重排：精确问题为 `1.0`，子串命中为 `0.9`，高重合为 `0.8+`，这样既能保留 FTS5 fallback，又能让阈值验收稳定。
- **避坑**：P09 退出 Mock 时除了 service 分流，还要浏览器确认 `data-api-mode=real`、Network 命中 `/api/assistant/ask`，并静态排查模型版本、请求号、原始上下文、prompt、trace 等内部调试信息没有露出。

### T-017: 工单详情 AI 建议与引用真实闭环
- **陷阱**：P05 在前序任务中为了避免越界曾用 `isMockMode` 隐藏 AI 面板；退出 Mock 时只切 service 不够，还要解除模板上的真实模式限制。
- **经验**：`answer_id` 可以作为前端内部状态传给 `used_assistant_answer_id`，但页面只能展示回答类型、正文、缺失字段和引用标题/片段/类型，不能展示 answer_id、confidence、上下文数量、匹配度或模型链路。
- **避坑**：真实联调发送回复会写 SQLite，优先使用临时 runtime DB；若用默认库，回复内容必须带唯一标记并在验收后删除，避免污染后续 E2E。

### T-018: 客服工作台与账号设置真实闭环
- **陷阱**：`VITE_USE_MOCK=false` 下即使运行时没有调用 mock 函数，service 顶层静态 `import '@/mocks'` 也会让 Vite dev 浏览器网络加载 `/src/mocks/*.ts`，严格验收会判定仍命中 Mock。
- **经验**：dashboard 统计应由后端按当前用户和真实 SQLite 计算，P02 快捷问答只展示 answer、missing_fields、references 等业务字段；P10 settings 只能返回数据库、模型和 `api_key_configured` 等状态字段，不能返回 Key、Token、Base URL 或可还原片段。
- **避坑**：real/mock 分支服务应在 mock 分支内动态 `await import('@/mocks')`；浏览器验收要包含静态资源网络检查，并使用临时 SQLite DB，避免 `init_db.py` 或联调写入污染默认演示库。

### T-019: E2E 回归与 startup 文档
- **陷阱**：启动文档既不能写明文演示密码，又必须让新开发者能完成登录；只写“以 seed 为准”会让文档可执行性不足，写固定密码又会触发敏感信息验收风险。
- **经验**：最终收口任务适合采用 Planner / Developer / Spec Reviewer / Quality Reviewer / Tester 链路；完整 E2E 可由 Developer 跑一遍，后续 reviewer 聚焦规格、质量、敏感信息、清理和门禁复核，避免反复污染运行库。
- **避坑**：startup 文档应提供本机安全重置演示密码命令，使用静默输入和 bcrypt hash 写入本地 SQLite，不记录明文；最终报告要诚实说明无 tracked baseline 时不能用 `git diff` 单独证明变更边界，并确认 `.playwright-cli`、临时 DB、上传目录和端口都已清理。
