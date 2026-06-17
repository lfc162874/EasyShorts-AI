import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateRoleDto } from './dto/create-role.dto';

@Injectable()
export class RoleService {
  constructor(private readonly prisma: PrismaService) {}

  async list(query: { page?: number; page_size?: number; keyword?: string }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const where: Record<string, unknown> = {};

    if (query.keyword) {
      where.OR = [
        { name: { contains: query.keyword } },
        { code: { contains: query.keyword } },
      ];
    }

    const [items, total] = await Promise.all([
      this.prisma.role.findMany({
        where,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'asc' },
        include: {
          menus: {
            include: { menu: true },
          },
        },
      }),
      this.prisma.role.count({ where }),
    ]);

    return {
      items: items.map((r) => ({
        ...r,
        menus: r.menus.map((rm) => rm.menu),
      })),
      page,
      page_size: pageSize,
      total,
    };
  }

  async getById(id: number) {
    const role = await this.prisma.role.findUnique({
      where: { id },
      include: { menus: { include: { menu: true } } },
    });
    if (!role) throw new NotFoundException('角色不存在');
    return role;
  }

  async create(dto: CreateRoleDto) {
    const existing = await this.prisma.role.findUnique({ where: { code: dto.code } });
    if (existing) throw new ConflictException('角色编码已存在');

    const role = await this.prisma.role.create({
      data: {
        name: dto.name,
        code: dto.code,
        description: dto.description || null,
        isSystem: dto.is_system || false,
      },
    });

    if (dto.menu_ids?.length) {
      await this.prisma.roleMenu.createMany({
        data: dto.menu_ids.map((menuId) => ({ roleId: role.id, menuId })),
        skipDuplicates: true,
      });
    }

    return this.getById(role.id);
  }

  async update(id: number, dto: Partial<CreateRoleDto>) {
    await this.getById(id);

    if (dto.name !== undefined || dto.code !== undefined || dto.description !== undefined) {
      if (dto.code) {
        const existing = await this.prisma.role.findFirst({
          where: { code: dto.code, id: { not: id } },
        });
        if (existing) throw new ConflictException('角色编码已存在');
      }
      await this.prisma.role.update({
        where: { id },
        data: {
          ...(dto.name && { name: dto.name }),
          ...(dto.code && { code: dto.code }),
          ...(dto.description !== undefined && { description: dto.description }),
        },
      });
    }
    return this.getById(id);
  }

  async assignMenus(id: number, menuIds: number[]) {
    await this.getById(id);
    await this.prisma.roleMenu.deleteMany({ where: { roleId: id } });
    if (menuIds.length > 0) {
      await this.prisma.roleMenu.createMany({
        data: menuIds.map((menuId) => ({ roleId: id, menuId })),
      });
    }
    return this.getById(id);
  }
}
