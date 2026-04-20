# EasyShorts AI

EasyShorts AI 是一个面向 AI 资讯场景的智能处理平台，围绕“来源采集 -> 内容处理 -> Agent 分析 -> 热点聚合 -> 推送计划”搭了一条可观测、可追踪、可配置的工作流。

当前仓库已经不再停留在文档草案阶段，而是包含一套可运行的前后端管理后台：你可以维护新闻来源、查看采集记录、处理内容、触发 Agent 运行、查看热点池和推送计划，并通过系统配置接入真实模型与推送渠道。

## 界面预览

### 平台首页

![平台首页](./doc/screenshots/home.png)

### AI 热点监控

![AI 热点监控](./doc/screenshots/hot-monitor.png)

### 来源管理

![来源管理](./doc/screenshots/sources.png)

### 内容中心

![内容中心](./doc/screenshots/news-list.png)

### Agent 运行中心

![Agent 运行中心](./doc/screenshots/agent-runs.png)

### 推送计划

![推送计划](./doc/screenshots/push-plans.png)

## 当前核心能力

- 来源管理：支持 `RSS`、`ATOM`、`WEB`、`MANUAL` 四类新闻源，支持手动同步和定时采集。
- 内容处理：对采集内容进行清洗、去重、翻译、摘要、标签分类和质量过滤。
- Agent 智能处理：基于 AgentScope 串起分类、摘要、热点识别、推送规划等处理步骤。
- 热点池与推送：沉淀热点主题、生成推送计划、记录执行结果，支持 webhook 和 email 等渠道扩展。
- 基础设施：内置 JWT 登录、RBAC 权限、菜单管理、系统配置、任务中心、日志中心和文件上传。

## 工作流

```text
新闻来源
  -> 采集记录
  -> 内容中心
  -> 内容处理
  -> Agent 运行
  -> 热点池
  -> 推送计划
  -> 推送记录
```

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy + Alembic
- 异步任务：Celery + Redis
- 数据库：PostgreSQL
- 智能处理：AgentScope
- 模型默认值：`qwen3.5-plus`
- 部署与运行：Docker / 本机开发环境

## 本地启动

### 1. 启动后端

```bash
cd /Users/lfc/softwear/EasyShortsAI
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python scripts/bootstrap_admin.py
../.venv/bin/uvicorn app.main:app --reload --port 8000
```

默认数据库连接建议使用：

```text
postgresql+psycopg://postgres:123456@localhost:5432/easy_shorts
```

如果要启用真实模型能力，在 `backend/.env` 中补充：

```text
DASHSCOPE_API_KEY=你的 DashScope Key
AGENT_DEFAULT_PROVIDER=dashscope
AGENT_DEFAULT_MODEL_NAME=qwen3.5-plus
```

如果要跑异步任务，还需要另外启动：

```bash
cd /Users/lfc/softwear/EasyShortsAI/backend
../.venv/bin/celery -A app.core.celery_app.celery_app worker -l info -Q system_queue,news_queue,content_queue
```

### 2. 启动前端

```bash
cd /Users/lfc/softwear/EasyShortsAI/frontend
npm install
npm run dev
```

启动后可访问：

- 前端：`http://localhost:5173/`
- 后端接口文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/easy-shorts/health`

## 默认账号

- 管理员：`admin / Admin@123456`
- 运营账号：`operator / Operator@123456`

## 仓库结构

```text
EasyShortsAI/
  backend/        FastAPI、Celery、Agent、数据模型与测试
  frontend/       Vue 3 管理后台
  doc/            需求、架构、接口、开发计划与截图
```

## 文档索引

- [需求文档](./doc/需求文档.md)
- [需求文档 v2](./doc/需求文档v2.md)
- [需求文档 v3](./doc/需求文档v3.md)
- [技术架构文档](./doc/技术架构文档.md)
- [开发计划文档](./doc/开发计划文档.md)
- [后端接口文档](./doc/后端接口文档.md)
- [采集开发文档](./doc/采集开发文档.md)
- [Agent 智能处理模块](./doc/Agent智能处理模块.md)

## 当前进度

目前这套仓库已经完成了以下落地部分：

- 后端基础设施与 RBAC
- 新闻来源、采集记录、内容中心
- 内容处理链路
- Agent 运行、热点池、推送计划与推送记录
- 前端管理后台主要页面
- 文档、接口、测试与默认数据初始化

后续如果继续往前推进，最自然的方向会是：

1. 完善更多来源站点的采集适配器
2. 接入更稳定的登录态 / 反爬方案
3. 增强热点聚类和推送策略
4. 补齐推送渠道的真实配置与运维能力
