/**
 * RBAC 权限守卫
 * 校验当前用户是否拥有 @Permissions() 声明的权限码
 * 超级管理员 (is_superuser) 自动绕过所有权限检查
 */
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException as NestForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { PERMISSIONS_KEY } from '../decorators/permissions.decorator';
import { IS_PUBLIC_KEY } from '../decorators/public.decorator';
import type { RequestUser } from '../interfaces';

@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // 检查 @Public() 装饰器
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;

    // 获取所需权限
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    // 未声明权限则放行
    if (!requiredPermissions || requiredPermissions.length === 0) return true;

    // 获取当前用户
    const request = context.switchToHttp().getRequest();
    const user = request.user as RequestUser | undefined;

    if (!user) throw new NestForbiddenException('未认证');

    // 超管绕过
    if (user.is_superuser) return true;

    // 检查权限
    const hasPermission = requiredPermissions.some((perm) =>
      user.permissions.includes(perm),
    );

    if (!hasPermission) {
      throw new NestForbiddenException('无权限访问当前资源');
    }

    return true;
  }
}
