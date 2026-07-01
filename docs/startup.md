# 启动指南

本文档用于在本地启动智能客服 MVP，并以真实后端模式完成登录、工作台、接单、工单详情、AI 建议、回复、完成工单、QA 维护、文档入库和智能问答调试流程。

## 环境要求

- Python 3.12，建议使用项目根目录下的 `.venv`。
- Node.js 与 npm，前端依赖 Vite、Vue、TypeScript。
- SQLite 3，需支持 FTS5。
- 本地文件写入权限，后端会写入 SQLite 数据库、上传目录和可选日志目录。
- 可选：百炼 / DashScope 文本生成与 Embedding 调用权限。
- 可选：SQLite vector 扩展；未配置时系统按 FTS5 / LIKE 降级检索。

## 依赖安装

后端：

```bash
cd /path/to/customer-service-bot
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

前端：

```bash
cd /path/to/customer-service-bot/frontend
npm install
```

## 配置字段

后端会依次读取项目根目录 `.env`、项目根目录 `.env.local`、`backend/.env`、`backend/.env.local`。本地建议复制 `backend/.env.example` 为 `backend/.env.local` 后按需修改。

只提交字段名和占位值，不要把真实 API Key、Token、密码或可还原的服务地址写入仓库：

```dotenv
SERVICE_NAME=customer-service-bot-api
ENVIRONMENT=local
DEBUG=false
HOST=127.0.0.1
PORT=8099
CORS_ORIGINS=["http://localhost:5199","http://127.0.0.1:5199"]
CORS_METHODS=["*"]
CORS_HEADERS=["*"]
DATABASE_PATH=backend/data/customer_service.db
DATABASE_URL=
UPLOAD_DIR=backend/uploads
DASHSCOPE_API_KEY=
BAILIAN_BASE_URL=
BAILIAN_CHAT_MODEL=qwen-plus
BAILIAN_EMBEDDING_MODEL=text-embedding-v4
BAILIAN_EMBEDDING_DIMENSIONS=1024
SQLITE_VECTOR_EXTENSION_PATH=
LOG_FILE_ENABLED=false
LOG_DIR=backend/logs
```

前端运行时字段：

```dotenv
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8099
```

字段说明：

- `DATABASE_PATH` / `DATABASE_URL`：SQLite 数据库位置；通常只配置 `DATABASE_PATH`。
- `UPLOAD_DIR`：文档上传和解析后的本地文件目录。
- `DASHSCOPE_API_KEY`：百炼 / DashScope 调用凭据；留空时进入模型不可用或降级路径。
- `BAILIAN_BASE_URL`：百炼兼容接口地址；使用真实地址时只保存在本机 `.env.local`。
- `BAILIAN_CHAT_MODEL`：文本生成模型名。
- `BAILIAN_EMBEDDING_MODEL`、`BAILIAN_EMBEDDING_DIMENSIONS`：Embedding 模型及向量维度。
- `SQLITE_VECTOR_EXTENSION_PATH`：SQLite vector 扩展路径；留空时使用 FTS5 / LIKE。
- `VITE_API_BASE_URL`：前端 API 基础路径，推荐使用 `/api` 走 Vite 代理。
- `VITE_USE_MOCK`：`false` 表示真实后端模式，`true` 仅用于前端演示。
- `VITE_BACKEND_PROXY_TARGET`：Vite 将 `/api` 代理到的后端地址。

## 初始化数据库

在项目根目录执行：

```bash
PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py
```

该命令会创建数据库表、初始化本地演示数据、验证 FTS5 关键字检索，并确保上传目录可用。本地演示账号仅用于本机开发与验收：

- 用户名：`agent01`
- 密码：以 seed 或本机安全配置为准；本文档不记录明文密码。

如新开发者不知道本机演示密码，可在初始化数据库后，在项目根目录执行以下命令重置 `agent01` 的本机 SQLite 开发库密码。命令会静默读取你输入的密码，只把 bcrypt hash 写入本机数据库；不要提交 `.env.local`、数据库文件或密码。

```bash
read -r -s DEMO_PASSWORD
export DEMO_PASSWORD
PYTHONPATH=.:backend .venv/bin/python - <<'PY'
import os
import sqlite3
from pathlib import Path

import bcrypt

raw_password = os.environ.get("DEMO_PASSWORD", "")
if not raw_password:
    raise SystemExit("密码不能为空。")

database_path = Path(os.environ.get("DATABASE_PATH", "backend/data/customer_service.db"))
password_hash = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

