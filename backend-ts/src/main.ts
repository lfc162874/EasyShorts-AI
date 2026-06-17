import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import helmet from 'helmet';

import { AppModule } from './app.module';
import { ResponseInterceptor } from './common/interceptors/response.interceptor';
import { AllExceptionsFilter } from './common/filters/all-exceptions.filter';
import { JwtAuthGuard } from './common/guards/jwt-auth.guard';
import { PermissionsGuard } from './common/guards/permissions.guard';
import { generateRequestId, RequestIdUtil } from './common/utils/request-id.util';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);

  // 安全中间件
  app.use(helmet());

  // CORS
  const origins = configService.get<string[]>('cors.origins', ['http://localhost:5173']);
  app.enableCors({
    origin: origins,
    credentials: true,
  });

  // API 前缀
  const apiPrefix = configService.get<string>('app.apiPrefix', '/easy-shorts');
  app.setGlobalPrefix(apiPrefix);

  // RequestId 中间件（必须在其他中间件之前）
  app.use((req: any, res: any, next: any) => {
    const requestId = (req.headers['x-request-id'] as string) || generateRequestId();
    req.headers['x-request-id'] = requestId;
    RequestIdUtil.run(requestId, next);
  });

  // 全局管道：DTO 校验 + 自动转型
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  // 全局守卫
  const reflector = app.get('Reflector' as any);
  const jwtService = app.get(JwtService);
  app.useGlobalGuards(new JwtAuthGuard(reflector, jwtService), new PermissionsGuard(reflector));

  // 全局拦截器：统一响应格式
  app.useGlobalInterceptors(new ResponseInterceptor());

  // 全局异常过滤器
  app.useGlobalFilters(new AllExceptionsFilter());

  const port = process.env.PORT || 8000;
  await app.listen(port);
  console.log(`🚀 EasyShorts AI Backend running on http://localhost:${port}${apiPrefix}`);
}

bootstrap();
