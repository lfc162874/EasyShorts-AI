import http from "@/api/http";
import type { ApiResponse } from "@/types/common";
import type { LoginPayload, LoginResponse, UserProfile } from "@/types/system";

export const login = (payload: LoginPayload): Promise<ApiResponse<LoginResponse>> =>
  http.post("/auth/login", payload);

export const logout = (): Promise<ApiResponse<{ success: true }>> =>
  http.post("/auth/logout");

export const getCurrentUser = (): Promise<ApiResponse<UserProfile>> =>
  http.get("/auth/me");
