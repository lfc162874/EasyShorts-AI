# AI 热点监控助手 Agent 智能处理模块后端开发计划

**项目名称：** AI 热点监控助手（AI Hotspot Monitoring Assistant）  
**文档版本：** V1.0  
**编写日期：** 2026-04-16  
**适用范围：** Agent 智能处理模块后端开发排期、模块拆分、接口设计、任务编排、联调验收

---

## 一、文档目的

本文档用于指导 `Agent 智能处理模块` 的后端开发工作。  
该模块开发将严格依据下列文档展开：

- [Agent智能处理模块](./Agent智能处理模块.md)
- [需求文档v3](./需求文档v3.md)
- [技术架构文档](./技术架构文档.md)
- [后端开发规范文档](./后端开发规范文档.md)

当前项目的基础设施、采集模块、内容处理底座已经具备，因此本计划不再重复规划登录、权限、来源采集、抓取记录等已完成内容，而是聚焦在：

1. 以 `AgentScope` 为核心的智能处理编排
2. 热点筛选、分类打标、摘要生成、内容扩展、推送决策
3. AI 热点简报生成
4. Agent 执行日志、回放、重试与可视化支撑接口

---

## 二、开发目标

### 2.1 模块目标

基于 [Agent智能处理模块](./Agent智能处理模块.md#L7)，后端需要实现一条完整的智能处理链路：

```text
待处理内容
   │
   ▼
HotspotAgent
   │
   ▼
ClassificationAgent
   │
   ▼
SummaryAgent
   │
   ▼
EnrichmentAgent
   │
   ▼
PushPlannerAgent
   │
   ▼
DigestAgent
   │
   ▼
热点简报 / 推送计划 / 推送执行
```

### 2.2 本阶段要达成的结果

1. 任意一条或一组采集内容都可以进入 Agent 处理流程。
2. 每个 Agent 都有明确输入、输出、状态、日志和中间产物。
3. 可以生成结构化的热点结果、解读结果、推送决策和简报结果。
4. 每一次 Agent 运行都支持查看、重试、回放和追踪。
5. 前端可以通过接口清晰展示每一个 Agent 的处理流程。

---

## 三、后端范围与边界

### 3.1 本阶段包含

1. AgentScope 运行时接入
2. Agent 工作流编排
3. Agent 输入输出结构定义
4. Agent 执行日志与工件持久化
5. 热点筛选、分类、摘要、扩展、推送决策、简报生成服务
6. Agent 任务接口、重试接口、运行详情接口
7. 与 Celery / Redis 的异步任务联动

### 3.2 本阶段不包含

1. 多租户隔离
2. 复杂的人机协作审批流
3. 多模型路由平台
4. 智能体自学习能力
5. 完整的 BI 与运营报表系统

### 3.3 开发原则

1. **AgentScope 是编排中心。** 所有智能处理链路统一走 AgentScope。
2. **结构化优先。** 每个 Agent 的输出必须有稳定 JSON 结构，不能只返回自然语言。
3. **任务可追踪。** 每一步执行都要有状态、耗时、输入摘要、输出摘要、错误信息。
4. **可重试可回放。** 任一 Agent 步骤失败后，要支持整条链路重试或单步重试。
5. **面向前端可视化。** 后端设计要天然支持前端查看“每一个 Agent 的处理流程”。

---

## 四、技术基线

| 模块 | 技术 |
| --- | --- |
| API 服务 | FastAPI |
| Agent 编排 | AgentScope |
| 异步任务 | Celery + Redis |
| 数据库 | PostgreSQL |
| ORM | SQLAlchemy |
| 配置管理 | SystemConfig + 环境变量 |
| 日志 | 系统日志 + Agent 运行日志 |
| 测试 | pytest |

### 4.1 依赖补充

当前 `backend/requirements.txt` 中尚未引入 `AgentScope`，本阶段首先需要补充：

1. `agentscope`
2. 模型 SDK（按最终接入模型补充）
3. Agent 输出结构校验依赖
4. 可选的文本相似度或嵌入依赖

---

## 五、建议的后端模块结构

建议在现有 `backend/app` 下新增以下目录：

```text
backend/app/
├── agents/
│   ├── __init__.py
│   ├── runtime.py
│   ├── context.py
│   ├── prompts/
│   │   ├── hotspot_agent.md
│   │   ├── classification_agent.md
│   │   ├── summary_agent.md
│   │   ├── enrichment_agent.md
│   │   ├── push_planner_agent.md
│   │   └── digest_agent.md
│   ├── hotspot_agent.py
│   ├── classification_agent.py
│   ├── summary_agent.py
│   ├── enrichment_agent.py
│   ├── push_planner_agent.py
│   ├── digest_agent.py
│   └── workflows/
│       └── intelligent_processing_workflow.py
├── services/
│   ├── agent_run_service.py
│   ├── hotspot_service.py
│   ├── digest_service.py
│   └── push_strategy_service.py
├── tasks/
│   └── agent_tasks.py
├── schemas/
│   └── agent.py
└── api/v1/
    └── agent.py
```

---

## 六、Agent 设计与职责拆分

依据 [Agent智能处理模块](./Agent智能处理模块.md#L202)，建议后端固定 6 个核心 Agent。

### 6.1 HotspotAgent

**职责：**

1. 判断内容是否属于 AI 热点
2. 给出热度评分
3. 输出推荐理由
4. 给出是否进入下一阶段

**输入：**

- 标题
- 正文
- 来源
- 发布时间
- 已有热度基础分

**输出：**

```json
{
  "is_hot": true,
  "score": 86,
  "reason": "来源权威、时效性强、命中高热关键词"
}
```

### 6.2 ClassificationAgent

**职责：**

1. 输出主分类
2. 输出标签
3. 输出主题词

**输出：**

```json
{
  "category": "AI Agent",
  "tags": ["Agent", "LLM", "Automation"],
  "keywords": ["OpenAI", "Agent", "Tool Calling"]
}
```

### 6.3 SummaryAgent

**职责：**

1. 生成优化标题
2. 生成一句话摘要
3. 生成 3-5 条核心要点

### 6.4 EnrichmentAgent

**职责：**

1. 输出背景说明
2. 输出行业影响
3. 输出技术解读
4. 输出应用场景

### 6.5 PushPlannerAgent

**职责：**

1. 判断是否立即推送
2. 判断进入日报 / 周报
3. 给出优先级
4. 给出建议渠道

### 6.6 DigestAgent

**职责：**

1. 聚合多条热点结果
2. 生成 AI 热点简报
3. 输出结构化日报 / 周报内容

---

## 七、工作流设计

### 7.1 单条内容处理工作流

```text
内容入池
   │
   ▼
创建 agent_run
   │
   ▼
HotspotAgent
   │
   ├── 非热点 -> 结束并记录结果
   │
   ▼
ClassificationAgent
   │
   ▼
SummaryAgent
   │
   ▼
EnrichmentAgent
   │
   ▼
PushPlannerAgent
   │
   ▼
写回热点结果 / 推送计划 / Agent 工件
```

### 7.2 多条内容简报生成工作流

```text
按时间或规则筛选热点池
   │
   ▼
聚合候选热点
   │
   ▼
DigestAgent
   │
   ▼
生成日报 / 周报
   │
   ▼
进入推送执行链路
```

### 7.3 推荐运行方式

1. API 层只负责创建任务
2. Celery 任务负责启动 AgentScope 工作流
3. AgentRunService 负责写入运行记录和步骤记录
4. 前端通过查询接口查看结果，不直接等待长任务

---

## 八、数据表规划

建议新增以下核心表。

### 8.1 `agent_runs`

用于记录一次完整 Agent 工作流。

核心字段建议：

- `run_type`：single_article / digest / push_plan
- `biz_type`：news / hot_topic / digest
- `biz_id`
- `status`
- `current_step`
- `started_at`
- `finished_at`
- `triggered_by`
- `request_id`
- `error_message`

### 8.2 `agent_run_steps`

用于记录每个 Agent 节点的执行明细。

核心字段建议：

- `run_id`
- `step_code`
- `agent_name`
- `step_order`
- `status`
- `model_name`
- `prompt_version`
- `input_summary`
- `output_summary`
- `started_at`
- `finished_at`
- `duration_ms`
- `error_message`

### 8.3 `agent_run_artifacts`

用于存储中间工件和结构化结果。

核心字段建议：

- `run_id`
- `step_id`
- `artifact_type`
- `artifact_key`
- `content_json`
- `content_text`

### 8.4 `hot_topics`

用于存储热点结果。

核心字段建议：

- `title`
- `summary`
- `category`
- `tags`
- `score`
- `priority`
- `reason`
- `trend`
- `status`

### 8.5 `hot_topic_items`

用于关联热点与原始内容。

核心字段建议：

- `topic_id`
- `news_id`
- `source_id`
- `weight`
- `is_primary`

### 8.6 `digest_reports`

用于存储 AI 热点简报。

核心字段建议：

- `report_type`
- `report_date`
- `title`
- `content`
- `status`
- `topic_count`

### 8.7 `push_plans`

用于存储推送决策结果。

核心字段建议：

- `biz_type`
- `biz_id`
- `push_now`
- `priority`
- `push_type`
- `channels`
- `planned_at`

---

## 九、接口规划

建议新增 `agent` 相关接口组。

### 9.1 Agent 运行接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/easy-shorts/agent/runs/news/{news_id}` | 对单条内容发起 Agent 处理 |
| POST | `/easy-shorts/agent/runs/digest` | 发起简报生成 |
| GET | `/easy-shorts/agent/runs` | Agent 运行列表 |
| GET | `/easy-shorts/agent/runs/{run_id}` | Agent 运行详情 |
| POST | `/easy-shorts/agent/runs/{run_id}/retry` | 重试整个运行 |
| POST | `/easy-shorts/agent/runs/{run_id}/steps/{step_id}/retry` | 重试单步 |

### 9.2 热点结果接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/easy-shorts/hot-topics` | 热点列表 |
| GET | `/easy-shorts/hot-topics/{topic_id}` | 热点详情 |
| POST | `/easy-shorts/hot-topics/{topic_id}/reprocess` | 重新处理热点 |

### 9.3 简报接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/easy-shorts/digests` | 简报列表 |
| GET | `/easy-shorts/digests/{digest_id}` | 简报详情 |
| POST | `/easy-shorts/digests/{digest_id}/push` | 推送指定简报 |

### 9.4 推送决策接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/easy-shorts/push-plans` | 推送计划列表 |
| GET | `/easy-shorts/push-plans/{plan_id}` | 推送计划详情 |
| POST | `/easy-shorts/push-plans/{plan_id}/execute` | 执行推送 |

---

## 十、开发阶段规划

### 阶段 A：AgentScope 接入与运行底座

**目标：** 先把 Agent 运行基础设施搭起来。

**主要任务：**

1. 接入 `AgentScope` 依赖与基础配置
2. 新建 `app/agents` 目录与运行时封装
3. 设计统一 Agent 输入输出 Schema
4. 完成 `agent_runs / agent_run_steps / agent_run_artifacts` 迁移脚本
5. 建立 Celery 与 Agent 工作流联动任务

**交付物：**

- AgentScope 基础运行骨架
- Agent 运行表
- Agent 运行日志接口基础版

### 阶段 B：五个处理 Agent 落地

**目标：** 跑通单条内容智能处理链路。

**主要任务：**

1. 实现 HotspotAgent
2. 实现 ClassificationAgent
3. 实现 SummaryAgent
4. 实现 EnrichmentAgent
5. 实现 PushPlannerAgent
6. 将结果写回 `hot_topics / push_plans / artifacts`

**交付物：**

- 单条内容处理工作流
- 处理结果结构化写回
- 运行详情接口

### 阶段 C：DigestAgent 与简报体系

**目标：** 让系统可以自动生成 AI 热点简报。

**主要任务：**

1. 实现热点聚合逻辑
2. 实现 DigestAgent
3. 新增 `digest_reports`
4. 支持日报 / 周报生成任务
5. 支持导出和再次推送

### 阶段 D：推送执行闭环

**目标：** 打通从智能决策到实际推送的链路。

**主要任务：**

1. 推送渠道抽象
2. 邮件 / 飞书 / 企业微信 / Webhook 接口封装
3. 推送失败重试
4. 推送执行日志
5. 推送记录查询接口

### 阶段 E：稳定性与运维能力

**目标：** 让 Agent 模块可追踪、可维护、可复盘。

**主要任务：**

1. 超时控制
2. 幂等控制
3. Prompt 版本管理
4. 模型配置切换
5. 失败告警
6. 回放与人工复核

---

## 十一、测试计划

### 11.1 单元测试

覆盖：

1. Agent 输入输出结构
2. 结果解析
3. 状态流转
4. 错误处理

### 11.2 集成测试

覆盖：

1. `news -> agent_run -> hot_topic`
2. `hot_topics -> digest_report`
3. `push_plan -> push_record`

### 11.3 回归测试

重点检查：

1. 不影响现有采集模块
2. 不影响内容中心接口
3. Agent 失败时不污染原始数据

---

## 十二、验收标准

满足以下条件可视为后端阶段完成：

1. 支持对内容发起 Agent 智能处理任务。
2. 每个 Agent 节点都能记录执行状态、输入摘要、输出摘要、错误信息和耗时。
3. 能生成结构化热点结果、推送计划和 AI 热点简报。
4. 前端可通过接口完整查看 Agent 流程和每一步结果。
5. 支持整条任务重试和单步重试。
6. Celery 异步执行链路稳定可用。

---

## 十三、建议开发顺序

为了降低风险，后端建议严格按如下顺序推进：

1. 先做 `AgentScope + 运行记录底座`
2. 再做 `HotspotAgent -> ClassificationAgent -> SummaryAgent -> EnrichmentAgent -> PushPlannerAgent`
3. 再做 `DigestAgent`
4. 再做 `推送执行`
5. 最后补 `运维、回放、重试、告警`

这个顺序的好处是：

1. 每一步都有可验证结果
2. 前端能尽早接入流程可视化
3. 不会一开始把推送和简报耦合得太重

