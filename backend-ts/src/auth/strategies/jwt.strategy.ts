/**
 * JWT 策略
 * 由 JwtAuthGuard 调用，负责从 request 中提取并验证 token
 */
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(private readonly configService: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get<string>('jwt.secret', 'change-me-in-production-please'),
    });
  }

  async validate(payload: { sub: string }) {
    // sub 存储的是用户 ID
    const userId = parseInt(payload.sub, 10);
    if (!userId || isNaN(userId)) {
      throw new UnauthorizedException('无效的认证令牌');
    }
    return { id: userId };
  }
}
