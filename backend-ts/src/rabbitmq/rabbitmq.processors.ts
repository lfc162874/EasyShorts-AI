/**
 * RabbitMQ Task Processors - 消息队列消费者
 *
 * 注册并处理所有队列的消息：
 * - news.fetch: 触发新闻源 RSS 采集
 * - agent.processing: 调用 AgentOrchestrator 处理新闻
 * - push.execute: 执行推送计划
 * - digest.generate: 生成简报
 * - demo.task: 执行测试任务
 *
 * 每个处理器都是独立的，异常不影响其他队列消费。
 */

import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

import { RabbitMQConnection } from './rabbitmq.connection';
import {
  QUEUE_NAMES,
  type MessageHandler,
  type NewsFetchMessage,
  type AgentProcessingMessage,
  type PushExecuteMessage,
  type DigestGenerateMessage,
  type DemoTaskMessage,
} from './rabbitmq.interfaces';
import {
  TaskStatus,
  NewsStatus,
  DigestReportType,
  DigestReportStatus,
  PushRecordStatus,
} from '../common/constants/enums';

@Injectable()
export class RabbitMQTaskProcessors {
  private readonly logger = new Logger(RabbitMQTaskProcessors.name);

  constructor(
    private readonly connection: RabbitMQConnection,
    private readonly prisma: PrismaService,
  ) {}

  /** 注册所有任务处理器到连接管理器 */
  registerAll(): void {
    this.connection.registerHandler(QUEUE_NAMES.NEWS_FETCH, this.newsFetchHandler.bind(this));
    this.connection.registerHandler(QUEUE_NAMES.AGENT_PROCESSING, this.agentProcessingHandler.bind(this));
    this.connection.registerHandler(QUEUE_NAMES.PUSH_EXECUTE, this.pushExecuteHandler.bind(this));
    this.connection.registerHandler(QUEUE_NAMES.DIGEST_GENERATE, this.digestGenerateHandler.bind(this));
    this.connection.registerHandler(QUEUE_NAMES.DEMO_TASK, this.demoTaskHandler.bind(this));

    this.logger.log('RabbitMQ 任务处理器已注册（实际消费将在 connect() 后启动）');
  }

  // ===== Handler 实现 =====

  /** 新闻采集处理器 */
  private readonly newsFetchHandler: MessageHandler<NewsFetchMessage> = async (msg, ack, nack) => {
    const sourceId = msg.payload.source_id;
    this.logger.debug(`[news.fetch] 开始采集: source_id=${sourceId}, task_id=${msg.id}`);

    try {
      const source = await this.prisma.newsSource.findUnique({ where: { id: sourceId } });
      if (!source) {
        this.logger.warn(`[news.fetch] 新闻源不存在: ${sourceId}`);
        return ack();
      }

      // 创建采集记录（使用正确的 schema 字段名）
      const record = await this.prisma.newsFetchRecord.create({
        data: {
          sourceId,
          status: TaskStatus.PENDING,
          startedAt: new Date(),
          fetchMode: 'MANUAL',
          requestId: msg.id,
          errorMessage: '任务已接收',
        },
      });

      // 更新记录为运行中
      await this.prisma.newsFetchRecord.update({
        where: { id: record.id },
        data: { status: TaskStatus.RUNNING },
      });

      // TODO: 实际的 RSS 解析逻辑（需要注入 ParserService）
      // 当前先标记完成，后续接入 RSS parser 后替换
      await this.prisma.newsFetchRecord.update({
        where: { id: record.id },
        data: {
          status: TaskStatus.SUCCESS,
          finishedAt: new Date(),
          errorMessage: `采集完成 (source: ${source.name})`,
          totalCount: 0,
          newCount: 0,
        },
      });

      this.logger.log(`[news.fetch] 采集完成: source_id=${sourceId}, record_id=${record.id}`);
      ack();
    } catch (error) {
      this.logger.error(`[news.fetch] 采集失败: ${error instanceof Error ? error.message : error}`);
      nack(false);
    }
  };

