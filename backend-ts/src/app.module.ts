import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ScheduleModule } from '@nestjs/schedule';
import configuration from './config/configuration';

// 模块
import { HealthModule } from './health/health.module';
import { AuthModule } from './auth/auth.module';
import { UserModule } from './user/user.module';
import { RoleModule } from './role/role.module';
import { MenuModule } from './menu/menu.module';
import { SystemModule } from './system/system.module';
import { NewsModule } from './news/news.module';
import { AgentModule } from './agent/agent.module';
import { RabbitMQModule } from './rabbitmq/rabbitmq.module';
import { StorageModule } from './storage/storage.module';

// 全局模块
import { PrismaModule } from './prisma/prisma.module';

@Module({
  imports: [
    // 配置（全局）
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['.env.local', '.env'],
    }),

    // 定时任务
    ScheduleModule.forRoot(),

    // 数据库（全局）
    PrismaModule,

    // 功能模块
    HealthModule,
    AuthModule,
    UserModule,
    RoleModule,
    MenuModule,
    SystemModule,
    NewsModule,
    AgentModule,
    RabbitMQModule,
    StorageModule,
  ],
})
export class AppModule {}
