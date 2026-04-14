# EasyShorts AI Backend

阶段一后端基础工程已经初始化，当前包含以下能力：

- FastAPI 基础工程与统一接口前缀 `/easy-shorts`
- PostgreSQL 数据访问层与 SQLAlchemy 模型
- Alembic 迁移初始化
- JWT 登录鉴权与 RBAC 基础模型
- 用户、角色、菜单、系统配置、平台账号基础接口
- 新闻源、新闻列表、抓取记录与内容生成接口
- 文件上传与本地存储适配层
- 操作日志、错误日志、任务日志基础查询接口
- Celery 演示任务与 Redis 配置

## 目录说明

```text
backend/
  app/
    api/
    core/
    db/
    integrations/
    schemas/
    services/
    tasks/
  scripts/
  tests/
```

## 本地快速启动

如果你现在要按本机 PostgreSQL 来启动，就走这一条。你的数据库连接建议写成：

```text
postgresql+psycopg://postgres:123456@localhost:5432/easy_shorts
```

这里我先按项目默认数据库名 `easy_shorts` 来写；如果你本机实际库名不同，把最后一段改掉就行。

1. 进入项目根目录并准备虚拟环境：

```bash
cd /Users/lfc/softwear/EasyShortsAI
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
```

2. 准备 `backend/.env`，把数据库地址改成你的本机 PostgreSQL：

```bash
cp backend/.env.example backend/.env
```

然后把 `backend/.env` 里的 `DATABASE_URL` 改成：

```text
DATABASE_URL=postgresql+psycopg://postgres:123456@localhost:5432/easy_shorts
```

3. 执行数据库迁移：

```bash
cd backend
../.venv/bin/alembic upgrade head
```

4. 初始化默认管理员：

```bash
../.venv/bin/python scripts/bootstrap_admin.py
```

5. 启动后端服务：

```bash
../.venv/bin/uvicorn app.main:app --reload --port 8000
```

默认接口地址：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/easy-shorts/health`

默认管理员：

- 用户名：`admin`
- 密码：`Admin@123456`

## Docker 启动

如果你希望一次性拉起 PostgreSQL 和 Redis，再用 Docker 跑完整后端，使用这一套。

1. 直接启动整套服务：

```bash
cd /Users/lfc/softwear/EasyShortsAI
docker compose up --build
```

这会启动：

- `backend`
- `worker`
- `beat`
- `postgres`
- `redis`

注意：

- Docker 方案使用 [backend/.env.docker](/Users/lfc/softwear/EasyShortsAI/backend/.env.docker)
- 本机直连 PostgreSQL 启动使用 [backend/.env](/Users/lfc/softwear/EasyShortsAI/backend/.env)

## 默认管理员

启动或手动执行 `scripts/bootstrap_admin.py` 时，除了默认管理员，还会同步补齐一批基础设施数据：

- 菜单与权限节点
- 默认角色
- 默认示例用户
- 系统配置
- 平台账号占位数据

默认管理员通过环境变量控制：

- 用户名：`BOOTSTRAP_ADMIN_USERNAME`
- 密码：`BOOTSTRAP_ADMIN_PASSWORD`

默认值见 [backend/.env.example](/Users/lfc/softwear/EasyShortsAI/backend/.env.example)。

同时还会创建一个运营示例账号：

- 用户名：`operator`
- 密码：`Operator@123456`

## 已提供的接口

完整字段说明、请求体和返回结构见 [后端接口文档](../doc/后端接口文档.md)。

- `POST /easy-shorts/auth/login`
- `POST /easy-shorts/auth/logout`
- `GET /easy-shorts/auth/me`
- `GET/POST/PUT /easy-shorts/system/users`
- `GET/POST/PUT /easy-shorts/system/roles`
- `PUT /easy-shorts/system/roles/{role_id}/menus`
- `GET/POST/PUT /easy-shorts/system/menus`
- `GET/POST/PUT /easy-shorts/system/configs`
- `GET/POST/PUT /easy-shorts/system/platform-accounts`
- `GET /easy-shorts/system/logs/operations`
- `GET /easy-shorts/system/logs/errors`
- `GET /easy-shorts/system/tasks`
- `POST /easy-shorts/system/tasks/demo`
- `GET/POST/PUT /easy-shorts/news/sources`
- `POST /easy-shorts/news/sources/{source_id}/sync`
- `GET /easy-shorts/news`
- `GET /easy-shorts/news/{news_id}`
- `POST /easy-shorts/news/{news_id}/generate`
- `GET /easy-shorts/news/records`
- `POST /easy-shorts/uploads/files`

## 后续建议

接下来可以基于这套底座继续落阶段三：

1. 配音与字幕链路
2. 视频合成与素材管理
3. 发布审核与平台发布
