import type { PaginationQuery } from "@/types/common";

export type AgentRunStatus =
  | "PENDING"
  | "RUNNING"
  | "SUCCESS"
  | "FAILED"
  | "RETRYING"
  | "CANCELLED";

export type AgentRunType = "single_article" | "digest" | "push_plan";

export type AgentBizType = "news" | "hot_topic" | "digest";

export type HotTopicStatus = "ACTIVE" | "IGNORED" | "ARCHIVED";

export type PushPlanStatus = "PENDING" | "SCHEDULED" | "EXECUTED" | "FAILED" | "CANCELLED";

export type PushPlanType = "IMMEDIATE" | "DIGEST" | "SCHEDULED";

export type PriorityLevel = "HIGH" | "MEDIUM" | "LOW";

export type TrendLevel = "RISING" | "WATCH" | "STABLE";

export interface AgentConfigUpdateForm {
  default_model_name?: string | null;
  supported_models?: string[] | null;
  default_provider?: string | null;
  prompt_version?: string | null;
  push_channels?: string[] | null;
}

export interface AgentRunActionPayload {
  model_name?: string | null;
  force?: boolean;
}

export interface AgentModelItem {
  value: string;
  label: string;
  is_default: boolean;
}

export interface AgentModelResponse {
  default_model_name: string;
  supported_models: string[];
  default_provider: string;
  prompt_version: string;
  push_channels: string[];
  hot_threshold: number;
  options: AgentModelItem[];
}

export interface AgentConfigItem {
  default_model_name: string;
  supported_models: string[];
  default_provider: string;
  prompt_version: string;
  push_channels: string[];
  hot_threshold: number;
  prompts: Record<string, string>;
}

export interface AgentRunQuery extends PaginationQuery {
  status?: AgentRunStatus;
  run_type?: AgentRunType;
  biz_type?: AgentBizType;
  model_name?: string;
}

export interface AgentRunStepItem {
  id: number;
  run_id: number;
  step_code: string;
  agent_name: string;
  step_order: number;
  status: AgentRunStatus;
  model_name: string;
  prompt_version: string;
  input_summary: string | null;
  output_summary: string | null;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  created_at: string;
  updated_at: string;
}

export interface AgentRunArtifactItem {
  id: number;
  run_id: number;
  step_id: number | null;
  artifact_type: string;
  artifact_key: string;
  content_json: Record<string, unknown> | null;
  content_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentRunItem {
  id: number;
  parent_run_id: number | null;
  task_job_id: number | null;
  run_type: AgentRunType;
  biz_type: AgentBizType;
  biz_id: string;
  status: AgentRunStatus;
  current_step: string | null;
  model_name: string;
  prompt_version: string;
  input_summary: string | null;
  output_summary: string | null;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  triggered_by: number | null;
  request_id: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentRunDetailItem extends AgentRunItem {
  steps: AgentRunStepItem[];
  artifacts: AgentRunArtifactItem[];
}

export interface HotTopicNewsItem {
  id: number;
  news_id: number;
  source_id: number | null;
  source_name: string | null;
  title: string;
  url: string;
  weight: number;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface HotTopicItem {
  id: number;
  topic_key: string;
  title: string;
  summary: string | null;
  category: string | null;
  tags: string[] | null;
  score: number;
  priority: PriorityLevel;
  reason: string | null;
  trend: TrendLevel | string | null;
  status: HotTopicStatus;
  model_name: string;
  prompt_version: string;
  news_count: number;
  source_count: number;
  primary_news_id: number | null;
  extra: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface HotTopicDetailItem extends HotTopicItem {
  items: HotTopicNewsItem[];
}

export interface HotTopicQuery extends PaginationQuery {
  status?: HotTopicStatus;
  category?: string;
}

export interface PushPlanItem {
  id: number;
  biz_type: AgentBizType;
  biz_id: string;
  run_id: number | null;
  topic_id: number | null;
  push_now: boolean;
  priority: PriorityLevel;
  push_type: PushPlanType;
  channels: string[] | null;
  planned_at: string | null;
  status: PushPlanStatus;
  reason: string | null;
  model_name: string;
  prompt_version: string;
  executed_at: string | null;
  extra: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface PushPlanDetailItem extends PushPlanItem {
  topic: HotTopicItem | null;
  run: AgentRunItem | null;
}

export interface PushPlanQuery extends PaginationQuery {
  status?: PushPlanStatus;
  biz_type?: AgentBizType;
}
