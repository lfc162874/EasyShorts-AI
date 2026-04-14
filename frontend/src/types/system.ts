export interface LoginRequest {
  username: string;
  password: string;
}

export interface RoleSummary {
  id: number;
  name: string;
  code: string;
  description: string | null;
  is_system: boolean;
  menu_ids: number[];
}

export interface UserProfile {
  id: number;
  username: string;
  email: string | null;
  phone: string | null;
  nickname: string | null;
  status: "ACTIVE" | "DISABLED";
  is_superuser: boolean;
  roles: RoleSummary[];
  permissions: string[];
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserProfile;
}

export interface RoleItem {
  id: number;
  name: string;
  code: string;
  description: string | null;
  is_system: boolean;
  menu_ids: number[];
}

export interface MenuNode {
  id: number;
  parent_id: number | null;
  name: string;
  title: string;
  path: string | null;
  component: string | null;
  icon: string | null;
  permission_code: string | null;
  menu_type: "DIRECTORY" | "MENU" | "BUTTON";
  sort_order: number;
  hidden: boolean;
  created_at: string;
  updated_at: string;
  children: MenuNode[];
}

export interface SystemConfigItem {
  id: number;
  category: string;
  config_key: string;
  config_value: string;
  value_type: "STRING" | "INTEGER" | "FLOAT" | "BOOLEAN" | "JSON" | "SECRET";
  description: string | null;
  is_secret: boolean;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface PlatformAccountItem {
  id: number;
  platform: string;
  display_name: string;
  account_id: string;
  auth_status: "UNAUTHORIZED" | "AUTHORIZED" | "EXPIRED" | "DISABLED";
  access_token: string | null;
  refresh_token: string | null;
  expires_at: string | null;
  extra: Record<string, unknown> | null;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface OperationLogItem {
  id: number;
  module: string;
  action: string;
  biz_type: string | null;
  biz_id: string | null;
  operator_id: number | null;
  operator_name: string | null;
  request_id: string | null;
  method: string | null;
  path: string | null;
  ip_address: string | null;
  status: "SUCCESS" | "FAILED";
  message: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface ErrorLogItem {
  id: number;
  request_id: string | null;
  path: string | null;
  method: string | null;
  user_id: number | null;
  error_code: number;
  error_type: string;
  error_message: string;
  stack_trace: string | null;
  created_at: string;
}

export interface TaskJobItem {
  id: number;
  task_name: string;
  task_type: string;
  queue_name: string;
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "RETRYING" | "CANCELLED";
  celery_task_id: string | null;
  request_id: string | null;
  triggered_by: number | null;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  progress: number;
  error_message: string | null;
  retry_count: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FileAssetItem {
  id: number;
  original_name: string;
  storage_name: string;
  category: "IMAGE" | "AUDIO" | "VIDEO" | "DOCUMENT" | "OTHER";
  content_type: string;
  extension: string | null;
  size: number;
  storage_backend: string;
  storage_path: string;
  url: string;
  bucket_name: string | null;
  uploaded_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface HealthInfo {
  service: string;
  environment: string;
  api_prefix: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface UserUpsertForm {
  id?: number;
  username?: string;
  password?: string;
  email?: string | null;
  phone?: string | null;
  nickname?: string | null;
  role_ids: number[];
  is_superuser: boolean;
  status: "ACTIVE" | "DISABLED";
}

export interface RoleUpsertForm {
  id?: number;
  name: string;
  code: string;
  description?: string | null;
  menu_ids: number[];
  is_system: boolean;
}

export interface MenuUpsertForm {
  id?: number;
  parent_id: number | null;
  name: string;
  title: string;
  path?: string | null;
  component?: string | null;
  icon?: string | null;
  permission_code?: string | null;
  menu_type: "DIRECTORY" | "MENU" | "BUTTON";
  sort_order: number;
  hidden: boolean;
}

export interface ConfigUpsertForm {
  id?: number;
  category: string;
  config_key: string;
  config_value: string;
  value_type: "STRING" | "INTEGER" | "FLOAT" | "BOOLEAN" | "JSON" | "SECRET";
  description?: string | null;
  is_secret: boolean;
  is_enabled: boolean;
}

export interface PlatformAccountUpsertForm {
  id?: number;
  platform: string;
  display_name: string;
  account_id: string;
  auth_status: "UNAUTHORIZED" | "AUTHORIZED" | "EXPIRED" | "DISABLED";
  access_token?: string | null;
  refresh_token?: string | null;
  expires_at?: string | null;
  extra?: Record<string, unknown> | null;
  is_enabled: boolean;
}

export interface DemoTaskPayload {
  payload: {
    message: string;
  };
}

export interface DashboardOverview {
  health: HealthInfo;
  metrics: Array<{
    label: string;
    value: string;
    hint: string;
    trend?: string;
  }>;
  activity: OperationLogItem[];
  recent_tasks: TaskJobItem[];
}
