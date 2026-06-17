import { Controller, Get, Post, Put, Body, Param, Query, UseGuards } from '@nestjs/common';
import { SystemService } from './system.service';
import { PaginationDto } from '../common/dto/pagination.dto';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('system')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class SystemController {
  constructor(private readonly systemService: SystemService) {}

  // ===== 配置 =====
  @Get('configs')
  @Permissions('system:config:list')
  async listConfigs(@Query() query: PaginationDto) {
    return this.systemService.listConfigs(query);
  }

  @Post('configs')
  @Permissions('system:config:create')
  async createConfig(@Body() dto: any) {
    return this.systemService.createConfig(dto);
  }

  @Put('configs/:id')
  @Permissions('system:config:update')
  async updateConfig(@Param('id') id: string, @Body() dto: any) {
    return this.systemService.updateConfig(+id, dto);
  }

  // ===== 平台账号 =====
  @Get('platform-accounts')
  @Permissions('system:platform-account:list')
  async listPlatformAccounts(@Query() query: PaginationDto) {
    return this.systemService.listPlatformAccounts(query);
  }

  @Post('platform-accounts')
  @Permissions('system:platform-account:create')
  async createPlatformAccount(@Body() dto: any) {
    return this.systemService.createPlatformAccount(dto);
  }

  @Put('platform-accounts/:id')
  @Permissions('system:platform-account:update')
  async updatePlatformAccount(@Param('id') id: string, @Body() dto: any) {
    return this.systemService.updatePlatformAccount(+id, dto);
  }

  // ===== 日志 =====
  @Get('logs/operations')
  @Permissions('system:log:list')
  async listOperationLogs(@Query() query: PaginationDto) {
    return this.systemService.listOperationLogs(query);
  }

  @Get('logs/errors')
  @Permissions('system:log:list')
  async listErrorLogs(@Query() query: PaginationDto) {
    return this.systemService.listErrorLogs(query);
  }

  // ===== 任务 =====
  @Get('tasks')
  @Permissions('system:task:list')
  async listTasks(@Query() query: PaginationDto) {
    return this.systemService.listTaskJobs(query);
  }

  @Post('tasks/demo')
  @Permissions('system:task:list')
  async createDemoTask(@Body() body: { payload?: Record<string, unknown> }) {
    return this.systemService.createDemoTask(body.payload || {});
  }
}
