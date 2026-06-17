/**
 * EnrichmentAgent - Content enrichment agent
 * Adds background, industry impact, technical analysis and application scenarios
 *
 * Pattern: AI-first rule-fallback
 */

import { Injectable, Logger } from '@nestjs/common';
import { z } from 'zod';

import { AgentScopeRuntimeService } from './agents.runtime';
import type { AgentExecutionContext, ClassificationOutput, EnrichmentOutput } from './agents.types';
import {
  buildApplicationScenarios,
  buildBackground,
  buildImpact,
  buildTechnicalAnalysis,
} from './agents.common';

// ===== Zod Schema =====

export const EnrichmentSchema = z.object({
  background: z.string(),
  impact: z.string(),
  technical_analysis: z.string(),
  application_scenarios: z.array(z.string()).default([]),
});

@Injectable()
export class EnrichmentAgent {
  private readonly logger = new Logger(EnrichmentAgent.name);

  constructor(private readonly runtime: AgentScopeRuntimeService) {}

  private buildUserPrompt(
    ctx: AgentExecutionContext,
    classificationResult: ClassificationOutput,
    summaryResult: { title: string; summary: string },
  ): string {
    const news = ctx.news;
    return [
      'Add background, impact, technical analysis and application scenarios for this AI news. Output structured JSON only.',
      `Title: ${summaryResult.title}`,
      `Summary: ${summaryResult.summary}`,
      `Category: ${classificationResult.category}`,
      `Tags: ${classificationResult.tags.join(', ')}`,
      `Keywords: ${classificationResult.keywords.join(', ')}`,
      `Source: ${news.source}`,
      `Original Title: ${news.title}`,
      'Content (excerpt):',
      (news.content || news.summary || '').slice(0, 2000),
    ].join('\n');
  }

  async run(
    ctx: AgentExecutionContext,
    classificationResult: ClassificationOutput,
    summaryResult: { title: string; summary: string },
  ): Promise<EnrichmentOutput> {
    const aiResult = await this.runtime.callStructured<EnrichmentOutput>({
      agentName: 'EnrichmentAgent',
      systemPrompt: ctx.prompt_bundle.agent_enrichment_prompt || '',
      userPrompt: this.buildUserPrompt(ctx, classificationResult, summaryResult),
      schema: EnrichmentSchema,
    });

    if (aiResult) {
      this.logger.debug('EnrichmentAgent AI result complete');
      return aiResult;
    }

    return this.fallback(classificationResult, summaryResult);
  }

  private fallback(
    classificationResult: ClassificationOutput,
    summaryResult: { title: string; summary: string },
  ): EnrichmentOutput {
    const keywords = classificationResult.keywords;
    return {
      background: buildBackground(classificationResult.category, summaryResult.title, keywords),
      impact: buildImpact(classificationResult.category, classificationResult.hot_score || 60, keywords),
      technical_analysis: buildTechnicalAnalysis(classificationResult.category, keywords),
      application_scenarios: buildApplicationScenarios(classificationResult.category, keywords),
    };
  }
}
