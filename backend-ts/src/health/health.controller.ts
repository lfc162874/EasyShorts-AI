import { Controller, Get } from '@nestjs/common';
import { Public } from '../common/decorators/public.decorator';

@Controller()
export class HealthController {
  @Public()
  @Get('health')
  healthcheck() {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      service: 'EasyShorts AI Backend',
    };
  }
}
