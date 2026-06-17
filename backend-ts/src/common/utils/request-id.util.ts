/**
 * RequestId 工具
 * 使用 AsyncLocalStorage 存储当前请求的 request_id，贯穿整个请求生命周期
 */
import { AsyncLocalStorage } from 'async_hooks';

const requestIdStore = new AsyncLocalStorage<string>();

export const RequestIdUtil = {
  /** 获取当前请求的 request_id */
  getId(): string {
    return requestIdStore.getStore() || '';
  },

  /** 在上下文中运行回调 */
  run<T>(requestId: string, callback: () => T): T {
    return requestIdStore.run(requestId, callback);
  },
};

/** 生成新的 request_id (UUID v4) */
export function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback for older Node.js
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}
