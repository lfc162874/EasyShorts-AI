import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class AgentService {
  constructor(private readonly prisma: PrismaService) {}

  // ===== 配置 =====
  async getConfig() {
    const configs = await this.prisma.systemConfig.findMany({
      where: { category: { in: ['agent', 'parameter'] }, isEnabled: true },
    });
    const map = new Map(configs.map((c) => [c.configKey, c.configValue]));
    return {
      default_model_name: (map.get('default_model_name') as string) || 'qwen3.5-plus',
      supported_models: ((map.get('supported_models') as string) || 'qwen3.5-plus').split(',').map((s) => s.trim()),
      default_provider: (map.get('default_provider') as string) || 'dashscope',
      prompt_version: (map.get('prompt_version') as string) || 'v1',
      push_channels: ((map.get('push_channels') as string) || '').split(',').filter(Boolean),
      hot_threshold: parseInt((map.get('hot_threshold') as string) || '35', 10),
      prompts: Object.fromEntries(
        configs.filter((c) => c.category === 'prompt').map((c) => [c.configKey, c.configValue]),
      ),
    };
  }

  async updateConfig(data: Record<string, unknown>) {
    for (const [key, value] of Object.entries(data)) {
      await this.prisma.systemConfig.upsert({
        where: { category_configKey: { category: 'agent', configKey: key } },
        update: { configValue: String(value) },
        create: { category: 'agent', configKey: key, configValue: String(value), valueType: 'STRING' },
      });
    }
    return this.getConfig();
  }

  getModels() {
    return [
      { value: 'qwen3.5-plus', label: 'Qwen 3.5 Plus', is_default: true },
      { value: 'qwen-max', label: 'Qwen Max', is_default: false },
      { value: 'gpt-4o', label: 'GPT-4o', is_default: false },
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini', is_default: false },
      { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4', is_default: false },
      { value: 'deepseek-chat', label: 'DeepSeek Chat', is_default: false },
    ];
  }

  // ===== 运行记录 =====
  async listRuns(query: { page?: number; page_size?: number; status?: string }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const where: Record<string, unknown> = {};
    if (query.status) where.status = query.status;

    const [items, total] = await Promise.all([
      this.prisma.agentRun.findMany({
        where,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.agentRun.count({ where }),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  async getRun(id: number) {
    const run = await this.prisma.agentRun.findUnique({
      where: { id },
      include: { steps: true, artifacts: true },
    });
    if (!run) throw new Error('Agent 运行记录不存在');
    return run;
  }

  // ===== 热点 =====
  async listHotTopics(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.hotTopic.findMany({
        where: { status: 'ACTIVE' },
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { score: 'desc', id: 'desc' },
      }),
      this.prisma.hotTopic.count({ where: { status: 'ACTIVE' } }),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  // ===== 推送计划 =====
  async listPushPlans(query: { page?: number; page_size?: number }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const [items, total] = await Promise.all([
      this.prisma.pushPlan.findMany({
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.pushPlan.count(),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  async getTopic(id: number) {
    const topic = await this.prisma.hotTopic.findUnique({ where: { id } });
    if (!topic) throw new Error('热点不存在');
    return topic;
  }

  async getPlan(id: number) {
    const plan = await this.prisma.pushPlan.findUnique({ where: { id } });
    if (!plan) throw new Error('推送计划不存在');
    return plan;
  }
}
