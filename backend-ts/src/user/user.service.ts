/**
 * 用户管理服务
 * CRUD /system/users
 */
import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { AuthService } from '../auth/auth.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';

@Injectable()
export class UserService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly authService: AuthService,
  ) {}

  async list(query: { page?: number; page_size?: number; keyword?: string }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const where: Record<string, unknown> = {};

    if (query.keyword) {
      where.OR = [
        { username: { contains: query.keyword } },
        { nickname: { contains: query.keyword } },
        { email: { contains: query.keyword } },
      ];
    }

    const [items, total] = await Promise.all([
      this.prisma.user.findMany({
        where,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
        select: {
          id: true,
          username: true,
          nickname: true,
          email: true,
          phone: true,
          status: true,
          isSuperuser: true,
          lastLoginAt: true,
          createdAt: true,
          updatedAt: true,
          roles: {
            select: {
              role: {
                select: { id: true, name: true, code: true },
              },
            },
          },
        },
      }),
      this.prisma.user.count({ where }),
    ]);

    return {
      items: items.map((u) => ({
        ...u,
        roles: u.roles.map((ur) => ur.role),
      })),
      page,
      page_size: pageSize,
      total,
    };
  }

  async getById(id: number) {
    const user = await this.prisma.user.findUnique({
      where: { id },
      include: {
        roles: {
          include: { role: true },
        },
      },
    });
    if (!user) throw new NotFoundException('用户不存在');
    return user;
  }

  async create(dto: CreateUserDto) {
    // 检查用户名唯一性
    const existing = await this.prisma.user.findUnique({
      where: { username: dto.username },
    });
    if (existing) throw new ConflictException('用户名已存在');

    const hashedPassword = await this.authService.hashPassword(dto.password);

    const user = await this.prisma.user.create({
      data: {
        username: dto.username,
        hashedPassword,
        nickname: dto.nickname || null,
        email: dto.email || null,
        phone: dto.phone || null,
        isSuperuser: dto.is_superuser || false,
        status: 'ACTIVE',
      },
    });

    // 分配角色
    if (dto.role_ids?.length) {
      await this.prisma.userRole.createMany({
        data: dto.role_ids.map((roleId) => ({
          userId: user.id,
          roleId,
        })),
        skipDuplicates: true,
      });
    }

    return this.getById(user.id);
  }

  async update(id: number, dto: UpdateUserDto) {
    await this.getById(id); // 确保用户存在

    const updateData: Record<string, unknown> = {};
    if (dto.nickname !== undefined) updateData.nickname = dto.nickname;
    if (dto.email !== undefined) updateData.email = dto.email;
    if (dto.phone !== undefined) updateData.phone = dto.phone;
    if (dto.is_superuser !== undefined) updateData.isSuperuser = dto.is_superuser;
    if (dto.password) {
      updateData.hashedPassword = await this.authService.hashPassword(dto.password);
    }

    await this.prisma.user.update({ where: { id }, data: updateData });

    // 更新角色关联
    if (dto.role_ids !== undefined) {
      await this.prisma.userRole.deleteMany({ where: { userId: id } });
      if (dto.role_ids.length > 0) {
        await this.prisma.userRole.createMany({
          data: dto.role_ids.map((roleId) => ({ userId: id, roleId })),
        });
      }
    }

    return this.getById(id);
  }
}