with sqlite3.connect(database_path) as connection:
    cursor = connection.execute(
        "update users set password_hash = ? where username = ?",
        (password_hash, "agent01"),
    )
    if cursor.rowcount != 1:
        raise SystemExit("未找到本地演示账号 agent01，请先初始化数据库。")

print("已更新本地演示账号 agent01 的密码。")
PY
unset DEMO_PASSWORD
```

如果使用自定义数据库位置，请先在同一个终端设置 `DATABASE_PATH`，例如指向你的本机 SQLite 开发库路径。

## 启动后端

在项目根目录执行：

```bash
PYTHONPATH=.:backend .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099 --app-dir backend
```

健康检查：

```bash
curl -s http://127.0.0.1:8099/health
```

## 启动前端

另开一个终端：

```bash
cd /path/to/customer-service-bot/frontend
VITE_API_BASE_URL=/api \
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8099 \
VITE_USE_MOCK=false \
npm run dev -- --host 127.0.0.1 --port 5199
```

浏览器打开：

```text
http://127.0.0.1:5199
```

真实后端模式下，浏览器控制台应满足：

```js
document.documentElement.dataset.apiMode === 'real'
```

## Mock 模式与真实模式

- `VITE_USE_MOCK=false`：真实后端模式。页面应请求 `/api/...`，不应加载 `/src/mocks`、`frontend/src/mocks` 或 `mocks/*.ts` 静态资源。
- `VITE_USE_MOCK=true`：前端演示模式。仅用于无后端时查看页面，不用于最终 E2E 验收。
- 最终回归页面不应出现 `[Mock]`、`Mock-only`、Mock 账号提示或其他仅 Mock 模式文案。

## 外部服务与降级

- 百炼聊天可用时，工单详情 AI 建议和智能问答调试会返回 live 模型结果。
- 百炼聊天不可用或未配置时，页面应展示清晰失败或降级提示；测试报告只能标注 unavailable / fallback，不能宣称 live。
- 百炼 Embedding 可用时，QA 和文档入库会写入 embedding 状态。
- 百炼 Embedding 不可用时，知识检索仍可通过 FTS5 / LIKE 等降级路径返回可解释结果或提示。
- SQLite vector 扩展未配置时，系统使用 FTS5 / LIKE 降级；报告需明确写明 `SQLite vector fallback to FTS5/LIKE`。

## 验证命令

后端质量门禁：

```bash
.venv/bin/python -m ruff check backend/src backend/tests
.venv/bin/python -m mypy backend/src backend/tests
.venv/bin/python -m pytest backend/tests -q
```

前端质量门禁：

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

真实模式静态检查：

```bash
rg -n "from ['\"]@/mocks|from ['\"]\\.\\./mocks|^import .*mock" frontend/src/services frontend/src/stores frontend/src/pages -g '*.ts' -g '*.vue'
```

预期没有真实运行路径的顶层 mock import；允许在 mock 分支内动态加载 mocks，但 `VITE_USE_MOCK=false` 时浏览器网络不应请求 mock 文件。

## 常见问题

- 端口占用：检查 `lsof -iTCP:8099 -sTCP:LISTEN` 和 `lsof -iTCP:5199 -sTCP:LISTEN`，停止旧进程后重启。
- 登录后又回登录页：确认前端以 `VITE_USE_MOCK=false` 启动，后端 `/api/auth/login` 返回 200，浏览器没有旧 token 干扰。
- 页面仍像 Mock：确认环境变量拼写正确，刷新页面后检查 `document.documentElement.dataset.apiMode` 和 Network 面板。
- 模型服务不可用：检查 `DASHSCOPE_API_KEY`、`BAILIAN_BASE_URL`、模型名和本机网络；不要把真实值写入文档或报告。
- 文档上传失败：确认 `UPLOAD_DIR` 存在且当前用户可写。
- 检索没有向量命中：确认 `SQLITE_VECTOR_EXTENSION_PATH` 是否配置；未配置时按 FTS5 / LIKE 降级验收。
- macOS 首次启动较慢：前端依赖预构建和后端 bcrypt / aiosqlite 初始化可能需要数秒。

## 安全说明

- 不要提交真实 API Key、Token、密码、私有 Base URL 或可还原的密钥片段。
- `backend/.env.local`、本地数据库、上传目录和测试样本应只保存在本机。
- Settings 页面只应展示账号信息和配置状态，不展示 Key、Token、Base URL、secret 或 URL 明文。
- 测试报告只能记录字段是否配置、live / fallback 状态、脱敏后的接口路径和 HTTP 状态。
