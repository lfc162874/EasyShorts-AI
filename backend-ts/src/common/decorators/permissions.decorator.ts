/**
 * @Permissions() 装饰器
 * 标记接口所需的权限码
 */
import { SetMetadata } from '@nestjs/common';

export const PERMISSIONS_KEY = 'permissions';

export const Permissions = (...permissions: string[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);
