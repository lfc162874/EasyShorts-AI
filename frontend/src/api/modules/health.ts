import http from "@/api/http";
import type { ApiResponse } from "@/types/common";
import type { HealthInfo } from "@/types/system";

export const getHealth = (): Promise<ApiResponse<HealthInfo>> => http.get("/health");
