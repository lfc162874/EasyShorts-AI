/**
 * 应用配置
 * 使用 @nestjs/config 的 registerAs() 映射所有环境变量
 * 与原 Python 后端 app/core/config.py 完全对齐
 */
export default () => ({
  app: {
    name: process.env.APP_NAME || 'EasyShortsAI',
    env: process.env.APP_ENV || 'development',
    debug: process.env.DEBUG === 'true',
    apiPrefix: process.env.API_PREFIX || '/easy-shorts',
  },
  database: {
    url: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/easy_shorts',
  },
  rabbitmq: {
    uri: process.env.RABBITMQ_URI || 'amqp://guest:guest@localhost:5672',
  },
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
  },
  jwt: {
    secret: process.env.SECRET_KEY || 'change-me-in-production-please',
    expiresIn:
      process.env.ACCESS_TOKEN_EXPIRE_MINUTES
        ? `${process.env.ACCESS_TOKEN_EXPIRE_MINUTES}m`
        : '720m',
  },
  agent: {
    defaultModelName: process.env.AGENT_DEFAULT_MODEL_NAME || 'qwen3.5-plus',
    defaultProvider: process.env.AGENT_DEFAULT_PROVIDER || 'dashscope',
    promptVersion: process.env.AGENT_PROMPT_VERSION || 'v1',
    dashscopeApiKey: process.env.DASHSCOPE_API_KEY || '',
    openaiApiKey: process.env.OPENAI_API_KEY || '',
    openaiBaseUrl: process.env.OPENAI_BASE_URL || '',
  },
  storage: {
    backend: process.env.STORAGE_BACKEND || 'local',
    localRoot: process.env.LOCAL_STORAGE_ROOT || './data/uploads',
    maxUploadSizeMb: parseInt(process.env.MAX_UPLOAD_SIZE_MB || '10', 10),
  },
  bootstrap: {
    autoCreateTables: process.env.AUTO_CREATE_TABLES === 'true',
    adminOnStartup: process.env.BOOTSTRAP_ADMIN_ON_STARTUP === 'true',
    adminUsername: process.env.ADMIN_USERNAME || 'admin',
    adminPassword: process.env.ADMIN_PASSWORD || 'admin123',
  },
  cors: {
    origins: (process.env.BACKEND_CORS_ORIGINS || 'http://localhost:5173').split(','),
  },
});
