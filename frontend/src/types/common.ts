export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  request_id: string;
}

export interface PagedData<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface PaginationQuery {
  page?: number;
  page_size?: number;
  keyword?: string;
}

export interface OptionItem {
  label: string;
  value: string;
}

export interface StatCardItem {
  label: string;
  value: string;
  hint: string;
  trend?: string;
}
