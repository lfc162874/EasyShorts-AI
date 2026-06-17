/**
 * @ReqUser() 装饰器
 * 从 request 中提取当前登录用户信息
 */
import { createParamDecorator, ExecutionContext } from '@nestjs/common';
import type { RequestUser } from '../interfaces';

export const ReqUser = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext): RequestUser => {
    const request = ctx.switchToHttp().getRequest();
    return request.user as RequestUser;
  },
);
