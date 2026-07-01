# 测试报告：T-007 后端基础设施与健康检查

**测试时间**：2026-05-24 11:39:50 CST
**Tester Agent ID**：codex-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户或 Tester 打开后端健康检查地址时，能看到服务正常的成功响应。 | PASS | 使用 `cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 短时启动成功；`GET http://127.0.0.1:8099/health` 返回 `{"code":200,"message":"success","data":{"status":"ok","service":"customer-service-bot-api","time":"2026-05-24T11:38:16.689180+08:00"}}`。验证后确认 8099 无残留监听进程。 |
| 2 | 前端页面仍可在 Mock 模式打开，后端基础设施完成后不要求用户进行页面验收。 | PASS | `frontend/.env:2` 为 `VITE_USE_MOCK=true`；执行 `npm run build` 通过，输出 `✓ built in 418ms`。未进行用户页面验收。 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|------|------|------|
| 1 | `backend/src/main.py` 基于 `pycore.api.APIServer` 创建应用，不自行重写 FastAPI server 核心能力 | PASS | `backend/src/main.py:6` 导入 `APIConfig` / `APIServer`，`backend/src/main.py:19` 通过 `APIServer(APIConfig(...))` 创建服务，`backend/src/main.py:72` 暴露 `api_server.app`。未发现 `FastAPI()` 实例化。 |
| 2 | `backend/src/core/config.py` 基于 `pycore.core.ConfigManager` 读取配置，敏感值只从 `.env` 或 `.env.local` 读取 | PASS | `backend/src/core/config.py:9` 导入 `ConfigManager`，`backend/src/core/config.py:98-100` 使用 `ConfigManager.instance().load_from_dict(...)` 加载设置；`backend/src/core/config.py:115-119` 只读取项目根和 backend 下的 `.env` / `.env.local`。`rg` 未发现 `os.environ` / `os.getenv` / `use_env`。 |
| 3 | `backend/src/api/deps.py` 基于 pycore 模板扩展路由级依赖 | PASS | `backend/src/api/deps.py:11-36` 保留 `HTTPBearer`、`get_current_user`、`require_admin` 的路由级依赖结构，并按项目规范从 `src.db.session` 导入 `get_db`（`backend/src/api/deps.py:9`）。 |
| 4 | CORS 中间件已注册，统一响应与统一错误格式符合 `docs/api-contracts.md` | PASS | `backend/src/main.py:27-30` 启用 CORS 配置，运行时 `app.user_middleware` 为 `['RequestContextMiddleware', 'CORSMiddleware']`；`backend/src/api/routes/health.py:23-34` 返回 `code/message/data` 成功包，`backend/src/api/errors.py:44-52` 返回 `code/message/data: null` 错误包；`backend/tests/test_health.py:11-44` 覆盖健康检查、404 错误包和 CORS 预检。 |
| 5 | `pyproject.toml` 已配置 ruff、mypy、pytest | PASS | `pyproject.toml:1-17` 配置 ruff，`pyproject.toml:19-31` 配置 mypy，`pyproject.toml:33-36` 配置 pytest。 |
| 6 | `.venv/bin/python -m ruff check backend/src backend/tests` 通过 | PASS | 命令输出：`Python 3.12.12`、`All checks passed!`。按当前项目实际解释器 `.venv/bin/python` 执行。 |
| 7 | `.venv/bin/python -m mypy backend/src backend/tests` 通过 | PASS | 命令输出：`Success: no issues found in 16 source files`。 |
| 8 | `.venv/bin/python -m pytest backend/tests` 通过 | PASS | 命令输出：`3 passed, 11 warnings in 0.19s`。警告来自 `pycore/` 的 Pydantic deprecation，不作为项目业务质量门禁失败。 |
| 9 | `cd backend && PYTHONPATH=.. ../.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port <free-port>` 可短时启动 | PASS | 8099 启动成功并完成 `/health` 请求；验证后 `lsof -nP -iTCP:8099 -sTCP:LISTEN` 无输出。 |
| 10 | `GET /health` 返回 200，响应格式符合 `docs/api-contracts.md` | PASS | 实测响应包含 `code: 200`、`message: "success"`、`data.status: "ok"`、`data.service: "customer-service-bot-api"`、ISO 8601 `data.time`，与 `docs/api-contracts.md` 中 `/health` 契约一致。 |
| 11 | `pycore/` 未被纳入项目业务代码质量门禁 | PASS | 实际执行命令均只指定 `backend/src backend/tests`；`pyproject.toml:4` ruff `src` 为 `["backend/src", "backend/tests"]`，`pyproject.toml:9` 排除 `pycore`，`pyproject.toml:22-23` mypy 仅检查 `backend/src` / `backend/tests` 并排除 `^pycore/`。 |

## 补充检查

- 硬编码敏感值扫描：`rg` 仅在 `docs/api-contracts.md` 发现示例 `Bearer access_token_demo`，未发现真实 Key / Token / Secret 泄露。
- HTTP 客户端检查：`backend/src` 未发现 `httpx.Client` / `httpx.AsyncClient` 或裸 `httpx.get/post` 调用。
- 测试数据库隔离检查：`backend/tests` 未发现 `drop_all`、直接导入运行时 `engine` / `async_session_maker` 后清表等行为；T-007 未要求创建业务表或 seed 数据，`backend/data` 下无运行时数据库文件需要校验。

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | pytest 执行时 `pycore/` 依赖产生 Pydantic V2 deprecation warnings。 | pycore 框架依赖 | 如后续维护 pycore 框架，可单独创建框架兼容性任务；不影响 T-007 项目业务代码验收。 |
