/**
 * RabbitMQ 队列定义和类型
 *
 * 队列命名规范: {domain}.{action}
 * 路由键格式: {queue_name}
 */

// ===== 队列名称 =====

export const QUEUE_NAMES = {
  /** 新闻采集任务 */
  NEWS_FETCH: 'news.fetch',
  /** Agent 智能处理任务 */
  AGENT_PROCESSING: 'agent.processing',
  /** 推送执行任务 */
  PUSH_EXECUTE: 'push.execute',
  /** 简报生成任务 */
  DIGEST_GENERATE: 'digest.generate',
  /** Demo/测试任务 */
  DEMO_TASK: 'demo.task',
} as const;

/** 所有队列名称列表（用于启动时批量声明） */
export const ALL_QUEUES = Object.values(QUEUE_NAMES);

// ===== Exchange =====

export const EXCHANGE_NAME = 'easy-shorts.direct';
export const EXCHANGE_TYPE = 'direct';

// ===== 消息类型 =====

export type QueueName = (typeof QUEUE_NAMES)[keyof typeof QUEUE_NAMES];

/** 基础消息结构 */
export interface BaseMessage {
  id?: string;
  task_type: string;
  created_at: string;
  payload: Record<string, unknown>;
}

/** 新闻采集消息 */
export interface NewsFetchMessage extends BaseMessage {
  task_type: 'news.fetch';
  payload: {
    source_id: number;
    force?: boolean;
  };
}

/** Agent 处理消息 */
export interface AgentProcessingMessage extends BaseMessage {
  task_type: 'agent.processing';
  payload: {
    news_id: number;
    run_type?: string;
  };
}

/** 推送执行消息 */
export interface PushExecuteMessage extends BaseMessage {
  task_type: 'push.execute';
  payload: {
    plan_id: number;
  };
}

/** 简报生成消息 */
export interface DigestGenerateMessage extends BaseMessage {
  task_type: 'digest.generate';
  payload: {
    limit?: number;
  };
}

/** Demo 任务消息 */
export interface DemoTaskMessage extends BaseMessage {
  task_type: 'demo.task';
  payload: {
    action: string;
    params?: Record<string, unknown>;
  };
}

/** 消息处理器函数签名 */
export type MessageHandler<T extends BaseMessage = BaseMessage> = (
  msg: T,
  ack: () => void,
  nack: (requeue?: boolean) => void,
) => Promise<void>;

/** 连接状态 */
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}
