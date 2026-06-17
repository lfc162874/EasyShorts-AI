# EasyShorts AI Backend (TypeScript)

> 基于 **NestJS + Prisma + RabbitMQ + AgentScope** 的 AI 热点追踪后端服务

这是 EasyShorts AI 项目的 TypeScript 后端重写版本，完全替代原 Python FastAPI 后端，**前端零改动即可对接**。

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | NestJS | ^10.3.0 |
| ORM | Prisma | ^5.22.0 |
| 任务队列 | RabbitMQ (amqplib) | ^0.10.0 |
| Agent 框架 | @agentscope-ai/agentscope | ^0.0.10 |
| 认证 | JWT (@nestjs/jwt) + Passport | - |
| 校验 | class-validator + class-transformer | - |
| 调度 | @nestjs/schedule | ^4.0.0 |
| Node.js | - | v18.0.0 |

## 项目结构

```
backend-ts/
├── src/
│   ├── app.module.ts              # 根模块
│   ├── main.ts                    # 入口文件（中间件/管道/守卫注册）
│   │
│   ├── common/                    # 公共模块
│   │   ├── constants/enums.ts     # 20 个枚举定义
│   │   ├── interfaces/index.ts    # ApiResponse, PaginatedData 等
│   │   ├── exceptions/            # 自定义异常（40100/40300/40400...）
│   │   ├── decorators/            # @Public(), @Permissions(), @ReqUser()
│   │   ├── guards/                # JWT 认证 + RBAC 权限守卫
│   │   ├── interceptors/          # 统一响应格式 {code,message,data}
│   │   ├── filters/               # 全局异常过滤器
│   │   ├── utils/request-id.util.ts
│   │   └── dto/pagination.dto.ts
│   │
│   ├── config/configuration.ts    # 环境变量映射
│   │
│   ├── prisma/                    # Prisma ORM
│   │   ├── prisma.service.ts      # PrismaClient 封装
│   │   └── prisma.module.ts       # 全局模块导出
│   │
│   ├── auth/                      # 认证模块
│   │   ├── strategies/jwt.strategy.ts
│   │   ├── auth.service.ts        # login/logout/getCurrentUser
│   │   └── auth.controller.ts     # POST /auth/login, /auth/logout, GET /auth/me
│   │
│   ├── user/                      # 用户管理 CRUD
│   ├── role/                      # 角色管理 CRUD + 菜单分配
│   ├── menu/                      # 菜单树 CRUD
│   ├── system/                    # 系统配置/平台账号/日志/任务
│   ├── news/                      # 新闻源/新闻列表/采集记录
│   │
│   ├── agent/                     # Agent 模块（对外 API）
│   │   ├── agent.service.ts       # 配置/模型/运行记录/热点/推送计划
│   │   └── agent.controller.ts    # RESTful 接口
│   │
│   ├── agents/                    # Agent 核心实现（AI-first rule-fallback）
│   │   ├── agents.types.ts        # 结构化输出类型定义
│   │   ├── agents.common.ts       # 规则降级工具函数
│   │   ├── agents.runtime.ts      # AgentScope 运行时封装
│   │   ├── hotspot.agent.ts       # 热点判断 Agent
│   │   ├── classification.agent.ts# 分类 Agent
│   │   ├── summary.agent.ts       # 摘要生成 Agent
│   │   ├── enrichment.agent.ts    # 内容增强 Agent
│   │   ├── push-planner.agent.ts  # 推送计划 Agent
│   │   ├── digest.agent.ts        # 简报生成 Agent
│   │   └── agents.orchestrator.ts # 智能处理编排器
│   │
│   ├── rabbitmq/                  # 任务队列模块
│   │   ├── rabbitmq.interfaces.ts # 队列定义/消息类型
│   │   ├── rabbitmq.connection.ts # 连接管理（自动重连）
│   │   ├── rabbitmq.service.ts    # 生产者（自动降级内联执行）
│   │   ├── rabbitmq.processors.ts # 5 个消费者处理器
│   │   └── rabbitmq.module.ts
│   │
│   ├── storage/                   # 文件存储模块
│   │   ├── storage.interfaces.ts  # IStorageService 接口
│   │   ├── local-storage.service.ts
│   │   ├── file-upload.service.ts # Multer 上传封装
│   │   └── storage.module.ts
│   │
│   └── health/                    # 健康检查
│
├── prisma/
│   ├── schema.prisma              # 完整数据库 Schema（20+ 模型）
│   └── seeds/
│       └── seed.ts                # 种子数据脚本
│
├── src/agents/prompts/            # Agent Prompt 模板（从 Python 端迁移）
├── doc/backend-ts-dev-spec.md    # 开发规范文档
├── .env.example                  # 环境变量模板
└── .npmrc                        # npm 镜像源配置
```

## 快速开始

### 前置条件

- Node.js **v18.0.0+**
- PostgreSQL（或 MySQL，按 `.env` 配置）
- RabbitMQ（可选，不配则降级为内联执行）

### 安装依赖

```bash
cd backend-ts
npm install --include=dev
```

### 环境配置

```bash
cp .env.example .env
# 编辑 .env 填写以下关键配置：
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | - |
| `RABBITMQ_URI` | RabbitMQ 连接（可选） | - |
| `JWT_SECRET` | JWT 签名密钥 | - |
| `DASHSCOPE_API_KEY` | 阿里 DashScope API Key（Agent AI 功能） | - |

### 初始化数据库

```bash
# 生成 Prisma Client
npx prisma generate

