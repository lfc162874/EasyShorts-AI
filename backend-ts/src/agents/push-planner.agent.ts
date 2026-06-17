/**
 * PushPlannerAgent - Push planning agent
 * Outputs push decisions: whether to push, priority, channels, timing
 *
 * Pattern: AI-first rule-fallback
 */

import { Injectable, Logger } from '@nestjs/common';
import { z } from 'zod';

import { AgentScopeRuntimeService } from './agents.runtime';
import type {
  AgentExecutionContext,
  ClassificationOutput,
  EnrichmentOutput,
  HotspotOutput,
  PushPlanOutput,
  SummaryOutput,
} from './agents.types';
import {
  buildModelLabel,
  inferPriority,
  mergeChannels,
  recommendChannels,
} from './agents.common';

// ===== Zod Schema =====

export const PushPlanSchema = z.object({
  push_now: z.boolean(),
  priority: z.string(),
  push_type: z.string(),
  channels: z.array(z.string()).default([]),
  planned_at: z.string(),
  reason: z.string(),
  title: z.string(),
});

@Injectable()
export class PushPlannerAgent {
  private readonly logger = new Logger(PushPlannerAgent.name);

  constructor(private readonly runtime: AgentScopeRuntimeService) {}

  private buildUserPrompt(
    ctx: AgentExecutionContext,
    hotspotResult: HotspotOutput,
    classificationResult: ClassificationOutput,
    summaryResult: SummaryOutput,
    enrichmentResult: EnrichmentOutput,
  ): string {
    return [
      'Output a push decision based on the following analysis. Output structured JSON only.',
      `News Title: ${summaryResult.title}`,
      `Summary: ${summaryResult.summary}`,
      `Category: ${classificationResult.category}`,
      `Tags: ${classificationResult.tags.join(', ')}`,
      `Hot Score: ${hotspotResult.score}`,
      `Priority: ${hotspotResult.priority}`,
      `Trend: ${hotspotResult.trend}`,
      `Impact: ${enrichmentResult.impact.slice(0, 200)}`,
      `Model: ${buildModelLabel(ctx.model_name)}`,
      `Channels: ${(ctx.config.push_channels as string[]) || 'webhook,email'}`,
    ].join('\n');
  }

  async run(
    ctx: AgentExecutionContext,
    hotspotResult: HotspotOutput,
    classificationResult: ClassificationOutput,
    summaryResult: SummaryOutput,
    enrichmentResult: EnrichmentOutput,
  ): Promise<PushPlanOutput> {
    const aiResult = await this.runtime.callStructured<PushPlanOutput>({
      agentName: 'PushPlannerAgent',
      systemPrompt: ctx.prompt_bundle.agent_push_planner_prompt || '',
      userPrompt: this.buildUserPrompt(
        ctx,
        hotspotResult,
        classificationResult,
        summaryResult,
        enrichmentResult,
      ),
      schema: PushPlanSchema,
    });

    if (aiResult) {
      this.logger.debug(`PushPlannerAgent AI result: push_now=${aiResult.push_now}, priority=${aiResult.priority}`);
      return aiResult;
    }

    return this.fallback(hotspotResult, classificationResult, summaryResult, ctx);
  }

  private fallback(
    hotspotResult: HotspotOutput,
    classificationResult: ClassificationOutput,
    summaryResult: SummaryOutput,
    ctx: AgentExecutionContext,
  ): PushPlanOutput {
    const priority = hotspotResult.priority;
    const channels = recommendChannels(priority);
    const configuredChannels = ctx.config.push_channels as string[] | undefined;

    const now = new Date();
    const pushNow = priority === 'HIGH';
    const plannedAt = pushNow
      ? now.toISOString()
      : new Date(now.getTime() + 6 * 60 * 60 * 1000).toISOString();

    return {
      push_now: pushNow,
      priority,
      push_type: 'HIGHLIGHT',
      channels: mergeChannels(channels, configuredChannels),
      planned_at: plannedAt,
      reason:
        priority === 'HIGH'
          ? `High hot content (${hotspotResult.score}), recommend immediate push`
          : `Medium hot content (${hotspotResult.score}), scheduled for later`,
      title: summaryResult.title,
    };
  }
}
