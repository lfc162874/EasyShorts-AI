/**
 * 业务异常体系
 * 与原 Python 后端 app/core/exceptions.py 完全对齐
 */

export class AppException extends Error {
  constructor(
    public readonly message: string,
    public readonly code: number,
    public readonly statusCode: number,
    public readonly data?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'AppException';
  }
}

/** 未认证 (401) */
export class UnauthorizedException extends AppException {
  constructor(message = '未认证或登录已失效') {
    super(message, 40100, 401);
  }
}

/** 无权限 (403) */
export class ForbiddenException extends AppException {
  constructor(message = '无权限访问当前资源') {
    super(message, 40300, 403);
  }
}

/** 资源不存在 (404) */
export class NotFoundException extends AppException {
  constructor(message = '资源不存在') {
    super(message, 40400, 404);
  }
}

/** 资源冲突 (409) */
export class ConflictException extends AppException {
  constructor(message = '资源状态冲突') {
    super(message, 40900, 409);
  }
}

/** 校验失败 (422) */
export class ValidationException extends AppException {
  constructor(message = '业务校验失败', data?: Record<string, unknown>) {
    super(message, 42200, 422, data);
  }
}
