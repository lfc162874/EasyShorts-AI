/**
 * 统一响应拦截器
 * 自动将 Controller 返回值包装为 { code, message, data, request_id } 格式
 * 与原 Python 后端 success_response() 完全对齐
 */
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable, map } from 'rxjs';
import type { ApiResponse } from '../interfaces';
import { RequestIdUtil } from '../utils/request-id.util';

@Injectable()
export class ResponseInterceptor<T> implements NestInterceptor<T, ApiResponse<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<ApiResponse<T>> {
    return next.handle().pipe(
      map((data) => ({
        code: 0,
        message: 'ok',
        data: data ?? {},
        request_id: RequestIdUtil.getId(),
      })),
    );
  }
}
