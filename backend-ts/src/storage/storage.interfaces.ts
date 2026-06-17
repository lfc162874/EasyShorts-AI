/**
 * Storage Service Interface
 *
 * 定义文件存储的抽象接口，支持本地存储和未来扩展（OSS/S3）
 */

export interface StorageUploadOptions {
  /** 文件分类 */
  category: string;
  /** 自定义子路径 */
  subDir?: string;
  /** 是否生成随机文件名 */
  randomName?: boolean;
}

export interface StorageFileInfo {
  /** 存储 key（相对路径） */
  key: string;
  /** 原始文件名 */
  originalName: string;
  /** MIME 类型 */
  mimeType: string;
  /** 文件大小（字节） */
  size: number;
  /** 访问 URL */
  url: string;
}

export interface IStorageService {
  /**
   * 上传文件（从 Buffer）
   */
  upload(buffer: Buffer, filename: string, options: StorageUploadOptions): Promise<StorageFileInfo>;

  /**
   * 删除文件
   */
  delete(key: string): Promise<boolean>;

  /**
   * 获取文件的访问 URL
   */
  getUrl(key: string): string;

  /**
   * 检查文件是否存在
   */
  exists(key: string): Promise<boolean>;
}
