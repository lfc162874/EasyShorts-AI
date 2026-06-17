/**
 * AgentOrchestrator — 智能处理编排器
 *
 * 编排 6 个 Agent 的完整流水线：
 *   HotspotAgent → ClassificationAgent → SummaryAgent → EnrichmentAgent → PushPlannerAgent
 *   + DigestAgent（独立，聚合多条热点）
 *
 * 对应 Python 端 workflows/intelligent_processing.py
 *
 * 设计原则：
 * - 每步都有独立的 AI 调用和规则降级
 * - 流水线任一步失败不影响后续步骤（各步骤有 fallback）
 * - 完整的执行记录写入 DB（AgentRun / AgentRunStep）
 */

import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { ConfigService } from '@nestjs/config';
import {
  AgentRunType,
  TaskStatus,
  AgentBizType,
  NewsStatus,
} from '../common/constants/enums';

import { AgentScopeRuntimeService } from './agents.runtime';
import { HotspotAgent } from './hotspot.agent';
import { ClassificationAgent } from './classification.agent';
import { SummaryAgent } from './summary.agent';
import { EnrichmentAgent } from './enrichment.agent';
import { PushPlannerAgent } from './push-planner.agent';
import { DigestAgent } from './digest.agent';
import type {
  AgentExecutionContext,
  ContentProcessingOutput,
  DigestItemInput,
  DigestOutput,
  EnrichmentOutput,
  HotspotOutput,
  PushPlanOutput,
  SummaryOutput,
  ClassificationOutput,
} from './agents.types';

/** 编排器输出结果 */
export interface OrchestratorResult {
  /** Agent 运行记录 ID */
  run_id: number;
  /** 是否为热点 */
  is_hot: boolean;
  /** 热点判断结果 */
  hotspot: HotspotOutput;
  /** 分类结果 */
  classification: ClassificationOutput;
  /** 摘要结果 */
  summary: SummaryOutput;
  /** 增强结果 */
  enrichment: EnrichmentOutput;
  /** 推送计划 */
  push_plan: PushPlanOutput;
  /** 聚合内容处理输出（给前端用） */
  content_processing: ContentProcessingOutput;
}

@Injectable()
export class AgentOrchestrator {
  private readonly logger = new Logger(AgentOrchestrator.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly configService: ConfigService,
    private readonly runtime: AgentScopeRuntimeService,
    private readonly hotspotAgent: HotspotAgent,
    private readonly classificationAgent: ClassificationAgent,
    private readonly summaryAgent: SummaryAgent,
    private readonly enrichmentAgent: EnrichmentAgent,
    private readonly pushPlannerAgent: PushPlannerAgent,
    private readonly digestAgent: DigestAgent,
  ) {}

