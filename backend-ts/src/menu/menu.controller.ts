import { Controller, Get, Post, Put, Body, Param, UseGuards } from '@nestjs/common';
import { MenuService } from './menu.service';
import { CreateMenuDto } from './dto/create-menu.dto';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('system/menus')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class MenuController {
  constructor(private readonly menuService: MenuService) {}

  @Get()
  @Permissions('system:menu:list')
  async list() {
    return this.menuService.list();
  }

  @Post()
  @Permissions('system:menu:create')
  async create(@Body() dto: CreateMenuDto) {
    return this.menuService.create(dto);
  }

  @Put(':id')
  @Permissions('system:menu:update')
  async update(@Param('id') id: string, @Body() dto: Partial<CreateMenuDto>) {
    return this.menuService.update(+id, dto);
  }
}
