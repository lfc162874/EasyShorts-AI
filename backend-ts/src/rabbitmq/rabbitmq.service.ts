/**
 * RabbitMQ Service - 高层消息队列服务
 *
 * 提供：
 * - 发布任务到队列（自动降级为内联执行）
 * - 任务状态查询
 * - 队列健康检查
 *
 * 设计原则：
 * - RabbitMQ 不可用时，自动降级为内联同步执行
 * - 所有 publish 方法都返回是否成功入队
 */

import { Injectable, Logger } from '@nestjs/common';
import { v4 as uuidv4 } from 'uuid';

import { RabbitMQConnection } from './rabbitmq.connection';
import {
  QUEUE_NAMES,
  type NewsFetchMessage,
  type AgentProcessingMessage,
  type PushExecuteMessage,
  type DigestGenerateMessage,
  type DemoTaskMessage,
} from './rabbitmq.interfaces';

@Injectable()
export class RabbitMQService {
  private readonly logger = new Logger(RabbitMQService.name);

  constructor(private readonly connection: RabbitMQConnection) {}

  /** 检查 RabbitMQ 是否可用 */
  get isAvailable(): boolean {
    return this.connection.isConnected;
  }

  /**
   * 发布新闻采集任务
   */
  async publishNewsFetch(sourceId: number, force = false): Promise<{ sent: boolean; task_id: string }> {
    const taskId = uuidv4();
    const msg: NewsFetchMessage = {
      id: taskId,
      task_type: 'news.fetch',
      created_at: new Date().toISOString(),
      payload: { source_id: sourceId, force },
    };

    const sent = await this.connection.publish(QUEUE_NAMES.NEWS_FETCH, msg);
    if (!sent) {
      this.logger.warn(`新闻采集任务未入队（RabbitMQ 不可用）: source_id=${sourceId}`);
    }
    return { sent, task_id: taskId };
  }

  /**
   * 发布 Agent 智能处理任务
   */
  async publishAgentProcessing(newsId: number, runType?: string): Promise<{ sent: boolean; task_id: string }> {
    const taskId = uuidv4();
    const msg: AgentProcessingMessage = {
      id: taskId,
      task_type: 'agent.processing',
      created_at: new Date().toISOString(),
      payload: { news_id: newsId, run_type: runType },
    };

    const sent = await this.connection.publish(QUEUE_NAMES.AGENT_PROCESSING, msg);
    if (!sent) {
      this.logger.warn(`Agent 处理任务未入队（RabbitMQ 不可用）: news_id=${newsId}`);
    }
    return { sent, task_id: taskId };
  }

  /**
   * 发布推送执行任务
   */
  async publishPushExecute(planId: number): Promise<{ sent: boolean; task_id: string }> {
    const taskId = uuidv4();
    const msg: PushExecuteMessage = {
      id: taskId,
      task_type: 'push.execute',
      created_at: new Date().toISOString(),
      payload: { plan_id: planId },
    };

    const sent = await this.connection.publish(QUEUE_NAMES.PUSH_EXECUTE, msg);
    if (!sent) {
      this.logger.warn(`推送执行任务未入队（RabbitMQ 不可用）: plan_id=${planId}`);
    }
    return { sent, task_id: taskId };
  }

  /**
   * 发布简报生成任务
   */
  async publishDigestGenerate(limit = 10): Promise<{ sent: boolean; task_id: string }> {
    const taskId = uuidv4();
    const msg: DigestGenerateMessage = {
      id: taskId,
      task_type: 'digest.generate',
      created_at: new Date().toISOString(),
      payload: { limit },
    };

    const sent = await this.connection.publish(QUEUE_NAMES.DIGEST_GENERATE, msg);
    if (!sent) {
      this.logger.warn(`简报生成任务未入队（RabbitMQ 不可用）`);
    }
    return { sent, task_id: taskId };
  }

  /**
   * 发布 Demo 测试任务
   */
  async publishDemoTask(action: string, params?: Record<string, unknown>): Promise<{ sent: boolean; task_id: string }> {
    const taskId = uuidv4();
    const msg: DemoTaskMessage = {
      id: taskId,
      task_type: 'demo.task',
      created_at: new Date().toISOString(),
      payload: { action, params },
    };

    const sent = await this.connection.publish(QUEUE_NAMES.DEMO_TASK, msg);
    if (!sent) {
      this.logger.warn(`Demo 任务未入队（RabbitMQ 不可用）: action=${action}`);
    }
    return { sent, task_id: taskId };
  }

  /** 获取连接状态信息 */
  getStatus(): {
    available: boolean;
    state: string;
    queues: string[];
  } {
    return {
      available: this.isAvailable,
      state: this.connection.state,
      queues: Object.values(QUEUE_NAMES),
    };
  }
}
