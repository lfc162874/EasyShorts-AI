import { Controller, Get, Post, Put, Body, Param, Query, UseGuards } from '@nestjs/common';
import { RoleService } from './role.service';
import { CreateRoleDto } from './dto/create-role.dto';
import { PaginationDto } from '../common/dto/pagination.dto';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('system/roles')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class RoleController {
  constructor(private readonly roleService: RoleService) {}

  @Get()
  @Permissions('system:role:list')
  async list(@Query() query: PaginationDto) {
    return this.roleService.list(query);
  }

  @Get(':id')
  @Permissions('system:role:list')
  async getById(@Param('id') id: string) {
    return this.roleService.getById(+id);
  }

  @Post()
  @Permissions('system:role:create')
  async create(@Body() dto: CreateRoleDto) {
    return this.roleService.create(dto);
  }

  @Put(':id')
  @Permissions('system:role:update')
  async update(@Param('id') id: string, @Body() dto: Partial<CreateRoleDto>) {
    return this.roleService.update(+id, dto);
  }

  @Put(':id/menus')
  @Permissions('system:role:list')
  async assignMenus(@Param('id') id: string, @Body('menu_ids') menuIds: number[]) {
    return this.roleService.assignMenus(+id, menuIds || []);
  }
}
