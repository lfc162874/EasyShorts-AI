import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateNewsSourceDto } from './dto/create-news-source.dto';
import { NewsSourceType, NewsStatus, TaskStatus, NewsFetchMode } from '../common/constants/enums';

@Injectable()
export class NewsService {
  constructor(private readonly prisma: PrismaService) {}

  // ===== 新闻源 =====
  async listSources(query: {
    page?: number;
    page_size?: number;
    keyword?: string;
    source_type?: NewsSourceType;
    is_enabled?: boolean;
  }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const where: Record<string, unknown> = {};

    if (query.keyword) {
      where.OR = [
        { sourceKey: { contains: query.keyword } },
        { name: { contains: query.keyword } },
        { url: { contains: query.keyword } },
      ];
    }
    if (query.source_type) where.sourceType = query.source_type;
    if (query.is_enabled !== undefined) where.isEnabled = query.is_enabled;

    const [items, total] = await Promise.all([
      this.prisma.newsSource.findMany({
        where,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { isEnabled: 'desc', id: 'desc' },
      }),
      this.prisma.newsSource.count({ where }),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  async getSource(id: number) {
    const source = await this.prisma.newsSource.findUnique({ where: { id } });
    if (!source) throw new NotFoundException('新闻源不存在');
    return source;
  }

  async createSource(dto: CreateNewsSourceDto) {
    const existing = await this.prisma.newsSource.findFirst({
      where: {
        OR: [{ sourceKey: dto.source_key }, { url: dto.url }],
      },
    });
    if (existing) throw new ConflictException('新闻源标识或地址已存在');

    return this.prisma.newsSource.create({
      data: {
        sourceKey: dto.source_key.toLowerCase(),
        name: dto.name,
        sourceType: dto.source_type,
        url: dto.url.trim(),
        category: dto.category || null,
        language: dto.language || 'en',
        fetchIntervalMinutes: dto.fetch_interval_minutes ?? 360,
        isEnabled: dto.is_enabled !== false,
        extra: dto.extra || null,
      },
    });
  }

  async updateSource(id: number, dto: Partial<CreateNewsSourceDto>) {
    const source = await this.getSource(id);
    if (dto.url) {
      const conflict = await this.prisma.newsSource.findFirst({
        where: { url: dto.url.trim(), id: { not: id } },
      });
      if (conflict) throw new ConflictException('新闻源地址已存在');
    }
    const data: Record<string, unknown> = {};
    if (dto.name !== undefined) data.name = dto.name.trim();
    if (dto.source_key !== undefined) data.sourceKey = dto.source_key.toLowerCase();
    if (dto.source_type !== undefined) data.sourceType = dto.source_type;
    if (dto.url !== undefined) data.url = dto.url.trim();
    if (dto.category !== undefined) data.category = dto.category?.trim() || null;
    if (dto.language !== undefined) data.language = dto.language?.trim() || 'en';
    if (dto.fetch_interval_minutes !== undefined) data.fetchIntervalMinutes = dto.fetch_interval_minutes;
    if (dto.is_enabled !== undefined) data.isEnabled = dto.is_enabled;

    return this.prisma.newsSource.update({ where: { id }, data });
  }

  // ===== 新闻列表 =====
  async listNews(query: {
    page?: number;
    page_size?: number;
    keyword?: string;
    status?: NewsStatus;
    source_id?: number;
    category?: string;
  }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const where: Record<string, unknown> = {};

    if (query.keyword) {
      where.OR = [
        { title: { contains: query.keyword } },
        { source: { contains: query.keyword } },
        { category: { contains: query.keyword } },
        { summary: { contains: query.keyword } },
      ];
    }
    if (query.status) where.status = query.status;
    if (query.source_id) where.sourceId = query.source_id;
    if (query.category) where.category = query.category;

    const [items, total] = await Promise.all([
      this.prisma.news.findMany({
        where,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { publishTime: 'desc', id: 'desc' },
      }),
      this.prisma.news.count({ where }),
    ]);
    return { items, page, page_size: pageSize, total };
  }

  async getNews(id: number) {
    const news = await this.prisma.news.findUnique({ where: { id } });
    if (!news) throw new NotFoundException('新闻不存在');
    return news;
  }

  // ===== 采集记录 =====
  async listFetchRecords(query: {
    page?: number;
    page_size?: number;
    source_id?: number;
    status?: string;
  }) {
    const page = query.page || 1;
    const pageSize = query.page_size || 20;
    const where: Record<string, unknown> = {};
    if (query.source_id) where.sourceId = query.source_id;
    if (query.status) where.status = query.status;

    const [records, total] = await Promise.all([
      this.prisma.newsFetchRecord.findMany({
        where,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { id: 'desc' },
      }),
      this.prisma.newsFetchRecord.count({ where }),
    ]);

    // 补充来源名称
    const sourceIds = [...new Set(records.map((r) => r.sourceId))];
    const sources = await this.prisma.newsSource.findMany({
      where: { id: { in: sourceIds } },
      select: { id: true, name: true },
    });
    const sourceMap = new Map(sources.map((s) => [s.id, s.name]));

    const items = records.map((r) => ({
      ...r,
      source_name: sourceMap.get(r.sourceId) || null,
    }));

    return { items, page, page_size: pageSize, total };
  }
}
