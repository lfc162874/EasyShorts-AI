import { Module, Global } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from '../prisma/prisma.module';

import { LocalStorageService } from './local-storage.service';
import { FileUploadService } from './file-upload.service';
import type { IStorageService } from './storage.interfaces';

@Global()
@Module({
  imports: [ConfigModule, PrismaModule],
  providers: [
    LocalStorageService,
    // 将 IStorageService 令牌绑定到 LocalStorageService 实现
    {
      provide: 'IStorageService',
      useExisting: LocalStorageService,
    },
    FileUploadService,
  ],
  exports: [LocalStorageService, FileUploadService, 'IStorageService'],
})
export class StorageModule {}
