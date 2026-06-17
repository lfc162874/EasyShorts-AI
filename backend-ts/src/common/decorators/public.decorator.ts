/**
 * @Public() 装饰器
 * 标记接口无需 JWT 认证即可访问
 */
import { SetMetadata } from '@nestjs/common';

export const IS_PUBLIC_KEY = 'isPublic';

export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);
