import type { ApiResponse, PagedData } from "@/types/common";

const requestId = () =>
  `req_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36)}`;

export const successResponse = <T>(data: T, message = "ok"): ApiResponse<T> => ({
  code: 0,
  message,
  data,
  request_id: requestId(),
});

export const pagedResponse = <T>(
  items: T[],
  page = 1,
  pageSize = 10,
): ApiResponse<PagedData<T>> => ({
  code: 0,
  message: "ok",
  data: {
    items,
    page,
    page_size: pageSize,
    total: items.length,
  },
  request_id: requestId(),
});

export const wait = (timeout = 280) =>
  new Promise((resolve) => window.setTimeout(resolve, timeout));
