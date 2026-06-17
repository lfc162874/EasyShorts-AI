/**
 * 认证控制器
 * POST /auth/login  - 登录
 * POST /auth/logout - 登出
 * GET  /auth/me     - 获取当前用户信息
 */
import { Controller, Post, Get, Body, Req, UseGuards } from '@nestjs/common';
import { AuthService } from './auth.service';
import { Public } from '../common/decorators/public.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';
import { ReqUser } from '../common/decorators/current-user.decorator';
import type { RequestUser } from '../common/interfaces';

class LoginDto {
  username!: string;
  password!: string;
}

@Controller('auth')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Public()
  @Post('login')
  async login(@Body() dto: LoginDto) {
    return this.authService.login(dto.username, dto.password);
  }

  @Post('logout')
  async logout() {
    // JWT 无状态，前端清除 token 即可
    return { message: '登出成功' };
  }

  @Get('me')
  async getMe(@ReqUser() user: RequestUser) {
    return this.authService.getCurrentUser(user.id);
  }
}
