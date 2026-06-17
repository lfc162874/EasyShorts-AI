import { Controller, Get, Post, Put, Body, Param, Query, UseGuards } from '@nestjs/common';
import { UserService } from './user.service';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { PaginationDto } from '../common/dto/pagination.dto';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('system/users')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @Permissions('system:user:list')
  async list(@Query() query: PaginationDto) {
    return this.userService.list(query);
  }

  @Get(':id')
  @Permissions('system:user:list')
  async getById(@Param('id') id: string) {
    return this.userService.getById(+id);
  }

  @Post()
  @Permissions('system:user:create')
  async create(@Body() dto: CreateUserDto) {
    return this.userService.create(dto);
  }

  @Put(':id')
  @Permissions('system:user:update')
  async update(@Param('id') id: string, @Body() dto: UpdateUserDto) {
    return this.userService.update(+id, dto);
  }
}
