/**
 * 系统常量定义
 * 与原 Python 后端 app/core/constants.py 完全对齐
 */

// ===== 用户相关 =====
export enum UserStatus {
  ACTIVE = 'ACTIVE',
  DISABLED = 'DISABLED',
}

export enum MenuType {
  DIRECTORY = 'DIRECTORY',
  MENU = 'MENU',
  BUTTON = 'BUTTON',
}

// ===== 任务状态 =====
export enum TaskStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  RETRYING = 'RETRYING',
  CANCELLED = 'CANCELLED',
}

export enum PlatformAuthStatus {
  UNAUTHORIZED = 'UNAUTHORIZED',
  AUTHORIZED = 'AUTHORIZED',
  EXPIRED = 'EXPIRED',
  DISABLED = 'DISABLED',
}

// ===== 新闻相关 =====
export enum NewsSourceType {
  RSS = 'RSS',
  ATOM = 'ATOM',
  WEB = 'WEB',
  MANUAL = 'MANUAL',
}

export enum NewsFetchMode {
  MANUAL = 'MANUAL',
  SCHEDULED = 'SCHEDULED',
}

export enum NewsStatus {
  NEW = 'NEW',
  DEDUPED = 'DEDUPED',
  FILTERED = 'FILTERED',
  REJECTED = 'REJECTED',
  SCRIPT_READY = 'SCRIPT_READY',
  ARCHIVED = 'ARCHIVED',
}

// ===== Agent 运行 =====
export enum AgentRunType {
  SINGLE_ARTICLE = 'single_article',
  INTELLIGENT_PROCESSING = 'intelligent_processing',
  DIGEST = 'digest',
  PUSH_PLAN = 'push_plan',
}

export enum AgentBizType {
  NEWS = 'news',
  HOT_TOPIC = 'hot_topic',
  DIGEST = 'digest',
}

// ===== 热点 =====
export enum HotTopicStatus {
  ACTIVE = 'ACTIVE',
  IGNORED = 'IGNORED',
  ARCHIVED = 'ARCHIVED',
}

// ===== Digest 报告 =====
export enum DigestReportType {
  DAILY = 'DAILY',
  WEEKLY = 'WEEKLY',
  TOPIC = 'TOPIC',
}

export enum DigestReportStatus {
  DRAFT = 'DRAFT',
  GENERATED = 'GENERATED',
  PUBLISHED = 'PUBLISHED',
  ARCHIVED = 'ARCHIVED',
}

// ===== 推送计划 =====
export enum PushPlanStatus {
  PENDING = 'PENDING',
  SCHEDULED = 'SCHEDULED',
  EXECUTED = 'EXECUTED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export enum PushPlanType {
  IMMEDIATE = 'IMMEDIATE',
  DIGEST = 'DIGEST',
  SCHEDULED = 'SCHEDULED',
}

export enum PushRecordStatus {
  PENDING = 'PENDING',
  SENT = 'SENT',
  FAILED = 'FAILED',
}

// ===== 视频 / 发布 =====
export enum VideoStatus {
  INIT = 'INIT',
  SCRIPT_GENERATED = 'SCRIPT_GENERATED',
  AUDIO_READY = 'AUDIO_READY',
  SUBTITLE_READY = 'SUBTITLE_READY',
  RENDERING = 'RENDERING',
  RENDER_SUCCESS = 'RENDER_SUCCESS',
  RENDER_FAILED = 'RENDER_FAILED',
  COMPLIANCE_PENDING = 'COMPLIANCE_PENDING',
  COMPLIANCE_REJECTED = 'COMPLIANCE_REJECTED',
  PUBLISH_READY = 'PUBLISH_READY',
  PUBLISHED = 'PUBLISHED',
}

export enum PublishStatus {
  PENDING = 'PENDING',
  SCHEDULED = 'SCHEDULED',
  SUBMITTING = 'SUBMITTING',
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  RETRYING = 'RETRYING',
  CANCELLED = 'CANCELLED',
}

// ===== 配置值类型 =====
export enum ConfigValueType {
  STRING = 'STRING',
  INTEGER = 'INTEGER',
  FLOAT = 'FLOAT',
  BOOLEAN = 'BOOLEAN',
  JSON = 'JSON',
  SECRET = 'SECRET',
}

// ===== 文件分类 =====
export enum FileCategory {
  IMAGE = 'IMAGE',
  AUDIO = 'AUDIO',
  VIDEO = 'VIDEO',
  DOCUMENT = 'DOCUMENT',
  OTHER = 'OTHER',
}

// ===== 操作结果 =====
export enum OperationStatus {
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
}
