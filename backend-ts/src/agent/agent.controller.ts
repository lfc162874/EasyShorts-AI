import { Controller, Get, Post, Put, Body, Param, Query, UseGuards } from '@nestjs/common';
import { AgentService } from './agent.service';
import { AgentOrchestrator } from '../agents/agents.orchestrator';
import { PaginationDto } from '../common/dto/pagination.dto';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('agent')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class AgentController {
  constructor(
    private readonly agentService: AgentService,
    private readonly orchestrator: AgentOrchestrator,
  ) {}

  // ===== 配置 =====
  @Get('config')
  @Permissions('agent:config:list')
  async getConfig() {
    return this.agentService.getConfig();
  }

  @Put('config')
  @Permissions('agent:config:update')
  async saveConfig(@Body() dto: Record<string, unknown>) {
    return this.agentService.updateConfig(dto);
  }

  @Get('models')
  @Permissions('agent:model:list')
  async getModels() {
    return this.agentService.getModels();
  }

  // ===== 运行记录 =====
  @Get('runs')
  @Permissions('agent:run:list')
  async listRuns(@Query() query: PaginationDto & { status?: string }) {
    return this.agentService.listRuns(query);
  }

  @Get('runs/:id')
  @Permissions('agent:run:list')
  async getRun(@Param('id') id: string) {
    return this.agentService.getRun(+id);
  }

  /**
   * 手动触发新闻的 Agent 处理（兼容旧接口，内部走编排器）
   */
  @Post('runs/news/:newsId')
  @Permissions('agent:run:create')
  async runNewsAgent(@Param('newsId') newsId: string) {
    const result = await this.orchestrator.processNews(+newsId);
    return { message: 'Agent 处理完成', run_id: result.run_id, is_hot: result.is_hot };
  }

  /** 重试 Agent 运行 */
  @Post('runs/:id/retry')
  @Permissions('agent:run:create')
  async retryAgentRun(@Param('id') id: string) {
    // TODO: 实现重试逻辑（重新执行失败的步骤）
    return { message: `重试任务已提交: run_id=${id}`, run_id: +id };
  }

  /** 重试 Agent 运行的单个步骤 */
  @Post('runs/:id/steps/:stepId/retry')
  @Permissions('agent:run:create')
  async retryAgentRunStep(
    @Param('id') id: string,
    @Param('stepId') stepId: string,
  ) {
    // TODO: 实现单步重试逻辑
    return { message: `重试步骤已提交: run_id=${id}, step_id=${stepId}` };
  }

  /**
   * 智能处理单条新闻
   * 触发完整 Agent 流水线：Hotspot → Classification → Summary → Enrichment → PushPlan
   */
  @Post('intelligent-processing/news/:newsId')
  @Permissions('agent:run:create')
  async intelligentProcessing(@Param('newsId') newsId: string) {
    const result = await this.orchestrator.processNews(+newsId);
    return result;
  }

  /**
   * 生成 AI 热点简报
   * 聚合多条热点内容生成简报
   */
  @Post('generate-digest')
  @Permissions('agent:digest:create')
  async generateDigest(@Body() body?: { limit?: number }) {
    return this.orchestrator.generateDigest(body);
  }

  // ===== 热点 =====
  @Get('hot-topics')
  @Permissions('agent:hot-topic:list')
  async listTopics(@Query() query: PaginationDto) {
    return this.agentService.listHotTopics(query);
  }

  @Get('hot-topics/:id')
  @Permissions('agent:hot-topic:list')
  async getTopic(@Param('id') id: string) {
    return this.agentService.getTopic(+id);
  }

  // ===== 推送计划 =====
  @Get('push-plans')
  @Permissions('agent:push-plan:list')
  async listPlans(@Query() query: PaginationDto) {
    return this.agentService.listPushPlans(query);
  }

  @Get('push-plans/:id')
  @Permissions('agent:push-plan:list')
  async getPlan(@Param('id') id: string) {
    return this.agentService.getPlan(+id);
  }

  /** 执行推送计划 */
  @Post('push-plans/:id/execute')
  @Permissions('agent:push-plan:update')
  async executePushPlan(@Param('id') id: string) {
    // TODO: 接入 RabbitMQ 推送任务或直接执行推送
    return { message: `推送计划已执行: plan_id=${+id}`, plan_id: +id };
  }
}
