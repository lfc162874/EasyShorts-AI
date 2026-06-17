/**
 * Local Storage Service
 *
 * 本地文件存储实现：
 * - 文件按 category/year/month/day 组织目录结构
 * - 支持随机文件名生成（防冲突）
 * - 提供静态文件访问 URL 映射
 */

import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { existsSync, mkdirSync, writeFileSync, unlinkSync, statSync, createReadStream } from 'fs';
import { join, relative } from 'path';
import { v4 as uuidv4 } from 'uuid';

import type {
  IStorageService,
  StorageFileInfo,
  StorageUploadOptions,
} from './storage.interfaces';

@Injectable()
export class LocalStorageService implements IStorageService {
  private readonly logger = new Logger(LocalStorageService.name);
  private readonly basePath: string;
  private readonly servePath: string;

  constructor(private readonly configService: ConfigService) {
    this.basePath =
      this.configService.get<string>('storage.localRoot') || join(process.cwd(), 'uploads');
    this.servePath =
      this.configService.get<string>('storage.servePath') || '/uploads';

    // 确保基础目录存在
    if (!existsSync(this.basePath)) {
      mkdirSync(this.basePath, { recursive: true });
      this.logger.log(`创建上传根目录: ${this.basePath}`);
    }
  }

  async upload(
    buffer: Buffer,
    filename: string,
    options: StorageUploadOptions,
  ): Promise<StorageFileInfo> {
    const now = new Date();
    const dateDir = `${now.getFullYear()}/${String(now.getMonth() + 1).padStart(2, '0')}/${String(now.getDate()).padStart(2, '0')}`;
    const subDir = options.subDir ? `${options.subDir}/` : '';
    const dirPath = join(this.basePath, options.category, subDir, dateDir);

    // 确保子目录存在
    if (!existsSync(dirPath)) {
      mkdirSync(dirPath, { recursive: true });
    }

    // 生成文件名
    const ext = filename.includes('.') ? '.' + filename.split('.').pop() : '';
    const finalName = options.randomName !== false
      ? `${uuidv4()}${ext}`
      : filename;

    const filePath = join(dirPath, finalName);
    writeFileSync(filePath, buffer);

    // 构建相对 key 和 URL
    const key = relative(this.basePath, filePath).replace(/\\/g, '/');
    const url = `${this.servePath}/${key}`;

    const fileInfo: StorageFileInfo = {
      key,
      originalName: filename,
      mimeType: this.guessMimeType(ext),
      size: buffer.length,
      url,
    };

    this.logger.debug(`文件已上传: ${key} (${buffer.length} bytes)`);
    return fileInfo;
  }

  async delete(key: string): Promise<boolean> {
    try {
      const filePath = join(this.basePath, key);
      if (existsSync(filePath)) {
        unlinkSync(filePath);
        this.logger.debug(`文件已删除: ${key}`);
        return true;
      }
      return false;
    } catch (error) {
      this.logger.error(`删除文件失败 [${key}]: ${error}`);
      return false;
    }
  }

  getUrl(key: string): string {
    return `${this.servePath}/${key}`;
  }

  async exists(key: string): Promise<boolean> {
    try {
      const filePath = join(this.basePath, key);
      return existsSync(filePath);
    } catch {
      return false;
    }
  }

  /** 获取本地文件绝对路径 */
  getAbsolutePath(key: string): string {
    return join(this.basePath, key);
  }

  /** 获取文件读取流 */
  createReadStream(key: string) {
    return createReadStream(join(this.basePath, key));
  }

  /** 获取文件统计信息 */
  getStat(key: string) {
    try {
      return statSync(join(this.basePath, key));
    } catch {
      return null;
    }
  }

  private guessMimeType(ext: string): string {
    const map: Record<string, string> = {
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.webp': 'image/webp',
      '.svg': 'image/svg+xml',
      '.pdf': 'application/pdf',
      '.json': 'application/json',
      '.txt': 'text/plain',
      '.md': 'text/markdown',
      '.mp4': 'video/mp4',
      '.mp3': 'audio/mpeg',
    };
    return map[ext.toLowerCase()] || 'application/octet-stream';
  }
}