# 推送 Schema 到数据库
npx prisma db push

# 导入种子数据（admin/admin123, operator/operator123）
npx tsx prisma/seeds/seed.ts
```

### 启动开发服务器

```bash
# 开发模式（热重载）
npm run start:dev

# 或普通启动
npm run start
```

服务默认运行在 `http://localhost:8000/easy-shorts`

## API 接口

所有接口前缀: `/easy-shorts`

### 认证

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/auth/login` | 公开 | 用户登录 |
| POST | `/auth/logout` | 登录 | 退出登录 |
| GET | `/auth/me` | 登录 | 当前用户信息 |

### 系统管理

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/system/users` | system:user:list | 用户列表 |
| POST | `/system/users` | system:user:create | 创建用户 |
| PUT | `/system/users/:id` | system:user:update | 更新用户 |
| GET | `/system/routes` | system:role:list | 角色列表 |
| GET | `/system/menus` | system:menu:list | 菜单列表 |
| GET | `/system/configs` | system:config:list | 系统配置 |
| GET | `/system/logs` | system:log:list | 操作日志 |

### 新闻管理

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/news/sources` | news:source:list | 新闻源列表 |
| POST | `/news/sources` | news:source:create | 创建新闻源 |
| PUT | `/news/sources/:id` | news:source:update | 更新新闻源 |
| POST | `/news/sources/:id/sync` | news:source:update | 同步新闻源 |
| GET | `/news` | news:list | 新闻列表 |
| GET | `/news/records` | news:fetch-record:list | 采集记录 |

### Agent 管理（核心功能）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/agent/config` | agent:config:list | Agent 配置 |
| PUT | `/agent/config` | agent:config:update | 更新配置 |
| GET | `/agent/models` | agent:model:list | 可用模型列表 |
| POST | `/agent/runs/news/:newsId` | agent:run:create | 触发 Agent 处理 |
| POST | `/agent/intelligent-processing/news/:newsId` | agent:run:create | 完整智能处理流水线 |
| POST | `/agent/generate-digest` | agent:digest:create | 生成 AI 简报 |
| GET | `/agent/runs` | agent:run:list | 运行记录 |
| GET | `/agent/runs/:id` | agent:run:list | 运行详情 |
| POST | `/agent/runs/:id/retry` | agent:run:create | 重试运行 |
| GET | `/agent/hot-topics` | agent:hot-topic:list | 热点列表 |
| GET | `/agent/push-plans` | agent:push-plan:list | 推送计划列表 |
| POST | `/agent/push-plans/:id/execute` | agent:push-plan:update | 执行推送 |

### 其他

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/health` | 公开 | 健康检查 |

## Agent 架构

### AI-First Rule-Fallback 模式

每个 Agent 都遵循统一的设计原则：

1. **优先调用 LLM**：通过 AgentScope DashScopeChatModel 获取结构化 JSON 输出
2. **规则降级保证**：LLM 不可用时，使用确定性规则逻辑返回合理结果
3. **永不崩溃**：任何异常都被捕获并降级，不会导致请求失败

### 智能处理流水线

```
News Input
    ↓
[HotspotAgent] → is_hot? score? priority?
    ↓ (is_hot=true)
[ClassificationAgent] → category? tags? keywords?
    ↓
[SummaryAgent] → title? summary? highlights?
    ↓
[EnrichmentAgent] → background? impact? technical_analysis?
    ↓
[PushPlannerAgent] → push_now? channels? planned_at?
    ↓
Output: OrchestratorResult (写入 DB)
```

### RabbitMQ 队列设计

| 队列名 | 用途 | 处理器 |
|--------|------|--------|
| `news.fetch` | RSS 新闻采集 | NewsFetchHandler |
| `agent.processing` | Agent 智能处理 | AgentProcessingHandler |
| `push.execute` | 推送执行 | PushExecuteHandler |
| `digest.generate` | 简报生成 | DigestGenerateHandler |
| `demo.task` | 测试任务 | DemoTaskHandler |

RabbitMQ 未连接时，所有发布操作自动降级为同步内联执行。

## 统一响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": { ... },
  "request_id": "req_abc123"
}
```

### 错误码

| 错误码 | 含义 |
|--------|------|
| 40100 | 未认证 / Token 无效 |
| 40300 | 无权限 |
| 40400 | 资源不存在 |
| 40900 | 资源冲突 |
| 42200 | 参数校验失败 |

## 开发命令

```bash
# 开发模式（watch + 自动重启）
npm run start:dev

# 调试模式
npm run start:debug

# 构建
npm run build

# 生产启动
npm run start:prod

# Prisma 相关
npm run prisma:generate    # 生成 Client
npm run prisma:migrate      # 运行迁移
npm run prisma:studio       # 打开 GUI
npm run prisma:push         # 推送 Schema

# 种子数据
npx tsx prisma/seeds/seed.ts
```

## 与前端对接

**前端零改动**。确认以下配置一致：

1. **代理**: Vite 已配置 `/easy-shorts` → `http://127.0.0.1:8000`
2. **认证**: Bearer Token，存储在 `localStorage.easyshorts-access-token`
3. **响应**: `{code:0, message:"ok", data, request_id}` 格式完全兼容
4. **登录**: 返回 `{access_token, token_type:"bearer", expires_in, user}`

默认账号：
- 超级管理员: `admin` / `admin123`
- 操作员: `operator` / `operator123`

## License

MIT
