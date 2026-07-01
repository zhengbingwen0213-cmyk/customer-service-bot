# 测试报告：T-001 前端工程、路由布局与登录设置 Mock

**测试时间**：2026-05-23 17:48:42 CST
**Tester Agent ID**：codex-tester
**复验轮次**：2

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户在登录页看到符合原型的账号输入框、密码输入框、登录按钮和错误提示区域。 | PASS | `frontend/src/pages/LoginPage.vue:65` 至 `frontend/src/pages/LoginPage.vue:106` 实现登录名、密码、错误提示区域和登录按钮；文案与 `docs/prototypes/01-登录页/index.html:154` 至 `docs/prototypes/01-登录页/index.html:183` 一致。 |
| 2 | 用户输入 Mock 账号密码并点击登录，页面进入登录后的后台布局，左侧导航、顶部账号区和内容区正常显示。 | PASS | `frontend/src/mocks/auth.ts:81` 至 `frontend/src/mocks/auth.ts:107` 返回 Mock 登录数据；`frontend/src/stores/auth.ts:31` 至 `frontend/src/stores/auth.ts:46` 写入登录态；`frontend/src/components/AppLayout.vue:40` 至 `frontend/src/components/AppLayout.vue:70` 提供左侧导航、顶部账号区和内容区。 |
| 3 | 用户进入账号与基础设置页，看到当前账号、模型和数据库配置状态的演示信息，页面不展示真实密钥或内部链路。 | PASS | `frontend/src/pages/SettingsPage.vue:16` 至 `frontend/src/pages/SettingsPage.vue:24` 从 `getAccountSettings()` 读取设置；`frontend/src/pages/SettingsPage.vue:51` 至 `frontend/src/pages/SettingsPage.vue:76` 只展示账号名、登录名、数据库、模型和 API Key 配置状态，未展示真实 Key、Base URL 或内部链路。 |
| 4 | 用户点击退出登录后回到登录页；本任务只验证 Mock 登录态，不要求真实后端、真实模型或真实数据库。 | PASS | `frontend/src/components/AppLayout.vue:26` 至 `frontend/src/components/AppLayout.vue:29` 和 `frontend/src/pages/SettingsPage.vue:27` 至 `frontend/src/pages/SettingsPage.vue:30` 调用 Mock logout 后跳转登录页；`frontend/src/services/auth.ts:1` 至 `frontend/src/services/auth.ts:23` 只接入 `frontend/src/mocks/`。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | Frontend typecheck passes | PASS | 已执行 `npm run type-check`，退出码 0。 |
| 2 | Frontend lint passes | PASS | 已执行 `npm run lint`，退出码 0。 |
| 3 | Frontend build passes | PASS | 已执行 `npm run build`，退出码 0；Vite build 完成。 |
| 4 | Mock 登录、当前账号、退出登录和设置数据字段与 docs/api-contracts.md 一致 | PASS | `frontend/src/types/auth.ts:1` 至 `frontend/src/types/auth.ts:30`、`frontend/src/types/settings.ts:3` 至 `frontend/src/types/settings.ts:15` 与 `docs/api-contracts.md:84` 至 `docs/api-contracts.md:92`、`docs/api-contracts.md:240` 至 `docs/api-contracts.md:335`、`docs/api-contracts.md:1243` 至 `docs/api-contracts.md:1271` 对齐；未发现 `permission_label`、`display_name` 或“标准客服权限”。 |
| 5 | Mock 数据集中存放在 frontend/src/mocks/，不得写入真实 Key、密码或外部服务凭证 | PASS | 业务 Mock 值集中在 `frontend/src/mocks/auth.ts:32` 至 `frontend/src/mocks/auth.ts:48`；`frontend/src/components/AppLayout.vue:20` 已移除上一轮硬编码的 `客服一组员工` 兜底，仅展示 `authStore.user?.name`。全局搜索未发现真实 API Key、外部服务凭证或组件/页面中的业务 Mock 值散落。 |

## 重点复验项

| # | 复验项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | `frontend/src/components/AppLayout.vue` 是否仍硬编码业务 Mock 账号名，比如 `客服一组员工`。 | PASS | `frontend/src/components/AppLayout.vue:20` 为 `authStore.user?.name ?? ''`；`rg "客服一组员工" frontend/src --glob '!frontend/src/mocks/**'` 无命中。 |
| 2 | 组件/页面中是否还有业务 Mock 演示值散落，业务展示数据是否集中在 `frontend/src/mocks/`。 | PASS | 账号、数据库、模型等展示值在 `frontend/src/pages/SettingsPage.vue` 中均来自 `user` / `system` 动态绑定；业务值来源为 `frontend/src/mocks/auth.ts:32` 至 `frontend/src/mocks/auth.ts:48`。 |
| 3 | 是否仍展示 `api-contracts.md` 未定义字段。 | PASS | `frontend/src/types/auth.ts` 与 `frontend/src/types/settings.ts` 仅声明契约字段；`rg "permission_label|display_name|标准客服权限" frontend/src` 无命中。 |

## 验证命令

| 命令 | 结果 |
|------|------|
| `npm run type-check` | PASS |
| `npm run lint` | PASS |
| `npm run build` | PASS |
| `npm run dev -- --host 127.0.0.1 --port 5199` + `curl -I http://127.0.0.1:5199/`、`curl -I http://127.0.0.1:5199/settings` | PASS，两个入口均返回 HTTP 200；验证后已关闭 5199 服务，`lsof -nP -iTCP:5199 -sTCP:LISTEN` 无监听进程。 |

## 本轮复验结论

- 已修复：`frontend/src/components/AppLayout.vue` 不再硬编码 `客服一组员工` 兜底值。
- 已修复：组件/页面未发现账号、模型、数据库等业务 Mock 展示值散落。
- 已修复：未发现 `api-contracts.md` 未定义字段展示或类型声明。
