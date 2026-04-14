import http, { upload } from "@/api/http";
import type { ApiResponse, PagedData, PaginationQuery } from "@/types/common";
import type {
  ConfigUpsertForm,
  ErrorLogItem,
  FileAssetItem,
  MenuNode,
  MenuUpsertForm,
  OperationLogItem,
  PlatformAccountItem,
  PlatformAccountUpsertForm,
  RoleItem,
  RoleUpsertForm,
  SystemConfigItem,
  TaskJobItem,
  UserProfile,
  UserUpsertForm,
} from "@/types/system";

export const listUsers = (
  query: PaginationQuery,
): Promise<ApiResponse<PagedData<UserProfile>>> =>
  http.get("/system/users", { params: query });

export const getUser = (userId: number): Promise<ApiResponse<UserProfile>> =>
  http.get(`/system/users/${userId}`);

export const saveUser = (payload: UserUpsertForm): Promise<ApiResponse<UserProfile>> =>
  payload.id
    ? http.put(`/system/users/${payload.id}`, payload)
    : http.post("/system/users", payload);

export const listRoles = (
  query?: PaginationQuery,
): Promise<ApiResponse<{ items: RoleItem[]; total: number }>> =>
  http.get("/system/roles", { params: query });

export const getRole = (roleId: number): Promise<ApiResponse<RoleItem>> =>
  http.get(`/system/roles/${roleId}`);

export const saveRole = (payload: RoleUpsertForm): Promise<ApiResponse<RoleItem>> =>
  payload.id
    ? http.put(`/system/roles/${payload.id}`, payload)
    : http.post("/system/roles", payload);

export const assignRoleMenus = (
  roleId: number,
  ids: number[],
): Promise<ApiResponse<RoleItem>> =>
  http.put(`/system/roles/${roleId}/menus`, { ids });

export const listMenus = (): Promise<ApiResponse<{ items: MenuNode[] }>> =>
  http.get("/system/menus");

export const saveMenu = (payload: MenuUpsertForm): Promise<ApiResponse<MenuNode>> =>
  payload.id
    ? http.put(`/system/menus/${payload.id}`, payload)
    : http.post("/system/menus", payload);

export const listConfigs = (
  query?: PaginationQuery,
): Promise<ApiResponse<{ items: SystemConfigItem[]; total: number }>> =>
  http.get("/system/configs", { params: query });

export const saveConfig = (
  payload: ConfigUpsertForm,
): Promise<ApiResponse<SystemConfigItem>> =>
  payload.id
    ? http.put(`/system/configs/${payload.id}`, payload)
    : http.post("/system/configs", payload);

export const listPlatformAccounts = (
  query?: PaginationQuery,
): Promise<ApiResponse<{ items: PlatformAccountItem[]; total: number }>> =>
  http.get("/system/platform-accounts", { params: query });

export const savePlatformAccount = (
  payload: PlatformAccountUpsertForm,
): Promise<ApiResponse<PlatformAccountItem>> =>
  payload.id
    ? http.put(`/system/platform-accounts/${payload.id}`, payload)
    : http.post("/system/platform-accounts", payload);

export const listOperationLogs = (
  query: PaginationQuery,
): Promise<ApiResponse<PagedData<OperationLogItem>>> =>
  http.get("/system/logs/operations", { params: query });

export const listErrorLogs = (
  query: PaginationQuery,
): Promise<ApiResponse<PagedData<ErrorLogItem>>> =>
  http.get("/system/logs/errors", { params: query });

export const listTasks = (
  query: PaginationQuery,
): Promise<ApiResponse<PagedData<TaskJobItem>>> =>
  http.get("/system/tasks", { params: query });

export const createDemoTask = (
  payload: { payload: { message: string } },
): Promise<ApiResponse<TaskJobItem>> => http.post("/system/tasks/demo", payload);

export const uploadFile = (
  file: File,
): Promise<ApiResponse<FileAssetItem>> => {
  const formData = new FormData();
  formData.append("file", file);
  return upload("/uploads/files", formData);
};
