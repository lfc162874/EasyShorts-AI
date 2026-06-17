/**
 * 公共接口定义
 */

/** 统一 API 响应结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
  request_id: string;
}

/** 分页数据结构 */
export interface PaginatedData<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

/** 当前请求用户信息 */
export interface RequestUser {
  id: number;
  username: string;
  nickname: string | null;
  email: string | null;
  is_superuser: boolean;
  status: string;
  permissions: string[];
}

/** JWT Payload */
export interface JwtPayload {
  sub: string; // 用户 ID
  iat?: number;
  exp?: number;
}
