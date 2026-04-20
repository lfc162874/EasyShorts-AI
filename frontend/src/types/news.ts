import type { PaginationQuery } from "@/types/common";

export interface NewsSourceExtraConfig {
  weight?: number;
  mode?: "list" | "single";
  article_urls?: string[];
  urls?: string[];
  max_items?: number;
  link_patterns?: string[];
  exclude_link_patterns?: string[];
  items?: Array<Record<string, unknown>>;
  entries?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export interface NewsSourceItem {
  id: number;
  source_key: string;
  name: string;
  source_type: "RSS" | "ATOM" | "WEB" | "MANUAL";
  url: string;
  category: string | null;
  language: string;
  fetch_interval_minutes: number;
  is_enabled: boolean;
  last_fetched_at: string | null;
  last_success_at: string | null;
  last_error_message: string | null;
  extra: NewsSourceExtraConfig | null;
  created_at: string;
  updated_at: string;
}

export interface NewsSourceUpsertForm {
  id?: number;
  source_key: string;
  name: string;
  source_type: "RSS" | "ATOM" | "WEB" | "MANUAL";
  url: string;
  category?: string | null;
  language: string;
  fetch_interval_minutes: number;
  is_enabled: boolean;
  extra: NewsSourceExtraConfig | null;
}

export interface NewsSourceQuery extends PaginationQuery {
  source_type?: "RSS" | "ATOM" | "WEB" | "MANUAL";
  is_enabled?: boolean;
}

export interface NewsItem {
  id: number;
  title: string;
  content: string | null;
  source: string;
  source_id: number | null;
  source_url: string | null;
  url: string;
  publish_time: string | null;
  status: "NEW" | "DEDUPED" | "FILTERED" | "REJECTED" | "SCRIPT_READY" | "ARCHIVED";
  dedup_hash: string | null;
  category: string | null;
  hot_score: number;
  language: string;
  summary: string | null;
  translated_title: string | null;
  translated_content: string | null;
  script: string | null;
  tags: string[] | null;
  filter_reason: string | null;
  raw_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface NewsDetailItem extends NewsItem {
  source_detail: NewsSourceItem | null;
  fetch_records: NewsFetchRecordItem[];
}

export interface NewsQuery extends PaginationQuery {
  status?: NewsItem["status"];
  source_id?: number;
  category?: string;
}

export interface NewsGenerateForm {
  style: string;
  regenerate: boolean;
}

export interface NewsFetchRecordItem {
  id: number;
  source_id: number;
  source_name: string | null;
  task_job_id: number | null;
  request_id: string | null;
  fetch_mode: "MANUAL" | "SCHEDULED";
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "RETRYING" | "CANCELLED";
  total_count: number;
  new_count: number;
  duplicate_count: number;
  filtered_count: number;
  error_count: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  extra: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface NewsFetchRecordQuery extends PaginationQuery {
  source_id?: number;
  status?: NewsFetchRecordItem["status"];
}
