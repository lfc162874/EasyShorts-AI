/**
 * SummaryAgent - Summary generation agent
 * Generates optimized title, concise summary and key highlights
 *
 * Pattern: AI-first rule-fallback
 */

import { Injectable, Logger } from '@nestjs/common';
import { z } from 'zod';

import { AgentScopeRuntimeService } from './agents.runtime';
import type { AgentExecutionContext, ClassificationOutput, SummaryOutput } from './agents.types';
import {
  buildHighlights,
  extractKeywords,
  normalizeWhitespace,
  summarizeText,
} from './agents.common';

// ===== Zod Schema =====

export const SummarySchema = z.object({
  title: z.string(),
  summary: z.string(),
  highlights: z.array(z.string()).default([]),
  source_summary: z.string().default(''),
});

@Injectable()
export class SummaryAgent {
  private readonly logger = new Logger(SummaryAgent.name);

  constructor(private readonly runtime: AgentScopeRuntimeService) {}

  private buildUserPrompt(
    ctx: AgentExecutionContext,
    classificationResult: ClassificationOutput,
  ): string {
    const news = ctx.news;
    return [
      'Generate an optimized title, one-line summary and key highlights for this AI news. Output structured JSON only.',
      `Title: ${news.title}`,
      `Source: ${news.source}`,
      `Category: ${classificationResult.category}`,
      `Tags: ${classificationResult.tags.join(', ')}`,
      `Keywords: ${classificationResult.keywords.join(', ')}`,
      `Language: ${news.language}`,
      `Original Summary: ${news.summary || 'N/A'}`,
      'Content:',
      news.content || '',
    ].join('\n');
  }

  async run(
    ctx: AgentExecutionContext,
    classificationResult: ClassificationOutput,
  ): Promise<SummaryOutput> {
    const aiResult = await this.runtime.callStructured<SummaryOutput>({
      agentName: 'SummaryAgent',
      systemPrompt: ctx.prompt_bundle.agent_summary_prompt || '',
      userPrompt: this.buildUserPrompt(ctx, classificationResult),
      schema: SummarySchema,
    });

    if (aiResult) {
      this.logger.debug(`SummaryAgent AI result: title=${aiResult.title.slice(0, 50)}`);
      return aiResult;
    }

    return this.fallback(ctx, classificationResult);
  }

  private fallback(
    ctx: AgentExecutionContext,
    classificationResult: ClassificationOutput,
  ): SummaryOutput {
    const news = ctx.news;
    const content = news.content || news.summary || '';
    const keywords = extractKeywords(`${news.title} ${content}`);

    return {
      title: news.title.length > 120 ? news.title.slice(0, 117) + '...' : news.title,
      summary: summarizeText(content),
      highlights: buildHighlights(content || '', keywords),
      source_summary: normalizeWhitespace(news.summary) || '',
    };
  }
}
