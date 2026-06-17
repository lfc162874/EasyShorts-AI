/**
 * ClassificationAgent - Content classification agent
 * Classifies news content, assigns tags and extracts keywords
 *
 * Pattern: AI-first rule-fallback
 */

import { Injectable, Logger } from '@nestjs/common';
import { z } from 'zod';

import { AgentScopeRuntimeService } from './agents.runtime';
import type {
  AgentExecutionContext,
  ClassificationOutput,
  HotspotOutput,
} from './agents.types';
import { extractKeywords, inferCategory } from './agents.common';

// ===== Zod Schema =====

export const ClassificationSchema = z.object({
  category: z.string(),
  tags: z.array(z.string()).default([]),
  keywords: z.array(z.string()).default([]),
  topic_hint: z.string(),
  hot_score: z.number(),
});

@Injectable()
export class ClassificationAgent {
  private readonly logger = new Logger(ClassificationAgent.name);

  constructor(private readonly runtime: AgentScopeRuntimeService) {}

  private buildUserPrompt(ctx: AgentExecutionContext, hotspotResult: HotspotOutput): string {
    const news = ctx.news;
    return [
      'Classify this AI news with category, tags and keywords. Output structured JSON only.',
      `Title: ${news.title}`,
      `Source: ${news.source}`,
      `Category: ${news.category || 'N/A'}`,
      `Hot Score: ${hotspotResult.score}`,
      `Is Hot: ${hotspotResult.is_hot}`,
      `Summary: ${news.summary || 'N/A'}`,
      'Content:',
      news.content || '',
    ].join('\n');
  }

  async run(
    ctx: AgentExecutionContext,
    hotspotResult: HotspotOutput,
  ): Promise<ClassificationOutput> {
    // Try AI
    const aiResult = await this.runtime.callStructured<ClassificationOutput>({
      agentName: 'ClassificationAgent',
      systemPrompt: ctx.prompt_bundle.agent_classification_prompt || '',
      userPrompt: this.buildUserPrompt(ctx, hotspotResult),
      schema: ClassificationSchema,
    });

    if (aiResult) {
      this.logger.debug(`ClassificationAgent AI result: category=${aiResult.category}`);
      return aiResult;
    }

    return this.fallback(ctx, hotspotResult);
  }

  private fallback(
    ctx: AgentExecutionContext,
    hotspotResult: HotspotOutput,
  ): ClassificationOutput {
    const news = ctx.news;
    const text = `${news.title} ${news.content || ''}`;
    const category = inferCategory(news.title, news.content || '', news.category || undefined);
    const keywordCandidates = extractKeywords(text);

    // Build tags (dedup merge)
    const tags: string[] = [];
    for (const candidate of [
      category,
      news.source,
      ...(news.tags || []),
      ...keywordCandidates,
    ]) {
      if (candidate && !tags.includes(candidate)) {
        tags.push(candidate);
        if (tags.length >= 5) break;
      }
    }

    return {
      category,
      tags: tags.slice(0, 5),
      keywords: keywordCandidates.slice(0, 6),
      topic_hint: category,
      hot_score: hotspotResult.score,
    };
  }
}
