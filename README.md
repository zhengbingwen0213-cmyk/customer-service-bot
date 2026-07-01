# Customer Service Bot

智能客服 MVP，面向客服团队的工单处理、知识库维护、文档入库和智能问答调试场景。项目由 SDD V7_2 流程管理，当前版本已完成本地真实后端模式的端到端验收。

## 功能范围

- 客服登录与会话鉴权。
- 工作台指标、待处理工单和知识库概览。
- 工单池、我的工单、工单详情、接单、回复、完成工单。
- AI 建议与智能问答调试，支持外部模型不可用时的清晰降级。
- QA 知识库维护、启停、检索和统计。
- 文档上传、入库任务队列、文档切片、FTS5 / LIKE 降级检索。
- 账号与基础配置状态查看。

## 技术栈

- Frontend：Vue 3、Vite、TypeScript、Pinia、Vue Router、Axios。
- Backend：FastAPI、Pydantic、SQLAlchemy Async、SQLite、FTS5、pytest、ruff、mypy。
- Runtime：Python 3.12、Node.js、npm。
- Process：SDD V7_2 任务、测试报告和人工验收记录。

## 快速启动

后端依赖：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

前端依赖：

```bash
cd frontend
npm install
```

初始化本地 SQLite 演示库：

```bash
cd /path/to/customer-service-bot
PYTHONPATH=.:backend .venv/bin/python backend/scripts/init_db.py
```

启动后端：

```bash
PYTHONPATH=.:backend .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099 --app-dir backend
```

启动前端：

```bash
cd frontend
VITE_API_BASE_URL=/api \
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8099 \
VITE_USE_MOCK=false \
npm run dev -- --host 127.0.0.1 --port 5199
```

访问：

```text
http://127.0.0.1:5199
```

本地演示账号用户名为 `agent01`。演示密码以 seed 或本机安全配置为准；如果新环境不知道密码，请按 [启动指南](docs/startup.md) 的“初始化数据库”章节重置本机演示密码。

## 环境配置

后端会依次读取项目根目录 `.env`、项目根目录 `.env.local`、`backend/.env`、`backend/.env.local`。本地配置建议复制：

```bash
cp backend/.env.example backend/.env.local
```

常用字段：

```dotenv
DATABASE_PATH=backend/data/customer_service.db
UPLOAD_DIR=backend/uploads
LOG_FILE_ENABLED=false
DASHSCOPE_API_KEY=
BAILIAN_BASE_URL=
SQLITE_VECTOR_EXTENSION_PATH=
```

前端真实后端模式：

```dotenv
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8099
```

不要提交真实 API Key、Token、密码、私有 Base URL、本地数据库或上传文件。

## 验证命令

后端：

```bash
.venv/bin/python -m ruff check backend/src backend/tests
.venv/bin/python -m mypy backend/src backend/tests
.venv/bin/python -m pytest backend/tests -q
```

前端：

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

冷启动验证可参考 [docs/startup.md](docs/startup.md)，从 GitHub 重新 clone 后安装依赖、初始化数据库并启动前后端。

## 目录结构

```text
.
├── backend/              # FastAPI 后端、数据库、服务层和测试
├── frontend/             # Vue 前端应用
├── pycore/               # 项目使用的 Python 基础能力封装
├── docs/                 # PRD、API 契约、启动指南、原型与计划
├── .sdd/                 # SDD 任务、状态、测试报告和经验记录
├── AGENTS.md             # AI Coding 入口说明
└── README.md
```

## 项目状态

- MVP 首次可运行版本已完成。
- 本地真实后端模式已完成人工验收。
- 初始提交已推送至 GitHub。
- 当前建议版本标签：`v0.1.0-mvp`。

更多启动、降级策略、安全说明和排错信息见 [docs/startup.md](docs/startup.md)。
