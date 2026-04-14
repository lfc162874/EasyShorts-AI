import http from "@/api/http";
import type { ApiResponse, PagedData, PaginationQuery } from "@/types/common";
import type {
  NewsDetailItem,
  NewsFetchRecordItem,
  NewsFetchRecordQuery,
  NewsGenerateForm,
  NewsItem,
  NewsQuery,
  NewsSourceItem,
  NewsSourceQuery,
  NewsSourceUpsertForm,
} from "@/types/news";
import type { TaskJobItem } from "@/types/system";

export const listNewsSources = (
  query?: NewsSourceQuery,
): Promise<ApiResponse<PagedData<NewsSourceItem>>> =>
  http.get("/news/sources", { params: query });

export const getNewsSource = (
  sourceId: number,
): Promise<ApiResponse<NewsSourceItem>> => http.get(`/news/sources/${sourceId}`);

export const saveNewsSource = (
  payload: NewsSourceUpsertForm,
): Promise<ApiResponse<NewsSourceItem>> => {
  if (payload.id) {
    const { id: _id, source_key: _sourceKey, ...updatePayload } = payload;
    return http.put(`/news/sources/${payload.id}`, updatePayload);
  }

  return http.post("/news/sources", payload);
};

export const syncNewsSource = (
  sourceId: number,
): Promise<ApiResponse<TaskJobItem>> =>
  http.post(`/news/sources/${sourceId}/sync`);

export const listNews = (
  query?: NewsQuery,
): Promise<ApiResponse<PagedData<NewsItem>>> => http.get("/news", { params: query });

export const getNews = (newsId: number): Promise<ApiResponse<NewsDetailItem>> =>
  http.get(`/news/${newsId}`);

export const generateNews = (
  newsId: number,
  payload?: NewsGenerateForm,
): Promise<ApiResponse<TaskJobItem>> =>
  http.post(`/news/${newsId}/generate`, payload ?? {});

export const listNewsFetchRecords = (
  query?: NewsFetchRecordQuery,
): Promise<ApiResponse<PagedData<NewsFetchRecordItem>>> =>
  http.get("/news/records", { params: query });

export const getNewsFetchRecord = (
  recordId: number,
): Promise<ApiResponse<NewsFetchRecordItem>> =>
  http.get(`/news/records/${recordId}`);
