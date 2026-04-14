import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { ElMessage } from "element-plus";

import type { ApiResponse } from "@/types/common";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/easy-shorts",
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("easyshorts-access-token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiResponse<unknown>;
    if (payload?.code !== 0) {
      if (payload?.code === 40100) {
        window.localStorage.removeItem("easyshorts-access-token");
        window.localStorage.removeItem("easyshorts-user");
      }
      ElMessage.error(payload?.message ?? "请求失败");
      return Promise.reject(payload);
    }
    return response;
  },
  (error: AxiosError<{ message?: string }>) => {
    const message = error.response?.data?.message ?? "网络异常，请稍后重试";
    ElMessage.error(message);
    return Promise.reject(error);
  },
);

const request = async <T>(
  config: AxiosRequestConfig,
): Promise<ApiResponse<T>> =>
  (await http.request<ApiResponse<T>>(config)).data;

const get = async <T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T>> => request<T>({ ...config, method: "GET", url });

const post = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T>> =>
  request<T>({ ...config, method: "POST", url, data });

const put = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T>> =>
  request<T>({ ...config, method: "PUT", url, data });

const del = async <T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T>> => request<T>({ ...config, method: "DELETE", url });

export const upload = async <T>(
  url: string,
  formData: FormData,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T>> =>
  request<T>({
    ...config,
    method: "POST",
    url,
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
      ...(config?.headers ?? {}),
    },
  });

const httpClient = {
  request,
  get,
  post,
  put,
  delete: del,
};

export default httpClient;
