/**
 * RabbitMQ Connection Manager
 *
 * 管理与 RabbitMQ 的连接生命周期：
 * - 懒连接（首次使用时建立）
 * - 自动重连（指数退避）
 * - 优雅关闭
 * - 连接状态监控
 */

import { Injectable, Logger, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import amqp, { Channel, Connection, ConsumeMessage } from 'amqplib';

import { ALL_QUEUES, EXCHANGE_NAME, EXCHANGE_TYPE, ConnectionState } from './rabbitmq.interfaces';
import type { MessageHandler, BaseMessage } from './rabbitmq.interfaces';

@Injectable()
export class RabbitMQConnection implements OnModuleDestroy {
  private readonly logger = new Logger(RabbitMQConnection.name);

  private _connection: Connection | null = null;
  private _channel: Channel | null = null;
  private _state = ConnectionState.DISCONNECTED;
  private _reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _reconnectAttempts = 0;
  private readonly MAX_RECONNECT_ATTEMPTS = 10;

  /** 已注册的消息处理器 */
  private readonly handlers = new Map<string, MessageHandler>();

  constructor(private readonly configService: ConfigService) {}

  /** 当前连接状态 */
  get state(): ConnectionState {
    return this._state;
  }

  /** 是否已连接 */
  get isConnected(): boolean {
    return this._state === ConnectionState.CONNECTED && !!this._channel;
  }

  /** 获取当前 channel（供内部使用） */
  get channel(): Channel | null {
    return this._channel;
  }

  /**
   * 建立连接并初始化队列
   * 首次调用时懒初始化，后续调用返回已有连接
   */
  async connect(): Promise<Channel | null> {
    if (this.isConnected) {
      return this._channel;
    }

    if (this._state === ConnectionState.CONNECTING || this._state === ConnectionState.RECONNECTING) {
      // 等待正在进行的连接
      await this.waitForConnection();
      return this._channel;
    }

    const uri = this.configService.get<string>('rabbitmq.uri');
    if (!uri) {
      this.logger.warn('RABBITMQ_URI 未配置，RabbitMQ 将不可用');
      return null;
    }

    this._state = ConnectionState.CONNECTING;

    try {
      this.logger.log(`正在连接 RabbitMQ... (尝试 ${this._reconnectAttempts + 1})`);

      this._connection = await amqp.connect(uri);
      this._channel = await this._connection.createChannel();

      // 监听连接错误
      this._connection.on('error', (err) => {
        this.logger.error(`RabbitMQ 连接错误: ${err.message}`);
        this._state = ConnectionState.ERROR;
      });

      this._connection.on('close', () => {
        this.logger.warn('RabbitMQ 连接已关闭');
        this._state = ConnectionState.DISCONNECTED;
        this._channel = null;
        this.scheduleReconnect();
      });

      // 声明 exchange
      await this._channel.assertExchange(EXCHANGE_NAME, EXCHANGE_TYPE, { durable: true });

      // 声明所有队列并绑定
      for (const queueName of ALL_QUEUES) {
        await this._channel.assertQueue(queueName, { durable: true });
        await this._channel.bindQueue(queueName, EXCHANGE_NAME, queueName);
        this.logger.debug(`Queue declared: ${queueName}`);
      }

      this._state = ConnectionState.CONNECTED;
      this._reconnectAttempts = 0;
      this.logger.log('RabbitMQ 连接成功');

      // 启动消费者
      await this.startConsumers();

      return this._channel;
    } catch (error) {
      this._state = ConnectionState.ERROR;
      this.logger.error(
        `RabbitMQ 连接失败: ${error instanceof Error ? error.message : error}`,
      );
      this.scheduleReconnect();
      return null;
    }
  }

  /**
   * 发布消息到指定队列
   *
   * @param queue 目标队列名
   * @param payload 消息负载
   * @returns 是否发布成功
   */
  async publish<T extends BaseMessage>(queue: string, payload: T): Promise<boolean> {
    const ch = await this.connect();
    if (!ch) {
      this.logger.debug(`RabbitMQ 不可用，消息未发送到 ${queue}`);
      return false;
    }

    try {
      const buffer = Buffer.from(JSON.stringify(payload));
      ch.publish(EXCHANGE_NAME, queue, buffer, {
        persistent: true,
        contentType: 'application/json',
        messageId: payload.id,
      });
      this.logger.debug(`消息已发布到 ${queue}: id=${payload.id}`);
      return true;
    } catch (error) {
      this.logger.error(`消息发布失败 [${queue}]: ${error instanceof Error ? error.message : error}`);
      return false;
    }
  }

  /**
   * 注册消息处理器
   */
  registerHandler(queueName: string, handler: MessageHandler): void {
    this.handlers.set(queueName, handler);
    this.logger.debug(`Handler registered for queue: ${queueName}`);
  }

  /** 优雅关闭 */
  async onModuleDestroy() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }

    if (this._channel) {
      try {
        await this._channel.close();
      } catch {
        // ignore
      }
    }

    if (this._connection) {
      try {
        await this._connection.close();
      } catch {
        // ignore
      }
    }

    this._state = ConnectionState.DISCONNECTED;
    this.logger.log('RabbitMQ 连接已优雅关闭');
  }

  // ===== 内部方法 =====

  /** 启动所有已注册的消费者 */
  private async startConsumers(): Promise<void> {
    if (!this._channel) return;

    for (const [queueName, handler] of this.handlers) {
      try {
        await this._channel.consume(queueName, async (msg: ConsumeMessage | null) => {
          if (!msg) return;

          let parsed: BaseMessage;
          try {
            parsed = JSON.parse(msg.content.toString());
          } catch {
            this.logger.warn(`无法解析消息 [${queueName}]，丢弃`);
            this._channel!.ack(msg);
            return;
          }

          try {
            await handler(parsed as any, () => this._channel!.ack(msg), (requeue = false) =>
              this._channel!.nack(msg, false, requeue),
            );
          } catch (error) {
            this.logger.error(
              `消息处理异常 [${queueName}]: ${error instanceof Error ? error.message : error}`,
            );
            this._channel!.nack(msg, false, false); // 不重新入队，避免死循环
          }
        }, { noAck: false });
        this.logger.debug(`Consumer started for: ${queueName}`);
      } catch (error) {
        this.logger.error(`启动消费者失败 [${queueName}]: ${error}`);
      }
    }
  }

  /** 安排重连 */
  private scheduleReconnect(): void {
    if (this._reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
      this.logger.error(`已达到最大重连次数 (${this.MAX_RECONNECT_ATTEMPTS})，停止重连`);
      return;
    }

    this._reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this._reconnectAttempts), 30000); // max 30s

    this.logger.warn(`${delay / 1000}s 后尝试第 ${this._reconnectAttempts} 次重连...`);

    this._reconnectTimer = setTimeout(async () => {
      this._state = ConnectionState.RECONNECTING;
      await this.connect();
    }, delay);
  }

  /** 等待连接完成 */
  private waitForConnection(timeoutMs = 10000): Promise<void> {
    return new Promise((resolve) => {
      const startTime = Date.now();
      const check = () => {
        if (this.isConnected || Date.now() - startTime >= timeoutMs) {
          resolve();
        } else {
          setTimeout(check, 100);
        }
      };
      check();
    });
  }
}
