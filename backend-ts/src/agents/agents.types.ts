/**
 * Agent 结构化输出类型定义
 * 对应 Python 端 structured_models.py 的 Pydantic 模型
 */

/** HotspotAgent 输出 */
export interface HotspotOutput {
  is_hot: boolean;
  score: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  trend: 'RISING' | 'WATCH' | 'STABLE';
  reason: string;
  keywords: string[];
}

/** ClassificationAgent 输出 */
export interface ClassificationOutput {
  category: string;
  tags: string[];
  keywords: string[];
  topic_hint: string;
  hot_score: number;
}

/** SummaryAgent 输出 */
export interface SummaryOutput {
  title: string;
  summary: string;
  highlights: string[];
  source_summary?: string;
}

/** ContentProcessing（智能处理）聚合输出 */
export interface ContentProcessingOutput {
  title: string;
  summary: string;
  highlights: string[];
  translated_title: string;
  translated_content: string;
  tags: string[];
  script: string;
}

/** EnrichmentAgent 输出 */
export interface EnrichmentOutput {
  background: string;
  impact: string;
  technical_analysis: string;
  application_scenarios: string[];
}

/** PushPlannerAgent 输出 */
export interface PushPlanOutput {
  push_now: boolean;
  priority: string;
  push_type: string;
  channels: string[];
  planned_at: string;
  reason: string;
  title: string;
}

/** DigestAgent 输出 */
export interface DigestOutput {
  title: string;
  summary: string;
  highlights: string[];
  topic_count: number;
}

/** Agent 执行上下文 — 对应 Python AgentExecutionContext */
export interface AgentExecutionContext {
  news: {
    id?: number;
    title: string;
    source: string;
    category: string | null;
    hot_score: number;
    language: string;
    publish_time: Date | null;
    summary: string | null;
    content: string | null;
    tags?: string[] | null;
    status?: string;
    url?: string | null;
  };
  model_name: string;
  prompt_version: string;
  config: Record<string, unknown>;
  prompt_bundle: Record<string, string>;
  /** 可选的 AgentScope 运行时实例（未配置时走规则降级） */
  runtime?: AgentScopeRuntime | null;
}

/** AgentScope 运行时接口 */
export interface AgentScopeRuntime {
  modelName: string;
  apiKey: string;
}

/** 单条热点摘要（输入给 DigestAgent） */
export interface DigestItemInput {
  title: string;
  summary: string;
  category: string;
  score: number;
}
