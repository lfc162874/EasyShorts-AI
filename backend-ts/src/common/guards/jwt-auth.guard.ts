/**
 * JWT 认证守卫
 * 从 Authorization: Bearer <token> 中提取并验证 JWT
 */
import {
  Injectable,
  ExecutionContext,
  UnauthorizedException as NestUnauthorizedException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { JwtService } from '@nestjs/jwt';
import { IS_PUBLIC_KEY } from '../decorators/public.decorator';
import { RequestIdUtil } from '../utils/request-id.util';
import type { RequestUser, JwtPayload } from '../interfaces';

@Injectable()
export class JwtAuthGuard {
  constructor(
    private readonly reflector: Reflector,
    private readonly jwtService: JwtService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // 检查 @Public() 装饰器
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;

    const request = context.switchToHttp().getRequest();
    const token = this.extractToken(request);

    if (!token) {
      throw new NestUnauthorizedException('未提供认证令牌');
    }

    try {
      const payload = this.jwtService.verify<JwtPayload>(token);
      // 将用户信息挂载到 request 上（后续中间件/守卫可使用）
      (request as Record<string, unknown>).user = {
        id: parseInt(payload.sub, 10),
        username: '',
        nickname: null,
        email: null,
        is_superuser: false,
        status: 'ACTIVE',
        permissions: [],
      } satisfies RequestUser;
      return true;
    } catch {
      throw new NestUnauthorizedException('认证令牌无效或已过期');
    }
  }

  private extractToken(request: Record<string, unknown>): string | null {
    const authHeader = request.headers?.['authorization'] as string | undefined;
    if (authHeader?.startsWith('Bearer ')) {
      return authHeader.slice(7);
    }
    return null;
  }
}
