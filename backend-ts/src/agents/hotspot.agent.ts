/**
 * HotspotAgent - Hotspot judgment agent
 * Determines whether input news is a high-value AI hotspot
 *
 * Pattern: AI-first rule-fallback
 */

import { Injectable, Logger } from '@nestjs/common';
import { z } from 'zod';

import { AgentScopeRuntimeService } from './agents.runtime';
import type { AgentExecutionContext, HotspotOutput } from './agents.types';
import {
  HOT_KEYWORDS,
  extractKeywords,
  inferPriority,
  inferTrend,
  normalizeWhitespace,
} from './agents.common';

// ===== Zod Structured Output Schema =====

export const HotspotSchema = z.object({
  is_hot: z.boolean(),
  score: z.number().min(0).max(100),
  priority: z.enum(['HIGH', 'MEDIUM', 'LOW']),
  trend: z.enum(['RISING', 'WATCH', 'STABLE']),
  reason: z.string(),
  keywords: z.array(z.string()).default([]),
});

@Injectable()
export class HotspotAgent {
  private readonly logger = new Logger(HotspotAgent.name);

  constructor(private readonly runtime: AgentScopeRuntimeService) {}

  /** Build user prompt */
  private buildUserPrompt(ctx: AgentExecutionContext): string {
    const news = ctx.news;
    return [
      'Determine whether this AI news is worth processing as a hotspot. Output structured JSON only.',
      `Title: ${news.title}`,
      `Source: ${news.source}`,
      `Category: ${news.category || 'N/A'}`,
      `Hot Score: ${news.hot_score}`,
      `Language: ${news.language}`,
      `Published: ${news.publish_time?.toISOString() || 'unknown'}`,
      `Summary: ${news.summary || 'N/A'}`,
      'Content:',
      news.content || '',
    ].join('\n');
  }

  /**
   * Execute hotspot judgment
   * Returns HotspotOutput, never throws (fallback guaranteed)
   */
  async run(ctx: AgentExecutionContext): Promise<HotspotOutput> {
    // Try AI call first
    const aiResult = await this.runtime.callStructured<HotspotOutput>({
      agentName: 'HotspotAgent',
      systemPrompt: ctx.prompt_bundle.agent_hotspot_prompt || '',
      userPrompt: this.buildUserPrompt(ctx),
      schema: HotspotSchema,
    });

    if (aiResult) {
      this.logger.debug(`HotspotAgent AI result: is_hot=${aiResult.is_hot}, score=${aiResult.score}`);
      return aiResult;
    }

    // Rule-based fallback
    return this.fallback(ctx);
  }

  /** Rule fallback logic */
  private fallback(ctx: AgentExecutionContext): HotspotOutput {
    const news = ctx.news;
    const text = `${news.title} ${news.content || ''}`.toLowerCase();
    const keywords = extractKeywords(text);
    let hotScore = news.hot_score || 0;

    // Hot keyword bonus
    if (HOT_KEYWORDS.some((kw) => text.includes(kw))) {
      hotScore += 8;
    }
    // Well-known source bonus
    if (
      news.source &&
      ['openai', 'anthropic', 'deepseek', 'qwen', 'modelscope'].some((marker) =>
        news.source!.toLowerCase().includes(marker),
      )
    ) {
      hotScore += 5;
    }

    hotScore = Math.min(hotScore, 100);
    const threshold = (ctx.config.hot_threshold as number) ?? 35;
    const isHot =
      hotScore >= threshold ||
      news.status === 'FILTERED' ||
      news.status === 'SCRIPT_READY';

    const reasonParts: string[] = [`Hot score ${hotScore}`, `Source: ${news.source}`];
    if (keywords.length > 0) {
      reasonParts.push(`Keywords: ${keywords.slice(0, 3).join(', ')}`);
    } else {
      reasonParts.push('No significant keywords matched');
    }
    if (news.summary) {
      reasonParts.push(`Summary: ${normalizeWhitespace(news.summary).slice(0, 60)}`);
    }

    return {
      is_hot: isHot,
      score: hotScore,
      priority: inferPriority(hotScore),
      trend: inferTrend(hotScore, news.title, news.content || ''),
      reason: reasonParts.join('; '),
      keywords: keywords.slice(0, 5),
    };
  }
}
