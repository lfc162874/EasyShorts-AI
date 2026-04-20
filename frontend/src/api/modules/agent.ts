import http from "@/api/http";
import type { ApiResponse, PagedData } from "@/types/common";
import type {
  AgentConfigItem,
  AgentConfigUpdateForm,
  AgentModelItem,
  AgentRunActionPayload,
  AgentRunDetailItem,
  AgentRunItem,
  AgentRunQuery,
  HotTopicDetailItem,
  HotTopicItem,
  HotTopicQuery,
  PushPlanDetailItem,
  PushPlanItem,
  PushPlanQuery,
} from "@/types/agent";
import type { TaskJobItem } from "@/types/system";

export const getAgentConfig = (): Promise<ApiResponse<AgentConfigItem>> =>
  http.get("/agent/config");

export const saveAgentConfig = (
  payload: AgentConfigUpdateForm,
): Promise<ApiResponse<AgentConfigItem>> => http.put("/agent/config", payload);

export const listAgentModels = (): Promise<ApiResponse<AgentModelItem[]>> =>
  http.get("/agent/models");

export const triggerAgentRun = (
  newsId: number,
  payload?: AgentRunActionPayload,
): Promise<ApiResponse<TaskJobItem>> =>
  http.post(`/agent/runs/news/${newsId}`, payload ?? {});

export const listAgentRuns = (
  query?: AgentRunQuery,
): Promise<ApiResponse<PagedData<AgentRunItem>>> => http.get("/agent/runs", { params: query });

export const getAgentRun = (
  runId: number,
): Promise<ApiResponse<AgentRunDetailItem>> => http.get(`/agent/runs/${runId}`);

export const retryAgentRun = (
  runId: number,
  payload?: AgentRunActionPayload,
): Promise<ApiResponse<TaskJobItem>> =>
  http.post(`/agent/runs/${runId}/retry`, payload ?? {});

export const retryAgentRunStep = (
  runId: number,
  stepId: number,
  payload?: AgentRunActionPayload,
): Promise<ApiResponse<TaskJobItem>> =>
  http.post(`/agent/runs/${runId}/steps/${stepId}/retry`, payload ?? {});

export const listHotTopics = (
  query?: HotTopicQuery,
): Promise<ApiResponse<PagedData<HotTopicItem>>> =>
  http.get("/agent/hot-topics", { params: query });

export const getHotTopic = (
  topicId: number,
): Promise<ApiResponse<HotTopicDetailItem>> => http.get(`/agent/hot-topics/${topicId}`);

export const listPushPlans = (
  query?: PushPlanQuery,
): Promise<ApiResponse<PagedData<PushPlanItem>>> =>
  http.get("/agent/push-plans", { params: query });

export const getPushPlan = (
  planId: number,
): Promise<ApiResponse<PushPlanDetailItem>> => http.get(`/agent/push-plans/${planId}`);

export const executePushPlan = (
  planId: number,
): Promise<ApiResponse<PushPlanItem>> => http.post(`/agent/push-plans/${planId}/execute`);