  /**
   * 智能处理单条新闻（完整流水线）
   * 对应 POST /agent/intelligent-processing
   */
  async processNews(newsId: number): Promise<OrchestratorResult> {
    // 1. 加载新闻数据
    const news = await this.prisma.news.findUnique({ where: { id: newsId } });
    if (!news) {
      throw new Error(`新闻不存在: id=${newsId}`);
    }

    // 2. 构建执行上下文
    const ctx = await this.buildContext(news);

    // 3. 创建运行记录（使用正确的 Prisma schema 字段名）
    const run = await this.prisma.agentRun.create({
      data: {
        runType: AgentRunType.INTELLIGENT_PROCESSING,
        status: TaskStatus.RUNNING,
        bizType: AgentBizType.NEWS,
        bizId: String(newsId),
        modelName: ctx.model_name,
        promptVersion: ctx.prompt_version,
        inputSummary: JSON.stringify({ news_id: newsId }),
      },
    });
    const runId = run.id;

    try {
      // ===== Step 1: 热点判断 =====
      const step1Start = Date.now();
      let hotspot = await this.hotspotAgent.run(ctx);
      let hotspotUsedAI = this.runtime.isAvailable();
      await this.recordStep(runId, 'HotspotAgent', TaskStatus.SUCCESS, hotspot, Date.now() - step1Start, 1, ctx);

      if (!hotspot.is_hot) {
        // 非热点：只记录，不继续处理
        await this.prisma.agentRun.update({
          where: { id: runId },
          data: {
            status: TaskStatus.SUCCESS,
            outputSummary: JSON.stringify(hotspot),
            finishedAt: new Date(),
          },
        });
        return this.buildNonHotResult(runId, hotspot, ctx);
      }

      // ===== Step 2: 分类 =====
      const step2Start = Date.now();
      const classification = await this.classificationAgent.run(ctx, hotspot);
      await this.recordStep(runId, 'ClassificationAgent', TaskStatus.SUCCESS, classification, Date.now() - step2Start, 2, ctx);

      // ===== Step 3: 摘要生成 =====
      const step3Start = Date.now();
      const summary = await this.summaryAgent.run(ctx, classification);
      await this.recordStep(runId, 'SummaryAgent', TaskStatus.SUCCESS, summary, Date.now() - step3Start, 3, ctx);

      // ===== Step 4: 内容增强 =====
      const step4Start = Date.now();
      const enrichment = await this.enrichmentAgent.run(ctx, classification, summary);
      await this.recordStep(runId, 'EnrichmentAgent', TaskStatus.SUCCESS, enrichment, Date.now() - step4Start, 4, ctx);

      // ===== Step 5: 推送计划 =====
      const step5Start = Date.now();
      const pushPlan = await this.pushPlannerAgent.run(ctx, hotspot, classification, summary, enrichment);
      await this.recordStep(runId, 'PushPlannerAgent', TaskStatus.SUCCESS, pushPlan, Date.now() - step5Start, 5, ctx);

      // 6. 更新运行记录状态
      const contentProcessing = this.buildContentProcessingOutput(summary, classification, enrichment);
      await this.prisma.agentRun.update({
        where: { id: runId },
        data: {
          status: TaskStatus.SUCCESS,
          outputSummary: JSON.stringify(contentProcessing),
          finishedAt: new Date(),
        },
      });

      // 7. 回写 News 记录（更新分类、摘要、热度等）
      await this.updateNewsFromResults(newsId, hotspot, classification, summary);

      this.logger.log(`智能处理完成: run_id=${runId}, news_id=${newsId}, hot=${hotspot.is_hot}`);

      return {
        run_id: runId,
        is_hot: true,
        hotspot,
        classification,
        summary,
        enrichment,
        push_plan: pushPlan,
        content_processing: contentProcessing,
      };
    } catch (error) {
      // 记录失败（使用 errorMessage 而非 error）
      await this.prisma.agentRun.update({
        where: { id: runId },
        data: {
          status: TaskStatus.FAILED,
          errorMessage: error instanceof Error ? error.message : String(error),
          finishedAt: new Date(),
        },
      });
      throw error;
    }
  }

  /**
   * 生成简报（聚合多条热点）
   * 对应 POST /agent/generate-digest
   */
  async generateDigest(options?: { limit?: number }): Promise<DigestOutput> {
    const limit = options?.limit || 10;

    // 获取最近的高分热点
    const hotTopics = await this.prisma.hotTopic.findMany({
      where: { status: 'ACTIVE' },
      orderBy: [{ score: 'desc' }, { id: 'desc' }],
      take: limit,
    });

    if (hotTopics.length === 0) {
      return this.digestAgent.run(
        await this.buildEmptyContext(),
        [],
      );
    }

    // 构建输入项
    const items: DigestItemInput[] = hotTopics.map((topic) => ({
      title: topic.title,
      summary: topic.summary || '',
      category: topic.category || '',
      score: topic.score,
    }));

    const ctx = await this.buildEmptyContext();
    return this.digestAgent.run(ctx, items);
  }

  // ===== 内部方法 =====

  /** 构建 Agent 执行上下文 */
  private async buildContext(news: {
    id?: number;
    title: string;
    source: string;
    category: string | null;
    hotScore: number;
    language: string;
    publishTime: Date | null;
    summary: string | null;
    content: string | null;
    tags?: string[] | null;
    status?: string;
    url?: string | null;
  }): Promise<AgentExecutionContext> {
    // 从 SystemConfig 读取 prompt 配置
    const configs = await this.prisma.systemConfig.findMany({
      where: { category: { in: ['agent', 'prompt'] }, isEnabled: true },
    });

    const promptBundle: Record<string, string> = {};
    for (const c of configs) {
      if (c.category === 'prompt') {
        promptBundle[`agent_${c.configKey}_prompt`] = c.configValue;
      }
    }

    // 从 DB 配置中读取 agent 相关参数，fallback 到默认值
    const hotConfig = configs.find(c => c.configKey === 'hot_threshold');
    const pushConfig = configs.find(c => c.configKey === 'push_channels');

    return {
      news: {
        id: news.id,
        title: news.title,
        source: news.source,
        category: news.category,
        hot_score: news.hotScore,
        language: news.language || 'en',
        publish_time: news.publishTime,
        summary: news.summary,
        content: news.content,
        tags: news.tags as string[] | undefined,
        status: news.status,
        url: news.url,
      },
      model_name: this.configService.get<string>('agent.defaultModelName', 'qwen3.5-plus'),
      prompt_version: this.configService.get<string>('agent.promptVersion', 'v1'),
      config: {
        hot_threshold: hotConfig ? parseInt(hotConfig.configValue, 10) : 35,
        push_channels: pushConfig ? pushConfig.configValue : 'webhook,email',
      },
      prompt_bundle: promptBundle,
      runtime: this.runtime.getRuntimeInfo(),
    };
  }

