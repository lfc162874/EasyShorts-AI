/**
 * DigestAgent - Digest generation agent
 * Aggregates multiple hot topics into an AI digest
 *
 * Pattern: AI-first rule-fallback
 */

import { Injectable, Logger } from '@nestjs/common';
import { z } from 'zod';

import { AgentScopeRuntimeService } from './agents.runtime';
import type { AgentExecutionContext, DigestOutput, DigestItemInput } from './agents.types';

// ===== Zod Schema =====

export const DigestSchema = z.object({
  title: z.string(),
  summary: z.string(),
  highlights: z.array(z.string()).default([]),
  topic_count: z.number(),
});

@Injectable()
export class DigestAgent {
  private readonly logger = new Logger(DigestAgent.name);

  constructor(private readonly runtime: AgentScopeRuntimeService) {}

  private buildUserPrompt(
    ctx: AgentExecutionContext,
    items: DigestItemInput[],
  ): string {
    const itemTexts = items.map((item, idx) => [
      `--- Topic ${idx + 1} ---`,
      `Title: ${item.title}`,
      `Category: ${item.category}`,
      `Score: ${item.score}`,
      `Summary: ${item.summary}`,
    ].join('\n'));

    return [
      'Generate an AI hot topics digest based on the following content. Output structured JSON only.',
      ...itemTexts,
    ].join('\n');
  }

  async run(
    ctx: AgentExecutionContext,
    items: DigestItemInput[],
  ): Promise<DigestOutput> {
    if (items.length === 0) {
      return this.emptyDigest();
    }

    const aiResult = await this.runtime.callStructured<DigestOutput>({
      agentName: 'DigestAgent',
      systemPrompt: ctx.prompt_bundle.agent_digest_prompt || '',
      userPrompt: this.buildUserPrompt(ctx, items),
      schema: DigestSchema,
    });

    if (aiResult) {
      this.logger.debug(`DigestAgent AI result: title=${aiResult.title}`);
      return aiResult;
    }

    return this.fallback(items);
  }

  private fallback(items: DigestItemInput[]): DigestOutput {
    const topItems = items.slice(0, 5);
    const highlights = topItems.map(
      (item) => `[${item.category}] ${item.title} (score: ${item.score})`,
    );

    // Category statistics
    const categoryCount = new Map<string, number>();
    for (const item of items) {
      categoryCount.set(item.category, (categoryCount.get(item.category) || 0) + 1);
    }
    const categories = [...categoryCount.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([cat]) => cat)
      .slice(0, 3);

    return {
      title: `AI Hot Digest - ${new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })}`,
      summary: `This digest covers ${items.length} hot topics including ${categories.join(', ')} and more.`,
      highlights,
      topic_count: items.length,
    };
  }

  private emptyDigest(): DigestOutput {
    return {
      title: 'AI Hot Digest',
      summary: 'No hot topics available.',
      highlights: ['No hot topic data to summarize.'],
      topic_count: 0,
    };
  }
}
