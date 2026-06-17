import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateMenuDto } from './dto/create-menu.dto';

@Injectable()
export class MenuService {
  constructor(private readonly prisma: PrismaService) {}

  async list() {
    const items = await this.prisma.menu.findMany({
      orderBy: [{ parentId: 'asc' }, { sortOrder: 'asc' }, { id: 'asc' }],
    });
    return { items };
  }

  async getById(id: number) {
    const menu = await this.prisma.menu.findUnique({ where: { id } });
    if (!menu) throw new NotFoundException('菜单不存在');
    return menu;
  }

  async create(dto: CreateMenuDto) {
    return this.prisma.menu.create({
      data: {
        name: dto.name,
        title: dto.title,
        path: dto.path || null,
        component: dto.component || null,
        icon: dto.icon || null,
        permissionCode: dto.permission_code || null,
        menuType: dto.menu_type,
        sortOrder: dto.sort_order ?? 0,
        hidden: dto.hidden ?? false,
        parentId: dto.parent_id ?? null,
      },
    });
  }

  async update(id: number, dto: Partial<CreateMenuDto>) {
    await this.getById(id);
    const data: Record<string, unknown> = {};
    if (dto.name !== undefined) data.name = dto.name;
    if (dto.title !== undefined) data.title = dto.title;
    if (dto.path !== undefined) data.path = dto.path;
    if (dto.component !== undefined) data.component = dto.component;
    if (dto.icon !== undefined) data.icon = dto.icon;
    if (dto.permission_code !== undefined) data.permissionCode = dto.permission_code;
    if (dto.menu_type !== undefined) data.menuType = dto.menu_type;
    if (dto.sort_order !== undefined) data.sortOrder = dto.sort_order;
    if (dto.hidden !== undefined) data.hidden = dto.hidden;
    if (dto.parent_id !== undefined) data.parentId = dto.parent_id;

    return this.prisma.menu.update({ where: { id }, data });
  }
}
