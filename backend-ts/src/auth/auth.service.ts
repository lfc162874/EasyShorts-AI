/**
 * 认证服务
 * 处理登录、登出、Token 生成与验证
 * 与原 Python 后端 app/api/v1/auth.py + app/core/security.py 对齐
 */
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma/prisma.service';
import type { RequestUser, JwtPayload } from '../common/interfaces';

@Injectable()
export class AuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  /**
   * 用户登录
   * @returns access_token + user 信息（与原后端响应格式完全一致）
   */
  async login(username: string, password: string): Promise<{
    access_token: string;
    token_type: 'bearer';
    expires_in: number;
    user: RequestUser;
  }> {
    const user = await this.prisma.user.findFirst({
      where: {
        username,
        status: 'ACTIVE',
      },
      include: {
        roles: {
          include: {
            role: {
              include: {
                menus: {
                  include: { menu: true },
                },
              },
            },
          },
        },
      },
    });

    if (!user) {
      throw new UnauthorizedException('用户名或密码错误');
    }

    const isMatch = await this.verifyPassword(password, user.hashedPassword);
    if (!isMatch) {
      throw new UnauthorizedException('用户名或密码错误');
    }

    // 更新最后登录时间
    await this.prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() },
    });

    const payload: JwtPayload = { sub: String(user.id) };
    const accessToken = this.jwtService.sign(payload);

    // 构建用户权限列表
    const permissions = this._buildPermissions(user);

    const userProfile: RequestUser = {
      id: user.id,
      username: user.username,
      nickname: user.nickname,
      email: user.email,
      is_superuser: user.isSuperuser,
      status: user.status,
      permissions,
    };

    return {
      access_token: accessToken,
      token_type: 'bearer',
      expires_in: 86400, // 24 hours (default JWT expiry)
      user: userProfile,
    };
  }

  /**
   * 获取当前登录用户信息
   */
  async getCurrentUser(userId: number): Promise<Record<string, unknown>> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: {
        roles: {
          include: {
            role: true,
          },
        },
      },
    });

    if (!user || user.status !== 'ACTIVE') {
      throw new UnauthorizedException('用户不存在或已被禁用');
    }

    const permissions = this._buildPermissions(user);
    const roles = user.roles.map((ur) => ({
      id: ur.role.id,
      name: ur.role.name,
      display_name: ur.role.displayName,
    }));

    return {
      id: user.id,
      username: user.username,
      nickname: user.nickname,
      email: user.email,
      phone: null,
      is_superuser: user.isSuperuser,
      status: user.status,
      roles,
      permissions,
      last_login_at: user.lastLoginAt?.toISOString() || null,
      created_at: user.createdAt.toISOString(),
      updated_at: user.updatedAt.toISOString(),
    };
  }

  /** 密码哈希 */
  hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, 12);
  }

  /** 验证密码 */
  verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
    return bcrypt.compare(password, hashedPassword);
  }

  /** 从用户角色-菜单关系构建权限码列表 */
  private _buildPermissions(user: {
    roles: Array<{ role: { menus: Array<{ menu: { permissionCode: string | null } }> } }>;
    isSuperuser: boolean;
  }): string[] {
    if (user.isSuperuser) return ['*'];

    const perms = new Set<string>();
    for (const ur of user.roles) {
      for (const rm of ur.role.menus) {
        if (rm.menu.permissionCode) {
          perms.add(rm.menu.permissionCode);
        }
      }
    }
    return [...perms];
  }
}
