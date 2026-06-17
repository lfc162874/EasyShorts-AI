# EasyShorts AI

EasyShorts AI 是一个面向 AI 资讯场景的智能处理平台，围绕"来源采集 -> 内容处理 -> Agent 分析 -> 热点聚合 -> 推送计划"搭了一条可观测、可追踪、可配置的工作流。

当前仓库包含一套可运行的前后端管理后台：你可以维护新闻来源、查看采集记录、处理内容、触发 Agent 运行、查看热点池和推送计划，并通过系统配置接入真实模型与推送渠道。

> **后端已从 Python (FastAPI) 重构为 TypeScript (NestJS)**，新后端位于 `backend-ts/` 目录，前端零改动即可对接。原 Python 后端保留在 `backend/` 目录作为历史参考。

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

- **来源管理**：支持 `RSS`、`ATOM`、`WEB`、`MANUAL` 四类新闻源，支持手动同步和定时采集。
- **内容处理**：对采集内容进行清洗、去重、翻译、摘要、标签分类和质量过滤。
- **Agent 智能处理**：基于 AgentScope（TypeScript 版）串起热点判断、分类、摘要、内容增强、推送规划等处理步骤，采用 **AI-First Rule-Fallback** 模式——优先调用 LLM，不可用时自动降级为规则逻辑。
- **热点池与推送**：沉淀热点主题、生成推送计划、记录执行结果，支持 webhook 和 email 等渠道扩展。
- **异步任务队列**：基于 RabbitMQ 的任务队列（采集 / Agent 处理 / 推送执行 / 简报生成），未连接时自动降级为同步内联执行。
- **基础设施**：内置 JWT 登录、RBAC 权限、菜单管理、系统配置、任务中心、日志中心和文件上传。

## 工作流

```text
新闻来源
  -> 采集记录
  -> 内容中心
  -> 内容处理
  -> Agent 运行（智能处理流水线）
  -> 热点池
  -> 推送计划
  -> 推送记录
```

### Agent 智能处理流水线

```
News Input
    ↓
[HotspotAgent]       → 是否热点? 热度评分? 优先级?
    ↓ (is_hot=true)
[ClassificationAgent] → 分类? 标签? 关键词?
    ↓
[SummaryAgent]       → 标题优化? 摘要? 亮点?
    ↓
[EnrichmentAgent]    → 背景? 影响? 技术分析?
    ↓
[PushPlannerAgent]   → 是否立即推送? 渠道? 计划时间?
    ↓
Output: 写入数据库（运行记录 / 热点 / 推送计划）
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 + Vite + TypeScript | Element Plus + Pinia + Vue Router |
| 后端框架 | NestJS ^10.3.0 | 模块化架构，装饰器风格 |
| ORM | Prisma ^5.22.0 | 类型安全的数据库访问 |
| 任务队列 | RabbitMQ (amqplib) | 5 个业务队列，自动降级 |
| Agent 框架 | @agentscope-ai/agentscope | AI-First Rule-Fallback 模式 |
| 数据库 | PostgreSQL | 通过 Prisma 管理 Schema |
| 认证 | JWT (@nestjs/jwt) + Passport | RBAC 权限控制 |
| API 文档 | Swagger (@nestjs/swagger) | 自动生成接口文档 |
| 默认模型 | qwen3.5-plus | 通过 DashScope 调用 |

## 本地启动

### 1. 启动后端 (NestJS)

```bash
cd backend-ts
npm install --include=dev
cp .env.example .env
# 编辑 .env 填写 DATABASE_URL、JWT_SECRET 等
npx prisma generate
npx prisma db push
npx tsx prisma/seeds/seed.ts
npm run start:dev
```

默认数据库连接建议使用：

```text
postgresql://postgres:123456@localhost:5432/easy_shorts
```

如果要启用真实模型能力，在 `backend-ts/.env` 中补充：

```text
DASHSCOPE_API_KEY=你的 DashScope Key
```

如果要启用异步任务队列，还需要启动 RabbitMQ 并在 `.env` 中配置 `RABBITMQ_URI`。不配则自动降级为同步执行。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 启动后可选：RabbitMQ（Docker）

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```

启动后可访问：

- 前端：`http://localhost:5173/`
- 后端接口文档：`http://127.0.0.1:8000/easy-shorts/docs`（Swagger）
- 健康检查：`http://127.0.0.1:8000/easy-shorts/health`
- RabbitMQ 管理界面：`http://localhost:15672`（guest/guest）

## 默认账号

- 超级管理员：`admin / admin123`
- 操作员：`operator / operator123`

## 仓库结构

```text
EasyShortsAI/
├── backend-ts/      NestJS + Prisma 后端（主力版本，TypeScript 重写）
│   ├── src/         源代码（模块化架构）
│   ├── prisma/      数据库 Schema + 种子数据
│   └── doc/         后端开发规范文档
├── backend/         FastAPI 后端（历史版本，Python）
├── frontend/        Vue 3 管理后台
├── doc/             需求、架构、接口、开发计划与截图
├── src/             （遗留目录）
├── prisma/          （遗留目录）
└── deploy/          部署配置
```

### 后端核心模块 (backend-ts/src/)

```
src/
├── common/          公共模块（枚举/接口/异常/装饰器/守卫/拦截器/过滤器）
├── config/          环境变量映射
├── prisma/          PrismaClient 封装
├── auth/            JWT 认证（登录/登出/当前用户）
├── user/            用户管理 CRUD
├── role/            角色管理 CRUD + 菜单分配
├── menu/            菜单树 CRUD
├── system/          系统配置/平台账号/日志/任务
├── news/            新闻源/新闻列表/采集记录
├── agent/           Agent 模块对外 API（配置/模型/运行/热点/推送计划）
├── agents/          Agent 核心实现（6 个 Agent + 编排器）
├── rabbitmq/        任务队列（连接管理/生产者/5 个消费者处理器）
├── storage/         文件存储（本地存储/Multer 上传）
└── health/          健康检查
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
- [后端 TS 开发规范](./backend-ts/doc/backend-ts-dev-spec.md)
- [后端 TS 详细文档](./backend-ts/README.md)

## 当前进度

目前这套仓库已经完成了以下落地部分：

- ✅ 后端基础设施与 RBAC（NestJS + Prisma 重构完成）
- ✅ 新闻来源、采集记录、内容中心
- ✅ 内容处理链路
- ✅ Agent 智能处理流水线（6 个 Agent + 编排器，AI-First Rule-Fallback）
- ✅ RabbitMQ 异步任务队列（5 个业务队列，自动降级）
- ✅ 热点池、推送计划与推送记录
- ✅ 前端管理后台主要页面
- ✅ 文档、接口、测试与默认数据初始化
- ✅ 后端从 Python (FastAPI) 迁移至 TypeScript (NestJS)

后续如果继续往前推进，最自然的方向会是：

1. 完善更多来源站点的采集适配器
2. 接入更稳定的登录态 / 反爬方案
3. 增强热点聚类和推送策略
4. 补齐推送渠道的真实配置与运维能力
5. 增加 AI 简报生成功能的完善与定时调度
