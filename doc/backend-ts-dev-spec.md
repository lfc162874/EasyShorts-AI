# EasyShorts AI 后端 TypeScript 重构 — 开发规范

> **版本**: v1.0  
> **日期**: 2026-06-16  
> **技术栈**: NestJS + Prisma + RabbitMQ + AgentScope-TypeScript  
> **目标**: 将现有 Python FastAPI 后端完整迁移为 TypeScript，**前端零改动兼容**

---

## 目录

1. [项目结构规范](#1-项目结构规范)
2. [命名约定](#2-命名约定)
3. [代码风格](#3-代码风格)
4. [API 响应格式规范（核心）](#4-api-响应格式规范核心)
5. [错误处理规范](#5-错误处理规范)
6. [认证与授权规范](#6-认证与授权规范)
7. [DTO / 校验规范](#7-dto--校验规范)
8. [Service 层规范](#8-service-层规范)
9. [Prisma 数据库规范](#9-prisma-数据库规范)
10. [Agent 模块规范](#10-agent-模块规范)
11. [任务队列规范（RabbitMQ）](#11-任务队列规范rabbitmq)
12. [日志规范](#12-日志规范)
13. [配置管理规范](#13-配置管理规范)
14. [文件上传与存储规范](#14-文件上传与存储规范)
15. [前端兼容性清单](#15-前端兼容性清单)

---

## 1. 项目结构规范

### 1.1 目录布局

```
backend-ts/src/
├── main.ts                    # 应用入口，bootstrap()
├── app.module.ts              # 根模块，聚合所有功能模块
│
├── common/                    # 全局公共模块（无 @Module 装饰器，纯导出）
│   ├── decorators/            # 自定义装饰器
│   ├── filters/               # 异常过滤器
│   ├── guards/                # 守卫
│   ├── interceptors/          # 拦截器
│   ├── interfaces/            # TypeScript 接口/类型定义
│   └── utils/                 # 纯函数工具集
│
├── config/                    # 配置模块
│   └── configuration.ts       # registerAs() 配置 schema
│
├── prisma/                    # Prisma Client 封装
│   ├── prisma.module.ts        # PrismaModule（全局）
│   └── prisma.service.ts       # PrismaService（封装 @prisma/client）
│
├── auth/                      # 认证模块
│   ├── auth.module.ts
│   ├── auth.controller.ts
│   ├── auth.service.ts
│   └── strategies/
│       └── jwt.strategy.ts
│
├── user/                      # 用户模块
│   ├── user.module.ts
│   ├── user.controller.ts
│   ├── user.service.ts
│   └── dto/
│       ├── create-user.dto.ts
│       └── update-user.dto.ts
│
├── role/                      # 角色模块
│   ├── role.module.ts
│   ├── role.controller.ts
│   ├── role.service.ts
│   └── dto/
│
├── menu/                      # 菜单模块
│   ├── menu.module.ts
│   ├── menu.controller.ts
│   ├── menu.service.ts
│   └── dto/
│
├── system/                    # 系统管理模块
│   ├── system.module.ts
│   ├── system.controller.ts
│   ├── system.service.ts
│   └── dto/
│
├── news/                      # 新闻业务模块
│   ├── news.module.ts
│   ├── news.controller.ts
│   ├── news.service.ts
│   ├── collector.service.ts    # 采集服务
│   ├── content-pipeline.service.ts  # 内容处理管道
│   └── dto/
│
├── agent/                     # Agent 管理 API 模块
│   ├── agent.module.ts
│   ├── agent.controller.ts
│   ├── agent.service.ts        # 运行管理 CRUD
│   ├── agent-config.service.ts  # 配置读写
│   └── dto/
│
├── agents/                    # AgentScope Agent 实现（纯逻辑，无 HTTP）
│   ├── runtime.ts             # 运行时构建器
│   ├── context.ts             # 执行上下文
│   ├── common.ts              # 规则兜底工具函数
│   ├── structured-models.ts   # 结构化输出类型
│   ├── hotspot.agent.ts
│   ├── classification.agent.ts
│   ├── summary.agent.ts
│   ├── enrichment.agent.ts
│   ├── push-planner.agent.ts
│   ├── digest.agent.ts
│   ├── workflows/
│   │   └── intelligent-processing.workflow.ts
│   └── prompts/               # prompt 模板文件（从 backend 复制）
│
├── tasks/                     # RabbitMQ 任务处理器
│   ├── tasks.module.ts
│   ├── queues.ts              # 队列/交换机定义常量
│   ├── news.processor.ts
│   ├── agent.processor.ts
│   └── demo.processor.ts
│
└── integrations/
    └── storage/
        ├── storage.service.ts      # 抽象接口
        └── local-storage.service.ts # 本地存储实现
```

### 1.2 文件命名规则

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 模块文件 | `kebab-case.module.ts` | `user.module.ts` |
| 控制器 | `kebab-case.controller.ts` | `news.controller.ts` |
| 服务 | `kebab-case.service.ts` | `agent-config.service.ts` |
| DTO | `kebab-case.dto.ts` | `create-user.dto.ts` |
| Agent | `kebab-case.agent.ts` | `hotspot.agent.ts` |
| 工作流 | `kebab-case.workflow.ts` | `intelligent-processing.workflow.ts` |
| 处理器 | `kebab-case.processor.ts` | `news.processor.ts` |
| 类型/接口 | `kebab-case.interface.ts` 或 `kebab-case.types.ts` | `response.interface.ts` |
| 常量 | `kebab-case.constants.ts` | `agent.constants.ts` |
| 枚举 | `kebab-case.enum.ts` | `news-status.enum.ts` |

### 1.3 模块职责边界

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Controller  │────▶│   Service   │────▶│   Prisma    │
│  (HTTP 层)   │     │  (业务逻辑)  │     │  (数据访问)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
  DTO 校验 / 序列化    调用 Agent / 外部服务
  权限装饰器           复杂业务编排
```

- **Controller**: 只做三件事 —— 接收请求参数、调用 Service、返回响应。不含业务逻辑。
- **Service**: 所有业务逻辑、数据组装、外部调用。可注入其他 Service。
- **Agent (`src/agents/`)**: 纯函数/AI 调用逻辑，不依赖 HTTP 上下文。通过 `context` 对象传入参数。
- **Processor (`src/tasks/`)**: RabbitMQ 消息消费者，调用 Service 完成异步任务。

---

## 2. 命名约定

### 2.1 TypeScript 通用

```typescript
// ✅ 类：PascalCase
class UserService {}
class AgentRuntime {}
class NewsCollectorService {}

// ✅ 接口：PascalCase，不以 I 开头
interface ApiResponse<T> {}
interface AgentExecutionContext {}

// ✅ 类型别名：PascalCase
type PaginatedResult<T> = { items: T[]; total: number; page: number; page_size: number };

// ✅ 枚举：PascalCase，成员 UPPER_SNAKE_CASE
enum UserStatus {
  ACTIVE = 'ACTIVE',
  DISABLED = 'DISABLED',
}

// ✅ 变量/函数/方法：camelCase
const hotThreshold = 35;
function listNewsSources(params: ListQuery): Promise<PaginatedResult<NewsSource>> {}
async function syncNewsSource(db: PrismaClient, sourceId: number): Promise<SyncResult> {}

// ✅ 常量：UPPER_SNAKE_CASE（仅在模块顶层）
const HOT_KEYWORDS = ['openai', 'anthropic', 'deepseek', 'qwen'];
const DEFAULT_FETCH_INTERVAL = 360;

// ✅ 私有方法/属性：下划线前缀
private _buildSummary(entry: ParsedNewsEntry): string {}
private _scoreHotness(text: string): number {}

// ✅ 文件名：kebab-case
// news.service.ts, agent-config.service.ts, create-user.dto.ts
```

### 2.2 数据库字段映射（Prisma → TS 类）

Prisma 生成的模型字段使用 `camelCase`，与原 Python SQLAlchemy 的 `snake_case` 不同。
**所有对外 API 的 JSON 字段必须保持 snake_case**（与原后端一致），在序列化层做转换。

```typescript
// Prisma 模型（自动生成，camelCase）
// { id, createdAt, updatedAt, sourceId, lastFetchedAt, ... }

// API 响应（必须 snake_case，与原后端完全一致）
// { id, created_at, updated_at, source_id, last_fetched_at, ... }
```

---

## 3. 代码风格

### 3.1 严格模式

```jsonc
// tsconfig.json 关键配置
{
  "strict": true,
  "noImplicitAny": true,
  "strictNullChecks": true,
  "strictFunctionTypes": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noImplicitReturns": true,
  "esModuleInterop": true
}
```

### 3.2 导入顺序

```typescript
// 1. Node / 外部库
import { Injectable, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaClient } from '@prisma/client';

// 2. 内部公共模块 (@/)
import { AppException } from '@/common/exceptions';
import type { RequestUser } from '@/common/interfaces';

// 3. 同目录或子目录
import { CreateUserDto } from './dto/create-user.dto';
import { HashUtil } from '@/common/utils/hash.util';
```

### 3.3 注释风格

```typescript
/**
 * 同步指定新闻源的数据采集
 *
 * @param db - Prisma 数据库客户端
 * @param sourceId - 新闻源 ID
 * @param options - 可选参数（触发模式、任务 ID 等）
 * @returns 采集结果摘要（含新增/去重/过滤统计）
 * @throws {NotFoundException} 新闻源不存在
 * @throws {ValidationException} 不支持的来源类型
 */
async function syncNewsSource(
  db: PrismaClient,
  sourceId: number,
  options?: SyncOptions,
): Promise<SyncResult> {}
```

### 3.4 异步编程

- **统一使用 `async/await`**，禁止 `.then()` 链式调用
- Service 层方法全部为 `async`
- Controller 可以是 async（NestJS 支持）

```typescript
// ✅ 正确
@Get()
async findAll(@Query() query: ListNewsDto) {
  const [items, total] = await this.newsService.listNews(query);
  return { items, total };
}

// ❌ 错误
@Get()
findAll(@Query() query: ListNewsDto) {
  return this.newsService.listNews(query).then(([items, total]) => ({ items, total }));
}
```

---

## 4. API 响应格式规范（核心）

> **这是最重要的规范**。新后端的所有 API 响应必须与原 Python 后端完全一致，
> 否则前端无法正常工作。

### 4.1 统一响应结构

```typescript
// 成功响应
{
  "code": 0,
  "message": "ok",
  "data": { /* 具体数据 */ },
  "request_id": "abc123"
}

// 错误响应
{
  "code": 40400,
  "message": "资源不存在",
  "data": {},
  "request_id": "abc123"
}

// 分页列表响应的 data 结构
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [...],
    "page": 1,
    "page_size": 20,
    "total": 100
  },
  "request_id": "abc123"
}
```

### 4.2 ResponseInterceptor 实现

全局注册 `ResponseInterceptor`，自动包装所有 Controller 返回值：

```typescript
// src/common/interceptors/response.interceptor.ts
@Injectable()
export class ResponseInterceptor<T> implements NestInterceptor<T, ApiResponse<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<ApiResponse<T>> {
    return next.handle().pipe(
      map(data => ({
        code: 0,
        message: 'ok',
        data: data ?? {},
        requestId: RequestIdUtil.getId(),
      })),
    );
  }
}
```

### 4.3 Controller 返回值约定

```typescript
// ✅ 直接返回数据（拦截器自动包装）
@Get('sources')
async listSources() {
  return this.newsService.listSources(); // 返回 { items, page, page_size, total }
}

// ✅ 创建成功返回 201（通过 @HttpCode）
@Post('sources')
@HttpCode(201)
async createSource(@Body() dto: CreateNewsSourceDto) {
  return this.newsService.createSource(dto);
}

// ✅ 异步任务提交返回 202
@Post('runs/news/:newsId')
@HttpCode(202)
async runAgent(@Param('newsId') newsId: number) {
  return this.agentService.dispatchNewsRun(newsId);
}

// ❌ 禁止手动包装响应
@Get('sources')
async listSources() {
  const data = await this.newsService.listSources();
  return { code: 0, message: 'ok', data }; // 拦截器会重复包装！
}
```

### 4.4 字段命名：snake_case

**所有 API JSON 字段必须使用 snake_case**，与原后端和前端保持一致：

```typescript
// ✅ API 响应中的字段
{
  "id": 1,
  "source_key": "techcrunch-ai",
  "source_type": "RSS",
  "last_fetched_at": "2026-06-16T10:00:00Z",
  "created_at": "2026-06-01T00:00:00Z",
  "is_enabled": true
}

// ❌ 不要用 camelCase（除非前端也同步改）
{
  "sourceKey": "techcrunch-ai",   // 前端不认识
  "lastFetchedAt": "..."           // 前端不认识
}
```

**实现方式**：在 Service 层或专门的 Serializer 层将 Prisma 的 camelCase 转换为 snake_case。

---

## 5. 错误处理规范

### 5.1 业务异常体系

与原 Python 后端的异常体系一一对应：

```typescript
// src/common/exceptions/app.exception.ts
export class AppException extends Error {
  constructor(
    public readonly message: string,
    public readonly code: number,
    public readonly statusCode: number,
    public readonly data?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'AppException';
  }
}

export class UnauthorizedException extends AppException {
  constructor(message = '未认证或登录已失效') {
    super(message, 40100, 401);
  }
}

export class ForbiddenException extends AppException {
  constructor(message = '无权限访问当前资源') {
    super(message, 40300, 403);
  }
}

export class NotFoundException extends AppException {
  constructor(message = '资源不存在') {
    super(message, 40400, 404);
  }
}

export class ConflictException extends AppException {
  constructor(message = '资源状态冲突') {
    super(message, 40900, 409);
  }
}

export class ValidationException extends AppException {
  constructor(message = '业务校验失败', data?: Record<string, unknown>) {
    super(message, 42200, 422, data);
  }
}
```

### 5.2 错误码体系（与原后端完全对齐）

| 错误码 | HTTP 状态码 | 含义 |
|--------|-----------|------|
| 40100 | 401 | 未认证 / Token 无效 / 已过期 |
| 40300 | 403 | 无权限访问 |
| 40400 | 404 | 资源不存在 |
| 40900 | 409 | 资源冲突（重复创建等） |
| 42200 | 422 | 业务校验失败 |

### 5.3 异常过滤器

```typescript
// src/common/filters/app-exception.filter.ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    if (exception instanceof AppException) {
      return response.status(exception.statusCode).json({
        code: exception.code,
        message: exception.message,
        data: exception.data ?? {},
        request_id: RequestIdUtil.getId(),
      });
    }

    if (exception instanceof ValidationError) {
      // class-validator 校验失败
      return response.status(400).json({
        code: 40000,
        message: '请求参数校验失败',
        data: this.formatValidationErrors(exception),
        request_id: RequestIdUtil.getId(),
      });
    }

    // 未预期的异常
    return response.status(500).json({
      code: 50000,
      message: process.env.APP_ENV === 'production'
        ? '服务器内部错误'
        : (exception as Error).message,
      data: {},
      request_id: RequestIdUtil.getId(),
    });
  }
}
```

### 5.4 Service 层抛出异常的方式

```typescript
// ✅ Service 中直接 throw 业务异常
async getSource(id: number) {
  const source = await this.prisma.newsSource.findUnique({ where: { id } });
  if (!source) {
    throw new NotFoundException('新闻源不存在');
  }
  return source;
}

// ✅ Controller 不需要 try/catch 业务异常（由全局过滤器统一处理）
@Get('sources/:id')
async getSourceDetail(@Param('id') id: string) {
  return this.newsService.getSource(+id); // NotFoundException 自动被过滤器捕获
}
```

---

## 6. 认证与授权规范

### 6.1 JWT 认证流程

```
前端请求 → Authorization: Bearer <token>
         → JwtAuthGuard 提取 token
         → JwtStrategy 验证签名 + 过期时间
         → 查询 DB 确认用户存在且状态正常
         → 将 user 注入 request 对象
```

### 6.2 Token 规范

| 项目 | 值 |
|------|-----|
| 算法 | HS256 |
| 有效期 | 720 分钟（12 小时） |
| payload.sub | 用户 ID（数字字符串） |
| 存储键名 | `easyshorts-access-token`（localStorage，与前端一致） |

### 6.3 装饰器使用

```typescript
// 公开接口（无需登录）
@Public()
@Get('/health')
healthcheck() {}

// 需要登录（默认行为，可不加额外装饰器）
@UseGuards(JwtAuthGuard)
@Get('/agent/config')
getConfig(@ReqUser() user: RequestUser) {}

// 需要特定权限
@Permissions('agent:config:update')
@Put('/agent/config')
updateConfig(@Body() dto: UpdateConfigDto, @ReqUser() user: RequestUser) {}

// 超管自动绕过权限检查（PermissionsGuard 内部实现）
```

### 6.4 权限码规范（与原后端完全一致）

权限码格式：`模块:操作:动作`

```
system:user:list       system:user:create
system:role:list       system:role:create
system:menu:list       system:menu:create
system:config:list     system:config:create
system:platform-account:list  system:platform-account:create
system:log:list
system:task:list
system:file:upload

news:source:list       news:source:create  news:source:update
news:fetch-record:list
news:list              news:generate

agent:config:list      agent:config:update
agent:model:list
agent:run:create       agent:run:list       agent:run:retry  agent:run:step:retry
agent:hot-topic:list   agent:hot-topic:reprocess
agent:push-plan:list   agent:push-plan:execute
agent:digest:list      agent:digest:push     agent:digest:create
agent:push-record:list
```

---

## 7. DTO / 校验规范

### 7.1 DTO 定义方式

使用 `class-validator` + `class-transformer`，替代原 Pydantic：

```typescript
// src/news/dto/create-news-source.dto.ts
import { IsString, IsOptional, IsEnum, IsInt, Min, Max, IsBoolean } from 'class-validator';
import { Type } from 'class-transformer';

export class CreateNewsSourceDto {
  @IsString()
  source_key!: string;

  @IsString()
  name!: string;

  @IsEnum(NewsSourceType)
  source_type!: NewsSourceType;

  @IsString()
  url!: string;

  @IsOptional()
  @IsString()
  category?: string;

  @IsOptional()
  @IsString()
  language?: string;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(14400)
  fetch_interval_minutes?: number = 360;

  @IsOptional()
  @IsBoolean()
  is_enabled?: boolean = true;

  @IsOptional()
  extra?: Record<string, unknown>;
}
```

### 7.2 分页查询 DTO（基类）

```typescript
// src/common/dto/pagination.dto.ts
import { IsOptional, IsInt, Min, Type } from 'class-validator';

export class PaginationDto {
  @Type(() => Number)
  @IsOptional()
  @IsInt()
  @Min(1)
  page?: number = 1;

  @Type(() => Number)
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  page_size?: number = 20;

  @IsOptional()
  keyword?: string;
}
```

### 7.3 更新 DTO 使用 Partial

```typescript
// src/user/dto/update-user.dto.ts
import { PartialType, OmitType } from '@nestjs/swagger'; // 或手动实现
import { CreateUserDto } from './create-user.dto';

export class UpdateUserDto extends PartialType(CreateUserDto) {}
// 所有字段变为可选，用于 PATCH/PUT 更新
```

### 7.4 全局验证管道

```typescript
// main.ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,          // 剥离未声明的属性
    forbidNonWhitelisted: true, // 遇到未声明属性直接报错
    transform: true,          // 自动转型（query string number → number）
    transformOptions: {
      enableImplicitConversion: true,
    },
  }),
);
```

---

## 8. Service 层规范

### 8.1 依赖注入

```typescript
@Injectable()
export class NewsService {
  constructor(
    private readonly prisma: PrismaService,     // 数据库
    private readonly configService: ConfigService, // 配置
  ) {}

  // 可选注入其他 Service
  // constructor(
  //   private readonly prisma: PrismaService,
  //   private readonly auditService: AuditService,
  // ) {}
}
```

### 8.2 Service 方法签名规范

```typescript
/**
 * 列表查询 → 返回 [数组, 总数]
 */
async listSources(query: ListSourceQuery): Promise<[NewsSourceItem[], number]>

/**
 * 详情查询 → 返回单个对象
 */
async getSource(id: number): Promise<NewsSourceDetail>

/**
 * 创建 → 返回创建后的对象
 */
async createSource(dto: CreateNewsSourceDto): Promise<NewsSourceItem>

/**
 * 更新 → 返回更新后的对象
 */
async updateSource(id: number, dto: UpdateNewsSourceDto): Promise<NewsSourceItem>

/**
 * 删除 → 软删除，返回 void（本项目不使用物理删除）
 */
async removeSource(id: number): Promise<void>
```

### 8.3 事务处理

```typescript
// ✅ 使用 $transaction
async transferData(sourceId: number, targetId: number) {
  return this.prisma.$transaction(async (tx) => {
    const source = await tx.newsSource.findUnique({ where: { id: sourceId } });
    if (!source) throw new NotFoundException();

    await tx.news.update({
      where: { id: targetId },
      data: { /* ... */ },
    });

    await tx.newsSource.update({
      where: { id: sourceId },
      data: { /* ... */ },
    });

    return result;
  });
}
```

### 8.4 操作审计日志

写操作（创建/更新/删除/执行）必须记录审计日志：

```typescript
// 在 Controller 或 Service 中调用
async updateConfig(dto: UpdateConfigDto, operator: RequestUser, req: Request) {
  const config = await this.doUpdate(dto);

  // 记录操作日志
  await this.auditService.record({
    module: 'agent',
    action: 'update_config',
    operatorId: operator.id,
    operatorName: operator.username,
    request: req,
    bizType: 'agent_config',
    bizId: 'default',
    message: '更新 Agent 配置',
  });

  return config;
}
```

---

## 9. Prisma 数据库规范

### 9.1 Schema 组织

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// === RBAC ===
model User { ... }
model Role { ... }
model Menu { ... }

// === Business ===
model News { ... }
model NewsSource { ... }
model NewsFetchRecord { ... }
model Video { ... }
model PublishRecord { ... }

// === Agent ===
model AgentRun { ... }
model AgentRunStep { ... }
model HotTopic { ... }
// ...

// === System ===
model OperationLog { ... }
model TaskJob { ... }
// ...
```

### 9.2 字段类型映射（Python → Prisma）

| Python (SQLAlchemy) | Prisma | 备注 |
|---------------------|--------|------|
| `Integer` (PK, autoincrement) | `Int @id @default(autoincrement())` | 主键 |
| `String(N)` | `String @db.VarChar(N)` | 变长字符串 |
| `Text` | `Text?` | 长文本，可为空 |
| `DateTime` (timezone=True) | `DateTime @db.Timestamptz` | 带时区时间戳 |
| `Boolean` | `Boolean @default(false)` | 布尔值 |
| `JSON` | `Json?` | JSON 字段 |
| `Enum(StrEnum)` | `Enum(XXXStatus)` | 枚举 |
| `ForeignKey(Integer)` | `关联关系` | Prisma 用关系代替外键字段 |

### 9.3 统一字段约定

每个业务模型必须包含以下基础字段：

```prisma
model ExampleModel {
  id          Int       @id @default(autoincrement())
  createdAt  DateTime  @default(now()) @map("created_at")
  updatedAt  DateTime  @updatedAt @map("updated_at")

  @@map("table_name")
}
```

> **注意**: 使用 `@map()` 让 Prisma 表名和字段名保持 snake_case，与原有数据库表结构一致。

### 9.4 PrismaService 封装

```typescript
// src/prisma/prisma.service.ts
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
```

### 9.5 查询模式

```typescript
// ✅ 列表查询（带分页 + 过滤 + 排序）
async listNews(query: ListNewsQuery) {
  const where = this.buildWhereClause(query);
  const [items, total] = await Promise.all([
    this.prisma.news.findMany({
      where,
      orderBy: { publishTime: 'desc' },
      skip: (query.page - 1) * query.page_size,
      take: query.page_size,
    }),
    this.prisma.news.count({ where }),
  ]);
  return [items.map(this.serializeNews), total];
}

// ✅ 详情查询
async getNews(id: number) {
  const news = await this.prisma.news.findUnique({ where: { id } });
  if (!news) throw new NotFoundException('新闻不存在');
  return this.serializeNewsDetail(news);
}

// ✅ where 条件构建（私有方法）
private buildWhereClause(query: ListNewsQuery): Prisma.NewsWhereInput {
  const where: Prisma.NewsWhereInput = {};
  if (query.keyword) {
    where.OR = [
      { title: { contains: query.keyword } },
      { summary: { contains: query.keyword } },
      { category: { contains: query.keyword } },
    ];
  }
  if (query.status) where.status = query.status;
  if (query.source_id) where.sourceId = query.source_id;
  return where;
}
```

---

## 10. Agent 模块规范

### 10.1 核心设计原则

> **"AI 优先，规则兜底"** —— 每个 Agent 先尝试调用 AgentScope LLM，
> 如果 LLM 调用失败或不可用，降级到确定性规则逻辑。

### 10.2 Agent 函数签名

```typescript
// src/agents/hotspot.agent.ts
export interface AgentResult {
  [key: string]: unknown;
}

/**
 * 执行热点识别 Agent
 *
 * @param context - Agent 执行上下文（含新闻数据、运行时配置、prompt 等）
 * @returns 热点识别结果（is_hot, score, priority, trend, reason, keywords）
 */
export async function runHotspotAgent(
  context: AgentExecutionContext,
): Promise<AgentResult> {
  // 1. 尝试 AgentScope LLM 调用
  const llmResult = await callAgentScopeLLM(context, 'HotspotAgent', HotspotSchema);
  if (llmResult) {
    return { ...llmResult, model_name: context.modelName, promptVersion: context.promptVersion };
  }

  // 2. 降级到规则引擎
  return fallbackRuleBasedHotspot(context);
}
```

### 10.3 AgentContext 定义

```typescript
// src/agents/context.ts
export interface AgentExecutionContext {
  /** 当前处理的新闻对象 */
  news: News; // Prisma News 类型

  /** 模型名称 */
  modelName: string;

  /** Prompt 版本 */
  promptVersion: string;

  /** Prompt 模板包（从 DB 或文件加载） */
  promptBundle: Record<string, string>;

  /** 系统配置（阈值等） */
  config: AgentSystemConfig;

  /** Agent 运行时（含 Provider 信息） */
  runtime: AgentRuntime | null;

  /** 是否强制重新执行（忽略缓存） */
  force: boolean;
}
```

### 10.4 Workflow 编排

```typescript
// src/agents/workflows/intelligent-processing.workflow.ts
export async function runSingleArticleWorkflow(
  context: AgentExecutionContext,
): Promise<WorkflowResult> {
  // Step 1: 热点识别
  const hotspot = await runHotspotAgent(context);
  const result: WorkflowResult = { hotspot };

  if (!hotspot.is_hot) {
    return result; // 非热点，提前退出
  }

  // Step 2-5: 串行执行后续 Agent
  const [classification, summary, enrichment, pushPlan] = await Promise.all([
    // 注意：实际有依赖关系，需要串行
    runClassificationAgent(context, hotspot),
    // summary 依赖 classification
    // enrichment 依赖 classification + summary
    // push_plan 依赖 hotspot + classification + summary
  ]);

  // 正确的串行编排：
  const classification = await runClassificationAgent(context, hotspot);
  const summary = await runSummaryAgent(context, hotspot, classification);
  const enrichment = await runEnrichmentAgent(context, classification, summary);
  const pushPlan = await runPushPlannerAgent(context, hotspot, classification, summary);

  return { hotspot, classification, summary, enrichment, pushPlan };
}
```

### 10.5 AgentScope TypeScript 集成规范

```typescript
// src/agents/runtime.ts
import { Agent, Model } from '@agentscope-ai/agentscope';

export interface AgentRuntime {
  modelName: string;
  provider: 'dashscope' | 'openai' | 'rule_based';
  defaultProvider: string;
  supportedModels: string[];
  pushChannels: string[];
  hotThreshold: number;
  promptBundle: Record<string, string>;
}

export function buildAgentRuntime(
  configFromDb: AgentConfigFromDb,
): AgentRuntime {
  // 从 SystemConfig 表读取配置，构建 Runtime 对象
  // 与原 Python build_agent_runtime() 逻辑一致
}

// AgentScope Model 工厂
function createLLMModel(runtime: AgentRuntime): Model {
  switch (runtime.provider) {
    case 'dashscope':
      return new Model({
        config_name: runtime.modelName,
        model_type: 'dashscope_chat',
        // ... dashscope 配置
      });
    case 'openai':
      return new Model({
        config_name: runtime.modelName,
        model_type: 'openai_chat',
        // ... openai 配置
      });
    default:
      throw new Error(`Unsupported provider: ${runtime.provider}`);
  }
}
```

---

## 11. 任务队列规范（RabbitMQ）

### 11.1 队列规划

| 队列名 | 用途 | 对应原 Celery Queue |
|--------|------|---------------------|
| `easy_shorts_system_queue` | 系统任务（Demo 健康检查） | `system_queue` |
| `easy_shorts_content_queue` | 内容任务（Agent 执行、内容生成/处理） | `content_queue` |
| `easy_shorts_news_queue` | 新闻采集任务 | `news_queue` |

### 11.2 消息格式

```typescript
// 所有 RabbitMQ 消息遵循统一信封格式
interface TaskMessageEnvelope<T = unknown> {
  /** 任务唯一标识（对应 TaskJob.id） */
  task_job_id: number;

  /** 任务类型标识 */
  task_type: string;

  /** 触发者用户 ID */
  triggered_by?: number;

  /** 关联的请求 ID（链路追踪） */
  request_id?: string;

  /** 任务负载（具体参数） */
  payload: T;
}
```

### 11.3 Processor 模板

```typescript
// src/tasks/agent.processor.ts
@Controller()
export class AgentProcessor {
  private readonly logger = new Logger(AgentProcessor.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly agentRunService: AgentRunService,
  ) {}

  /**
   * 消费 content_queue 中的 Agent 新闻处理任务
   */
  @RabbitSubscribe({
    exchange: 'easy_shorts_direct',
    routingKey: 'content_queue',
    queue: 'easy_shorts_content_queue',
  })
  async handleAgentNewsTask(msg: Message) {
    const envelope: TaskMessageEnvelope = JSON.parse(msg.content.toString());

    this.logger.log(`[Task-${envelope.task_job_id}] 开始执行 Agent 新闻处理`);

    try {
      // 1. 更新 TaskJob 状态为 RUNNING
      await this.updateTaskJob(envelope.task_job_id, 'RUNNING');

      // 2. 执行实际业务
      const result = await this.agentRunService.executeAgentRun(
        envelope.payload.agent_run_id,
      );

      // 3. 更新 TaskJob 状态为 SUCCESS
      await this.updateTaskJob(envelope.task_job_id, 'SUCCESS', { result });

      // 4. ACK 消息
      channel.ack(msg);
    } catch (error) {
      this.logger.error(`[Task-${envelope.task_job_id}] 执行失败: ${error}`);

      // 更新 TaskJob 状态为 FAILED
      await this.updateTaskJob(envelope.task_job_id, 'FAILED', {
        error_message: error.message,
      });

      // 根据重试次数决定 NACK 或 ACK（死信队列）
      channel.nack(msg, false, false); // requeue=false → 死信队列
    }
  }
}
```

### 11.4 定时任务（替代 Celery Beat）

使用 `@nestjs/schedule` 的 Cron 任务：

```typescript
// 每 10 分钟同步到期新闻源（替代原 celery beat）
@Cron('*/10 * * * *')
async syncDueNewsSources() {
  const dueSources = await this.newsService.listDueSources();
  for (const source of dueSources) {
    await this.rabbitmq.publish('news_queue', {
      task_type: 'news_source_sync',
      payload: { news_source_id: source.id, fetch_mode: 'SCHEDULED' },
    });
  }
}
```

### 11.5 降级策略

当 RabbitMQ 不可用时，支持内联同步执行（与原 Celery 降级策略一致）：

```typescript
async dispatchWithFallback<T>(
  queueName: string,
  envelope: TaskMessageEnvelope,
  inlineFn: () => Promise<T>,
): Promise<TaskJob> {
  const taskJob = await this.createTaskJob(envelope);

  try {
    // 尝试发送到 RabbitMQ
    await this.rabbitmq.publish(queueName, envelope);
    return taskJob;
  } catch (error) {
    this.logger.warn(`RabbitMQ 不可用，降级为内联执行: ${error.message}`);

    // 降级：同步执行
    await this.updateTaskJob(taskJob.id, 'RUNNING');
    const result = await inlineFn();
    return this.updateTaskJob(taskJob.id, 'SUCCESS', { result });
  }
}
```

---

## 12. 日志规范

### 12.1 日志框架

使用 NestJS 内置 `Logger`（基于 console，生产环境可替换为 Winston/Pino）。

### 12.2 日志格式

```
[2026-06-16T10:30:00.000Z] INFO  [AgentProcessor] [req-abc123] [Task-42] 开始执行 Agent 新闻处理
[2026-06-16T10:30:05.200Z] ERROR [NewsService] [req-abc123] 采集源 5 失败: ETIMEDOUT
```

### 12.3 日志级别使用

| 级别 | 使用场景 |
|------|---------|
| `log` | 一般信息（任务开始/完成、关键节点） |
| `warn` | 可恢复的异常情况（降级执行、重试） |
| `error` | 需要关注的错误（LLM 调用失败、DB 写入失败） |
| `debug` | 详细调试信息（仅开发环境开启） |
| `verbose` | 更详细的追踪（默认关闭） |

### 12.4 RequestId 链路追踪

每次 HTTP 请求生成唯一 `request_id`，贯穿该请求的所有日志和异步任务：

```typescript
// 中间件：为每个请求生成 request_id
app.use((req, res, next) => {
  req.headers['x-request-id'] = req.headers['x-request-id'] || randomUUID();
  next();
});
```

---

## 13. 配置管理规范

### 13.1 环境变量（.env）

与原 Python 后端 `.env.example` 保持一致的变量名：

```env
# ===== 应用 =====
APP_NAME=EasyShortsAI
APP_ENV=development
DEBUG=true
API_PREFIX=/easy-shorts

# ===== 安全 =====
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=720

# ===== 数据库 =====
DATABASE_URL=postgresql://user:pass@localhost:5432/easy_shorts

# ===== Redis / RabbitMQ =====
REDIS_URL=redis://localhost:6379
RABBITMQ_URI=amqp://guest:guest@localhost:5672

# ===== AI / AgentScope =====
DASHSCOPE_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=
AGENT_DEFAULT_MODEL_NAME=qwen3.5-plus
AGENT_DEFAULT_PROVIDER=dashscope
AGENT_PROMPT_VERSION=v1

# ===== 存储 =====
STORAGE_BACKEND=local
LOCAL_STORAGE_ROOT=./data/uploads
MAX_UPLOAD_SIZE_MB=10

# ===== 启动 =====
AUTO_CREATE_TABLES=true
BOOTSTRAP_ADMIN_ON_STARTUP=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# ===== CORS =====
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 13.2 配置加载

```typescript
// src/config/configuration.ts
export default () => ({
  app: {
    name: process.env.APP_NAME,
    env: process.env.APP_ENV,
    debug: process.env.DEBUG === 'true',
    apiPrefix: process.env.API_PREFIX || '/easy-shorts',
  },
  database: {
    url: process.env.DATABASE_URL,
  },
  rabbitmq: {
    uri: process.env.RABBITMQ_URI,
  },
  redis: {
    url: process.env.REDIS_URL,
  },
  jwt: {
    secret: process.env.SECRET_KEY,
    expiresIn: process.env.ACCESS_TOKEN_EXPIRE_MINUTES
      ? `${process.env.ACCESS_TOKEN_EXPIRE_MINUTES}s`
      : '720m',
  },
  agent: {
    defaultModelName: process.env.AGENT_DEFAULT_MODEL_NAME || 'qwen3.5-plus',
    defaultProvider: process.env.AGENT_DEFAULT_PROVIDER || 'dashscope',
    promptVersion: process.env.AGENT_PROMPT_VERSION || 'v1',
  },
  storage: {
    backend: process.env.STORAGE_BACKEND || 'local',
    localRoot: process.env.LOCAL_STORAGE_ROOT || './data/uploads',
    maxUploadSizeMb: parseInt(process.env.MAX_UPLOAD_SIZE_MB || '10', 10),
  },
});
```

---

## 14. 文件上传与存储规范

### 14.1 上传限制

| 参数 | 值 |
|------|-----|
| 最大文件大小 | 由 `MAX_UPLOAD_SIZE_MB` 控制（默认 10MB） |
| 允许类型 | 图片 / 音频 / 视频 / 文档 / 其他 |
| 存储后端 | 默认 local（可扩展 S3/OSS） |

### 14.2 存储服务接口

```typescript
// src/integrations/storage/storage.service.ts
export interface StorageClient {
  /** 保存文件，返回访问 URL */
  save(buffer: Buffer, filename: string, category: FileCategory): Promise<StoredObject>;

  /** 删除文件 */
  delete(storagePath: string): Promise<void>;

  /** 获取文件的公开访问 URL */
  getUrl(storagePath: string): string;
}

export interface StoredObject {
  storagePath: string;
  url: string;
  size: number;
  contentType: string;
}
```

---

## 15. 前端兼容性清单

> **每完成一个模块的开发，必须逐项核对以下兼容性要求。**

### 15.1 API 路径对照表

| 前端调用路径 | 新后端路由 | 方法 | 认证 | 权限码 |
|-------------|----------|------|------|--------|
| `/auth/login` | `auth/login` | POST | 否 | - |
| `/auth/logout` | `auth/logout` | POST | 是 | - |
| `/auth/me` | `auth/me` | GET | 是 | - |
| `/health` | `health` | GET | 否 | - |
| `/agent/config` | `agent/config` | GET/PUT | 是 | agent:config:list/update |
| `/agent/models` | `agent/models` | GET | 是 | agent:model:list |
| `/agent/runs` | `agent/runs` | GET/POST | 是 | agent:run:* |
| `/agent/runs/:id` | `agent/runs/:id` | GET/POST | 是 | agent:run:* |
| `/agent/runs/:id/steps/:sid/retry` | `agent/runs/:id/steps/:sid/retry` | POST | 是 | agent:run:step:retry |
| `/agent/hot-topics` | `agent/hot-topics` | GET/POST | 是 | agent:hot-topic:* |
| `/agent/push-plans` | `agent/push-plans` | GET/POST | 是 | agent:push-plan:* |
| `/agent/digests` | `agent/digests` | GET/POST | 是 | agent:digest:* |
| `/agent/push-records` | `agent/push-records` | GET | 是 | agent:push-record:list |
| `/news/sources` | `news/sources` | GET/POST/PUT | 是 | news:source:* |
| `/news/sources/:id/sync` | `news/sources/:id/sync` | POST | 是 | news:source:update |
| `/news` | `news` | GET/POST | 是 | news:list/generate |
| `/news/:id` | `news/:id` | GET/POST | 是 | news:list/process |
| `/news/records` | `news/records` | GET | 是 | news:fetch-record:list |
| `/system/users` | `system/users` | GET/POST/PUT | 是 | system:user:list |
| `/system/roles` | `system/roles` | GET/POST/PUT | 是 | system:role:list |
| `/system/roles/:id/menus` | `system/roles/:id/menus` | PUT | 是 | system:role:list |
| `/system/menus` | `system/menus` | GET/POST/PUT | 是 | system:menu:list |
| `/system/configs` | `system/configs` | GET/POST/PUT | 是 | system:config:list |
| `/system/platform-accounts` | `system/platform-accounts` | GET/POST/PUT | 是 | system:platform-account:* |
| `/system/logs/operations` | `system/logs/operations` | GET | 是 | system:log:list |
| `/system/logs/errors` | `system/logs/errors` | GET | 是 | system:log:list |
| `/system/tasks` | `system/tasks` | GET/POST | 是 | system:task:list |
| `/uploads/files` | `uploads/files` | POST | 是 | system:file:upload |

### 15.2 响应格式核对项

- [ ] 所有响应包含 `{ code, message, data, request_id }` 四个顶层字段
- [ ] 成功时 `code === 0`
- [ ] 分页列表 `data` 包含 `{ items, page, page_size, total }`
- [ ] 所有 JSON 字段名为 **snake_case**
- [ ] 时间格式 ISO 8601 UTC（如 `2026-06-16T10:00:00.000Z`）
- [ ] 枚举值为 **UPPER_SNAKE_CASE**（如 `"ACTIVE"`, `"PENDING"`）
- [ ] `null` 值保留为 JSON `null`（不转空字符串）
- [ ] 布尔值为 JSON `true/false`（非 `"true"/"false"`）

### 15.3 认证兼容

- [ ] 登录接口返回 `{ access_token, user }` 格式
- [ ] Token 通过 `Authorization: Bearer <token>` 传递
- [ ] Token 过期返回 `code: 40100`
- [ ] 权限不足返回 `code: 40300`
- [ ] 前端 localStorage key 为 `easyshorts-access-token`（不变）

### 15.4 错误码兼容

| 场景 | code | status_code | message 示例 |
|------|------|------------|-------------|
| Token 无效/过期 | 40100 | 401 | 未认证或登录已失效 |
| 无权限 | 40300 | 403 | 无权限访问当前资源 |
| 资源不存在 | 40400 | 404 | 资源不存在 / xxx 不存在 |
| 资源冲突 | 40900 | 409 | xxx 已存在 / xxx 状态冲突 |
| 校验失败 | 42200 | 422 | 业务校验失败 |
| 未知错误 | 50000 | 500 | 服务器内部错误 |

---

## 附录 A：枚举值速查表

以下枚举值必须与原后端 `constants.py` 完全一致：

```typescript
// UserStatus
export enum UserStatus { ACTIVE = 'ACTIVE', DISABLED = 'DISABLED' }

// MenuType
export enum MenuType { DIRECTORY = 'DIRECTORY', MENU = 'MENU', BUTTON = 'BUTTON' }

// TaskStatus
export enum TaskStatus {
  PENDING = 'PENDING', RUNNING = 'RUNNING', SUCCESS = 'SUCCESS',
  FAILED = 'FAILED', RETRYING = 'RETRYING', CANCELLED = 'CANCELLED',
}

// NewsSourceType
export enum NewsSourceType { RSS = 'RSS', ATOM = 'ATOM', WEB = 'WEB', MANUAL = 'MANUAL' }

// NewsFetchMode
export enum NewsFetchMode { MANUAL = 'MANUAL', SCHEDULED = 'SCHEDULED' }

// NewsStatus
export enum NewsStatus {
  NEW = 'NEW', DEDUPED = 'DEDUPED', FILTERED = 'FILTERED',
  REJECTED = 'REJECTED', SCRIPT_READY = 'SCRIPT_READY', ARCHIVED = 'ARCHIVED',
}

// AgentRunType
export enum AgentRunType { SINGLE_ARTICLE = 'single_article', DIGEST = 'digest', PUSH_PLAN = 'push_plan' }

// AgentBizType
export enum AgentBizType { NEWS = 'news', HOT_TOPIC = 'hot_topic', DIGEST = 'digest' }

// HotTopicStatus
export enum HotTopicStatus { ACTIVE = 'ACTIVE', IGNORED = 'IGNORED', ARCHIVED = 'ARCHIVED' }

// DigestReportType
export enum DigestReportType { DAILY = 'DAILY', WEEKLY = 'WEEKLY', TOPIC = 'TOPIC' }

// DigestReportStatus
export enum DigestReportStatus {
  DRAFT = 'DRAFT', GENERATED = 'GENERATED', PUBLISHED = 'PUBLISHED', ARCHIVED = 'ARCHIVED',
}

// PushPlanStatus
export enum PushPlanStatus {
  PENDING = 'PENDING', SCHEDULED = 'SCHEDULED', EXECUTED = 'EXECUTED',
  FAILED = 'FAILED', CANCELLED = 'CANCELLED',
}

// PushPlanType
export enum PushPlanType { IMMEDIATE = 'IMMEDIATE', DIGEST = 'DIGEST', SCHEDULED = 'SCHEDULED' }

// PushRecordStatus
export enum PushRecordStatus { PENDING = 'PENDING', SENT = 'SENT', FAILED = 'FAILED' }

// VideoStatus
export enum VideoStatus {
  INIT = 'INIT', SCRIPT_GENERATED = 'SCRIPT_GENERATED', AUDIO_READY = 'AUDIO_READY',
  SUBTITLE_READY = 'SUBTITLE_READY', RENDERING = 'RENDERING',
  RENDER_SUCCESS = 'RENDER_SUCCESS', RENDER_FAILED = 'RENDER_FAILED',
  COMPLIANCE_PENDING = 'COMPLIANCE_PENDING', COMPLIANCE_REJECTED = 'COMPLIANCE_REJECTED',
  PUBLISH_READY = 'PUBLISH_READY', PUBLISHED = 'PUBLISHED',
}

// PublishStatus
export enum PublishStatus {
  PENDING = 'PENDING', SCHEDULED = 'SCHEDULED', SUBMITTING = 'SUBMITTING',
  SUCCESS = 'SUCCESS', FAILED = 'FAILED', RETRYING = 'RETRYING', CANCELLED = 'CANCELLED',
}

// ConfigValueType
export enum ConfigValueType {
  STRING = 'STRING', INTEGER = 'INTEGER', FLOAT = 'FLOAT',
  BOOLEAN = 'BOOLEAN', JSON = 'JSON', SECRET = 'SECRET',
}

// FileCategory
export enum FileCategory {
  IMAGE = 'IMAGE', AUDIO = 'AUDIO', VIDEO = 'VIDEO', DOCUMENT = 'DOCUMENT', OTHER = 'OTHER',
}

// OperationStatus
export enum OperationStatus { SUCCESS = 'SUCCESS', FAILED = 'FAILED' }

// PlatformAuthStatus
export enum PlatformAuthStatus {
  UNAUTHORIZED = 'UNAUTHORIZED', AUTHORIZED = 'AUTHORIZED',
  EXPIRED = 'EXPIRED', DISABLED = 'DISABLED',
}
```

---

## 附录 B：开发检查清单（每个模块完成后自检）

### 代码质量
- [ ] TypeScript 编译无错误（`npm run build` 通过）
- [ ] ESLint 无 warning
- [ ] 所有 public 方法有 JSDoc 注释
- [ ] 无 `any` 类型（特殊场景需注释说明原因）
- [ ] 无 `console.log`（使用 Logger）
- [ ] 无硬编码魔法数字（提取为常量）

### 功能正确性
- [ ] API 路径与原后端完全一致
- [ ] 请求参数名和类型与原后端一致
- [ ] 响应 JSON 结构和字段名与原后端一致
- [ ] 错误码和错误消息与原后端一致
- [ ] 权限码与原后端一致
- [ ] 枚举值与原后端一致
- [ ] 分页参数和返回格式一致
- [ ] 时间字段格式为 ISO 8601 UTC

### 安全性
- [ ] 敏感接口都有认证守卫
- [ ] 写操作都有权限校验
- [ ] SQL 注入防护（Prisma 参数化查询）
- [ ] XSS 防护（输出转义）
- [ ] 密码不返回给前端
- [ ] 密码使用 bcrypt 哈希存储

### 性能
- [ ] 列表查询有分页限制（最大 100 条/页）
- [ ] 数据库查询避免 N+1（使用 include/select）
- [ ] 大文本字段列表接口截断（brief 模式）
