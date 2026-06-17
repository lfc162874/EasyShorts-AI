import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class SystemService {
  constructor(private readonly prisma: PrismaService) {}

  // ===== 系统配置 =====
  async listConfigs(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.systemConfig.findMany({
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'asc' },
      }),
      this.prisma.systemConfig.count(),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  async createConfig(data: {
    category: string;
    configKey: string;
    configValue: string;
    valueType?: string;
    description?: string;
    isSecret?: boolean;
  }) {
    return this.prisma.systemConfig.create({ data });
  }

  async updateConfig(id: number, data: Record<string, unknown>) {
    await this.prisma.systemConfig.update({ where: { id }, data });
    return this.prisma.systemConfig.findUnique({ where: { id } });
  }

  // ===== 平台账号 =====
  async listPlatformAccounts(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.platformAccount.findMany({
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.platformAccount.count(),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  async createPlatformAccount(data: {
    platform: string;
    displayName: string;
    accountId: string;
  }) {
    return this.prisma.platformAccount.create({ data });
  }

  async updatePlatformAccount(id: number, data: Record<string, unknown>) {
    await this.prisma.platformAccount.update({ where: { id }, data });
    return this.prisma.platformAccount.findUnique({ where: { id } });
  }

  // ===== 操作日志 =====
  async listOperationLogs(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.operationLog.findMany({
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.operationLog.count(),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  // ===== 错误日志 =====
  async listErrorLogs(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.errorLog.findMany({
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.errorLog.count(),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  // ===== 任务中心 =====
  async listTaskJobs(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.taskJob.findMany({
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.taskJob.count(),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  // ===== Demo 任务 =====
  async createDemoTask(payload: Record<string, unknown>, triggeredBy?: number) {
    const task = await this.prisma.taskJob.create({
      data: {
        taskName: 'demo_healthcheck',
        taskType: 'system',
        queueName: 'system_queue',
        status: 'PENDING',
        triggeredBy,
        payload: payload as object,
      },
    });
    // 模拟执行（后续接入 RabbitMQ 后替换为消息发送）
    const updated = await this.prisma.taskJob.update({
      where: { id: task.id },
      data: {
        status: 'SUCCESS',
        startedAt: new Date(),
        finishedAt: new Date(),
        result: { echo: payload, checkedAt: new Date().toISOString(), worker: 'inline' },
      },
    });
    // 返回更新后的数据（而非创建时的 PENDING 状态快照）
    return updated;
  }
}
