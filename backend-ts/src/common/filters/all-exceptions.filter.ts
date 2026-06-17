/**
 * 全局异常过滤器
 * 统一捕获业务异常和未预期异常，返回标准错误响应格式
 * 与原 Python 后端 error_response() 完全对齐
 */
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Response } from 'express';
import { ValidationError } from 'class-validator';
import {
  AppException,
  UnauthorizedException,
  ForbiddenException,
  NotFoundException,
  ConflictException,
  ValidationException,
} from '../exceptions/app.exception';
import { RequestIdUtil } from '../utils/request-id.util';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const requestId = RequestIdUtil.getId();

    // 业务异常
    if (exception instanceof AppException) {
      return response.status(exception.statusCode).json({
        code: exception.code,
        message: exception.message,
        data: exception.data ?? {},
        request_id: requestId,
      });
    }

    // class-validator 校验失败
    if (exception instanceof ValidationError && Array.isArray((exception as any).errors)) {
      return response.status(HttpStatus.BAD_REQUEST).json({
        code: 40000,
        message: '请求参数校验失败',
        data: this.formatValidationErrors(exception),
        request_id: requestId,
      });
    }

    // NestJS 内置 HttpException
    if (exception instanceof HttpException) {
      const status = exception.getStatus();
      const res = exception.getResponse();
      const message =
        typeof res === 'string' ? res : (res as Record<string, unknown>).message;

      return response.status(status).json({
        code: status * 100,
        message: Array.isArray(message) ? message.join('; ') : String(message ?? '请求错误'),
        data: {},
        request_id: requestId,
      });
    }

    // 未预期的异常
    const errMsg = exception instanceof Error ? exception.message : '未知错误';
    console.error(`[Unhandled Exception] ${errMsg}`, exception);

    return response.status(HttpStatus.INTERNAL_SERVER_ERROR).json({
      code: 50000,
      message: process.env.APP_ENV === 'production' ? '服务器内部错误' : errMsg,
      data: {},
      request_id: requestId,
    });
  }

  private formatValidationErrors(error: ValidationError): Record<string, string[]> {
    const errors: Record<string, string[]> = {};
    for (const constraint of Object.values(error.constraints || {})) {
      errors[error.property] = errors[error.property] || [];
      errors[error.property].push(constraint);
    }
    return errors;
  }
}
