/**
 * File Upload Service
 *
 * 基于 Multer 的文件上传服务：
 * - 限制文件大小（默认 10MB）
 * - 支持按 category 分类存储
 * - 上传记录写入 DB（FileAsset 表）
 * - 返回统一的 StorageFileInfo
 */

import {
  Injectable,
  Logger,
  BadRequestException,
  Inject,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { MulterModule } from '@nestjs/platform-express';
import { diskStorage, memoryStorage } from 'multer';
import { extname, join } from 'path';
import { v4 as uuidv4 } from 'uuid';

import { PrismaService } from '../prisma/prisma.service';
import type {
  IStorageService,
  StorageFileInfo,
  StorageUploadOptions,
} from './storage.interfaces';

/** 上传文件接口（兼容 UploadedFile） */
export interface UploadedFile {
  fieldname: string;
  originalname: string;
  encoding: string;
  mimetype: string;
  size: number;
  destination: string;
  filename: string;
  path: string;
  buffer: Buffer;
}

/** 允许上传的 MIME 类型 */
export const ALLOWED_MIME_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/svg+xml',
  'application/pdf',
  'application/json',
  'text/plain',
  'text/markdown',
  'video/mp4',
  'audio/mpeg',
]);

/** 默认最大文件大小 (10MB) */
const DEFAULT_MAX_SIZE = 10 * 1024 * 1024;

@Injectable()
export class FileUploadService {
  private readonly logger = new Logger(FileUploadService.name);
  private readonly maxSize: number;

  constructor(
    private readonly configService: ConfigService,
    private readonly prisma: PrismaService,
    @Inject('IStorageService') private readonly storage: IStorageService,
  ) {
    this.maxSize =
      this.configService.get<number>('storage.maxSize', DEFAULT_MAX_SIZE);
  }

  /**
   * 处理上传的文件
   */
  async handleUpload(file: UploadedFile, options: StorageUploadOptions): Promise<StorageFileInfo> {
    if (!file) {
      throw new BadRequestException('未提供上传文件');
    }

    // 校验 MIME 类型
    if (!ALLOWED_MIME_TYPES.has(file.mimetype)) {
      throw new BadRequestException(`不支持的文件类型: ${file.mimetype}`);
    }

    // 校验文件大小
    if (file.size > this.maxSize) {
      throw new BadRequestException(`文件过大，最大允许 ${this.maxSize / 1024 / 1024}MB`);
    }

    // 存储文件
    const fileInfo = await this.storage.upload(file.buffer, file.originalname, options);

    // 写入数据库记录（使用 Prisma schema 正确字段名）
    await this.prisma.fileAsset.create({
      data: {
        originalName: file.originalname,
        storageName: fileInfo.key,
        extension: extname(file.originalname) || undefined,
        size: file.size,
        contentType: file.mimetype,
        storagePath: fileInfo.key,
        url: fileInfo.url,
        category: options.category as any,
      },
    });

    return fileInfo;
  }

  /** 批量处理上传 */
  async handleUploadMultiple(
    files: UploadedFile[],
    options: StorageUploadOptions,
  ): Promise<StorageFileInfo[]> {
    if (!files || files.length === 0) {
      throw new BadRequestException('未提供上传文件');
    }
    return Promise.all(files.map((f) => this.handleUpload(f, options)));
  }

  /**
   * 获取 Multer Module 配置（用于内存模式）
   */
  static getMulterConfig(maxSize = DEFAULT_MAX_SIZE) {
    return MulterModule.register({
      limits: { fileSize: maxSize },
      storage: memoryStorage(),
      fileFilter(_req, file, cb) {
        if (ALLOWED_MIME_TYPES.has(file.mimetype)) {
          cb(null, true);
        } else {
          cb(new Error(`不支持的文件类型: ${file.mimetype}`), false);
        }
      },
    });
  }

  /**
   * 获取磁盘存储配置（用于大文件）
   */
  static getDiskStorageConfig(dest = './uploads/temp') {
    return MulterModule.register({
      storage: diskStorage({
        destination: (_req, _file, cb) => {
          const fs = require('fs');
          if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
          }
          cb(null, dest);
        },
        filename: (_req, file, cb) => {
          const ext = extname(file.originalname);
          cb(null, `${uuidv4()}${ext}`);
        },
      }),
    });
  }
}