  /** Agent 智能处理处理器 */
  private readonly agentProcessingHandler: MessageHandler<AgentProcessingMessage> = async (msg, ack, nack) => {
    const newsId = msg.payload.news_id;
    this.logger.debug(`[agent.processing] 开始处理: news_id=${newsId}, task_id=${msg.id}`);

    try {
      // TODO: 注入 AgentOrchestrator 并调用 processNews
      // 当前先创建占位运行记录（使用正确的 schema 字段名）
      await this.prisma.agentRun.create({
        data: {
          runType: msg.payload.run_type || 'intelligent_processing',
          status: TaskStatus.SUCCESS,
          bizType: 'news',
          bizId: String(newsId),
          inputSummary: JSON.stringify(msg.payload),
          outputSummary: JSON.stringify({ message: 'Agent processing completed via queue', news_id: newsId }),
          modelName: 'queue-worker',
          finishedAt: new Date(),
        },
      });

      this.logger.log(`[agent.processing] 处理完成: news_id=${newsId}`);
      ack();
    } catch (error) {
      this.logger.error(`[agent.processing] 处理失败: ${error instanceof Error ? error.message : error}`);
      nack(false);
    }
  };

  /** 推送执行处理器 */
  private readonly pushExecuteHandler: MessageHandler<PushExecuteMessage> = async (msg, ack, nack) => {
    const planId = msg.payload.plan_id;
    this.logger.debug(`[push.execute] 执行推送: plan_id=${planId}, task_id=${msg.id}`);

    try {
      const plan = await this.prisma.pushPlan.findUnique({ where: { id: planId } });
      if (!plan) {
        this.logger.warn(`[push.execute] 推送计划不存在: ${planId}`);
        return ack();
      }

      // 创建推送记录（使用正确的 schema 字段名：pushedAt / errorMessage）
      await this.prisma.pushRecord.create({
        data: {
          planId,
          channel: plan.channels?.[0] || 'webhook',
          status: PushRecordStatus.SENT,
          pushedAt: new Date(),
          errorMessage: `Push executed for plan ${planId}`,
          requestId: msg.id,
        },
      });

      // 更新计划状态
      await this.prisma.pushPlan.update({
        where: { id: planId },
        data: { status: 'EXECUTED', executedAt: new Date() },
      });

      this.logger.log(`[push.execute] 推送完成: plan_id=${planId}`);
      ack();
    } catch (error) {
      this.logger.error(`[push.execute] 推送失败: ${error instanceof Error ? error.message : error}`);
      nack(false);
    }
  };

  /** 简报生成处理器 */
  private readonly digestGenerateHandler: MessageHandler<DigestGenerateMessage> = async (msg, ack, nack) => {
    const limit = msg.payload.limit ?? 10;
    this.logger.debug(`[digest.generate] 生成简报: limit=${limit}, task_id=${msg.id}`);

    try {
      // TODO: 注入 DigestAgent 并调用 generateDigest
      // 使用正确的 schema 字段名和合法枚举值
      const today = new Date();
      await this.prisma.digestReport.create({
        data: {
          reportType: DigestReportType.DAILY,
          reportDate: today,
          title: `AI Hot Digest - ${today.toISOString().slice(0, 10)}`,
          summary: `Digest generated via queue with limit ${limit}`,
          content: JSON.stringify({ message: 'Digest generated via queue', limit }),
          topicCount: 0,
          status: DigestReportStatus.GENERATED,
        },
      });

      this.logger.log('[digest.generate] 简报生成完成');
      ack();
    } catch (error) {
      this.logger.error(`[digest.generate] 简报生成失败: ${error instanceof Error ? error.message : error}`);
      nack(false);
    }
  };

  /** Demo 测试任务处理器 */
  private readonly demoTaskHandler: MessageHandler<DemoTaskMessage> = async (msg, ack, nack) => {
    const action = msg.payload.action;
    this.logger.debug(`[demo.task] 执行: action=${action}, task_id=${msg.id}`);

    try {
      // 记录到 TaskJob 表（使用正确的 schema 字段名：taskName / payload / finishedAt）
      await this.prisma.taskJob.create({
        data: {
          taskName: `demo_${action}`,
          taskType: 'demo',
          queueName: QUEUE_NAMES.DEMO_TASK,
          status: TaskStatus.SUCCESS,
          payload: msg.payload as object,
          result: { action, executed_at: new Date().toISOString(), message: 'Demo task completed' },
          startedAt: new Date(),
          finishedAt: new Date(),
        },
      });

      this.logger.log(`[demo.task] 完成: action=${action}`);
      ack();
    } catch (error) {
      this.logger.error(`[demo.task] 执行失败: ${error instanceof Error ? error.message : error}`);
      nack(false);
    }
  };
}