  /** 构建空上下文（用于不需要具体新闻的操作） */
  private async buildEmptyContext(): Promise<AgentExecutionContext> {
    const configs = await this.prisma.systemConfig.findMany({
      where: { category: { in: ['agent', 'prompt'] }, isEnabled: true },
    });
    const promptBundle: Record<string, string> = {};
    for (const c of configs) {
      if (c.category === 'prompt') {
        promptBundle[`agent_${c.configKey}_prompt`] = c.configValue;
      }
    }

    return {
      news: {
        title: '',
        source: '',
        category: '',
        hot_score: 0,
        language: 'zh',
        publish_time: null,
        summary: null,
        content: null,
      },
      model_name: this.configService.get<string>('agent.defaultModelName', 'qwen3.5-plus'),
      prompt_version: this.configService.get<string>('agent.promptVersion', 'v1'),
      config: {},
      prompt_bundle: promptBundle,
      runtime: this.runtime.getRuntimeInfo(),
    };
  }

  /**
   * 记录单个 Agent 步骤
   * 使用正确的 Prisma schema 字段名：stepCode, stepOrder, inputSummary, outputSummary, finishedAt 等
   */
  private async recordStep(
    runId: number,
    agentName: string,
    status: string,
    output: unknown,
    durationMs: number,
    stepOrder: number,
    ctx: AgentExecutionContext,
  ): Promise<void> {
    await this.prisma.agentRunStep.create({
      data: {
        runId,
        stepCode: agentName,
        agentName,
        stepOrder,
        status: status as any,
        modelName: ctx.model_name,
        promptVersion: ctx.prompt_version,
        inputSummary: '{}',
        outputSummary: JSON.stringify(output),
        durationMs,
        startedAt: new Date(Date.now() - durationMs),
        finishedAt: new Date(),
      },
    });
  }

  /** 构建非热点的返回结果 */
  private buildNonHotResult(runId: number, hotspot: HotspotOutput, ctx: AgentExecutionContext): OrchestratorResult {
    const emptyClassification: ClassificationOutput = {
      category: ctx.news.category || '未分类',
      tags: [],
      keywords: hotspot.keywords,
      topic_hint: '',
      hot_score: hotspot.score,
    };
    const emptySummary: SummaryOutput = {
      title: ctx.news.title,
      summary: ctx.news.summary || '',
      highlights: [],
      source_summary: ctx.news.summary || '',
    };
    const emptyEnrichment: EnrichmentOutput = {
      background: '',
      impact: '',
      technical_analysis: '',
      application_scenarios: [],
    };
    const emptyPushPlan: PushPlanOutput = {
      push_now: false,
      priority: 'LOW',
      push_type: 'SKIP',
      channels: [],
      planned_at: new Date().toISOString(),
      reason: `非热点内容（评分 ${hotspot.score}）`,
      title: ctx.news.title,
    };

    return {
      run_id: runId,
      is_hot: false,
      hotspot,
      classification: emptyClassification,
      summary: emptySummary,
      enrichment: emptyEnrichment,
      push_plan: emptyPushPlan,
      content_processing: this.buildContentProcessingOutput(emptySummary, emptyClassification, emptyEnrichment),
    };
  }

  /** 构建聚合的内容处理输出 */
  private buildContentProcessingOutput(
    summary: SummaryOutput,
    classification: ClassificationOutput,
    _enrichment: EnrichmentOutput,
  ): ContentProcessingOutput {
    return {
      title: summary.title,
      summary: summary.summary,
      highlights: summary.highlights,
      translated_title: summary.title, // AI 翻译由 AI 分支处理；fallback 直接复用
      translated_content: summary.summary,
      tags: classification.tags,
      script: `【${summary.title}】\n${summary.highlights.join('\n')}`,
    };
  }

  /** 将 Agent 处理结果回写到 News 表（使用合法的 NewsStatus 枚举值） */
  private async updateNewsFromResults(
    newsId: number,
    hotspot: HotspotOutput,
    classification: ClassificationOutput,
    summary: SummaryOutput,
  ): Promise<void> {
    await this.prisma.news.update({
      where: { id: newsId },
      data: {
        category: classification.category,
        tags: classification.tags,
        hotScore: hotspot.score,
        summary: summary.summary || undefined,
        status: NewsStatus.SCRIPT_READY,
      },
    });
  }
}
