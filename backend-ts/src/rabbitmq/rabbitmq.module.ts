import { Module, OnModuleInit } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from '../prisma/prisma.module';

import { RabbitMQConnection } from './rabbitmq.connection';
import { RabbitMQService } from './rabbitmq.service';
import { RabbitMQTaskProcessors } from './rabbitmq.processors';
import { QUEUE_NAMES } from './rabbitmq.interfaces';

@Module({
  imports: [ConfigModule, PrismaModule],
  providers: [
    // 连接管理
    RabbitMQConnection,
    // 高层服务
    RabbitMQService,
    // 任务处理器（注册消费者）
    RabbitMQTaskProcessors,
  ],
  exports: [RabbitMQConnection, RabbitMQService],
})
export class RabbitMQModule implements OnModuleInit {
  constructor(
    private readonly processors: RabbitMQTaskProcessors,
    private readonly connection: RabbitMQConnection,
  ) {}

  /** 模块初始化时注册处理器并建立连接 */
  async onModuleInit() {
    this.processors.registerAll();
    // 建立连接（connect 内部会自动启动消费者）
    await this.connection.connect();
  }
}
