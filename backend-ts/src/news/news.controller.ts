import { Controller, Get, Post, Put, Body, Param, Query, UseGuards } from '@nestjs/common';
import { NewsService } from './news.service';
import { CreateNewsSourceDto } from './dto/create-news-source.dto';
import { PaginationDto } from '../common/dto/pagination.dto';
import { NewsSourceType, NewsStatus } from '../common/constants/enums';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('news')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class NewsController {
  constructor(private readonly newsService: NewsService) {}

  // ===== 新闻源 =====
  @Get('sources')
  @Permissions('news:source:list')
  async listSources(@Query() query: PaginationDto & { source_type?: string; is_enabled?: string }) {
    return this.newsService.listSources({
      ...query,
      source_type: query.source_type as NewsSourceType | undefined,
      is_enabled: query.is_enabled === 'true' ? true : query.is_enabled === 'false' ? false : undefined,
    });
  }

  @Get('sources/:id')
  @Permissions('news:source:list')
  async getSource(@Param('id') id: string) {
    return this.newsService.getSource(+id);
  }

  @Post('sources')
  @Permissions('news:source:create')
  async createSource(@Body() dto: CreateNewsSourceDto) {
    return this.newsService.createSource(dto);
  }

  @Put('sources/:id')
  @Permissions('news:source:update')
  async updateSource(@Param('id') id: string, @Body() dto: Partial<CreateNewsSourceDto>) {
    return this.newsService.updateSource(+id, dto);
  }

  @Post('sources/:id/sync')
  @Permissions('news:source:update')
  async syncSource(@Param('id') id: string) {
    // TODO: 接入 RabbitMQ 任务队列后实现
    return { message: '同步任务已提交', source_id: +id };
  }

  // ===== 新闻列表 =====
  @Get()
  @Permissions('news:list')
  async listNews(@Query() query: PaginationDto & { status?: string; source_id?: string; category?: string }) {
    return this.newsService.listNews({
      ...query,
      status: query.status as NewsStatus | undefined,
      source_id: query.source_id ? +query.source_id : undefined,
    });
  }

  @Get(':id')
  @Permissions('news:list')
  async getNews(@Param('id') id: string) {
    return this.newsService.getNews(+id);
  }

  // ===== 采集记录 =====
  @Get('records')
  @Permissions('news:fetch-record:list')
  async listRecords(@Query() query: PaginationDto & { source_id?: string; status?: string }) {
    return this.newsService.listFetchRecords({
      ...query,
      source_id: query.source_id ? +query.source_id : undefined,
    });
  }
}
