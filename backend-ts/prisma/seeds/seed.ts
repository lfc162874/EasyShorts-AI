/**
 * Bootstrap Seed Data Script
 *
 * 初始化系统基础数据：
 * - 超级管理员用户 (admin / admin123)
 * - 操作员用户 (operator / operator123)
 * - 预设角色（超级管理员、操作员）
 * - 预设菜单（系统管理、新闻管理、Agent 管理、推送管理）
 * - 系统配置项
 *
 * 用法: npx tsx prisma/seeds/seed.ts
 */

import { PrismaClient } from '@prisma/client';
import { hashSync } from 'bcrypt';

const prisma = new PrismaClient();

// ===== 数据定义 =====

const ROLES = [
  {
    name: 'super_admin',
    displayName: '超级管理员',
    description: '拥有所有权限',
    isSystem: true,
    sortOrder: 1,
  },
  {
    name: 'operator',
    displayName: '操作员',
    description: '日常运营操作权限',
    isSystem: true,
    sortOrder: 2,
  },
];

const USERS = [
  {
    username: 'admin',
    password: hashSync('admin123', 10),
    nickname: '系统管理员',
    email: 'admin@easyshorts.ai',
    isSuperuser: true,
    status: 'ACTIVE' as const,
  },
  {
    username: 'operator',
    password: hashSync('operator123', 10),
    nickname: '运营操作员',
    email: 'operator@easyshorts.ai',
    isSuperuser: false,
    status: 'ACTIVE' as const,
  },
];

// admin -> super_admin, operator -> operator
const USER_ROLE_MAP: Record<string, string> = {
  admin: 'super_admin',
  operator: 'operator',
};

const MENUS = [
  // 系统管理
  { name: 'Dashboard', path: '/dashboard', component: '', icon: 'dashboard', menuType: 'DIRECTORY' as const, parentId: null, sortOrder: 1, permission: '' },
  { name: 'User Management', path: '/system/users', component: 'system/users/index', icon: 'user', menuType: 'MENU' as const, parentId: null, sortOrder: 10, permission: 'system:user:list' },
  { name: 'Role Management', path: '/system/routes', component: 'system/routes/index', icon: 'team', menuType: 'MENU' as const, parentId: null, sortOrder: 20, permission: 'system:role:list' },
  { name: 'Menu Management', path: '/system/menus', component: 'system/menus/index', icon: 'menu', menuType: 'MENU' as const, parentId: null, sortOrder: 30, permission: 'system:menu:list' },

  // 新闻管理
  { name: 'News Sources', path: '/news/sources', component: 'news/sources/index', icon: 'read', menuType: 'MENU' as const, parentId: null, sortOrder: 40, permission: 'news:source:list' },
  { name: 'News List', path: '/news/list', component: 'news/list/index', icon: 'unordered-list', menuType: 'MENU' as const, parentId: null, sortOrder: 50, permission: 'news:list' },
  { name: 'Fetch Records', path: '/news/records', component: 'news/records/index', icon: 'history', menuType: 'MENU' as const, parentId: null, sortOrder: 60, permission: 'news:fetch-record:list' },

  // Agent 管理
  { name: 'Agent Config', path: '/agent/config', component: 'agent/config/index', icon: 'robot', menuType: 'MENU' as const, parentId: null, sortOrder: 70, permission: 'agent:config:list' },
  { name: 'Agent Runs', path: '/agent/runs', component: 'agent/runs/index', icon: 'thunderbolt', menuType: 'MENU' as const, parentId: null, sortOrder: 80, permission: 'agent:run:list' },
  { name: 'Hot Topics', path: '/agent/hot-topics', component: 'agent/hot-topics/index', icon: 'fire', menuType: 'MENU' as const, parentId: null, sortOrder: 90, permission: 'agent:hot-topic:list' },
  { name: 'Push Plans', path: '/agent/push-plans', component: 'agent/push-plans/index', icon: 'send', menuType: 'MENU' as const, parentId: null, sortOrder: 100, permission: 'agent:push-plan:list' },

  // 系统设置
  { name: 'Platform Accounts', path: '/system/accounts', component: 'system/accounts/index', icon: 'cloud-server', menuType: 'MENU' as const, parentId: null, sortOrder: 110, permission: 'system:account:list' },
  { name: 'Operation Logs', path: '/system/logs', component: 'system/logs/index', icon: 'file-text', menuType: 'MENU' as const, parentId: null, sortOrder: 120, permission: 'system:log:list' },
  { name: 'Task Jobs', path: '/system/tasks', component: 'system/tasks/index', icon: 'schedule', menuType: 'MENU' as const, parentId: null, sortOrder: 130, permission: 'system:task:list' },
  { name: 'System Configs', path: '/system/configs', component: 'system/configs/index', icon: 'setting', menuType: 'MENU' as const, parentId: null, sortOrder: 140, permission: 'system:config:list' },
];

/** 超级管理员拥有所有菜单 */
const SUPER_ADMIN_ALL_PERMISSIONS = MENUS.map((m) => m.permission).filter(Boolean);

/** 操作员权限 */
const OPERATOR_PERMISSIONS = [
  'news:source:list', 'news:source:create', 'news:source:update',
  'news:list',
  'agent:config:list', 'agent:config:update',
  'agent:model:list',
  'agent:run:create', 'agent:run:list',
  'agent:hot-topic:list',
  'agent:push-plan:list',
  'agent:digest:create',
];

const SYSTEM_CONFIGS = [
  // Agent 配置
  { category: 'agent', configKey: 'default_model_name', configValue: 'qwen3.5-plus', valueType: 'STRING', isEnabled: true },
  { category: 'agent', configKey: 'supported_models', configValue: 'qwen3.5-plus,qwen-max,gpt-4o,gpt-4o-mini,claude-sonnet-4-20250514,deepseek-chat', valueType: 'STRING', isEnabled: true },
  { category: 'agent', configKey: 'default_provider', configValue: 'dashscope', valueType: 'STRING', isEnabled: true },
  { category: 'agent', configKey: 'prompt_version', configValue: 'v1', valueType: 'STRING', isEnabled: true },
  { category: 'agent', configKey: 'push_channels', configValue: 'webhook,email,feishu', valueType: 'STRING', isEnabled: true },
  { category: 'agent', configKey: 'hot_threshold', configValue: '35', valueType: 'NUMBER', isEnabled: true },

  // Prompt 模板（从 prompts 目录读取的占位符，实际使用时从 DB 或文件加载）
  { category: 'prompt', configKey: 'hotspot_prompt', configValue: '判断输入内容是否属于高价值 AI 热点，输出结构化 JSON。要求：只输出 JSON；评估热度、趋势和推荐理由；保持简洁、稳定、可复现。', valueType: 'TEXT', isEnabled: true },
  { category: 'prompt', configKey: 'classification_prompt', configValue: '根据输入内容输出主分类、标签和关键词，要求只输出 JSON。要求：分类要稳定；标签最多 5 个；关键词最多 6 个。', valueType: 'TEXT', isEnabled: true },
  { category: 'prompt', configKey: 'summary_prompt', configValue: '根据输入内容生成优化标题、一句话摘要和核心要点，要求只输出 JSON。要求：标题简洁明确；摘要突出核心结论；要点控制在 3 到 5 条。', valueType: 'TEXT', isEnabled: true },
  { category: 'prompt', configKey: 'enrichment_prompt', configValue: '根据输入内容补充背景说明、行业影响、技术解读和应用场景，要求只输出 JSON。要求：保持分析客观；适合热点解读场景。', valueType: 'TEXT', isEnabled: true },
  { category: 'prompt', configKey: 'push_planner_prompt', configValue: '根据输入内容输出推送决策，要求只输出 JSON。要求：判断是否立即推送；输出优先级、渠道和计划时间；不要输出自然语言解释。', valueType: 'TEXT', isEnabled: true },
  { category: 'prompt', configKey: 'digest_prompt', configValue: '聚合多条热点内容，输出 AI 热点简报，要求只输出 JSON。要求：简报标题清晰；摘要简洁；适合日报/周报场景。', valueType: 'TEXT', isEnabled: true },

  // 参数配置
  { category: 'parameter', configKey: 'fetch_interval_minutes', configValue: '360', valueType: 'NUMBER', isEnabled: true },
  { category: 'parameter', configKey: 'max_news_per_fetch', configValue: '50', valueType: 'NUMBER', isEnabled: true },
  { category: 'parameter', configKey: 'digest_schedule_cron', configValue: '0 8 * * *', valueType: 'STRING', isEnabled: true },
  { category: 'parameter', configKey: 'auto_push_enabled', configValue: 'false', valueType: 'BOOLEAN', isEnabled: true },
];

// ===== 主函数 =====

async function main() {
  console.log('🌱 开始初始化种子数据...\n');

  // 1. 创建角色
  console.log('📋 创建角色...');
  for (const role of ROLES) {
    await prisma.role.upsert({
      where: { name: role.name },
      update: role,
      create: role,
    });
    console.log(`   ✅ ${role.displayName} (${role.name})`);
  }

  // 2. 创建用户 + 分配角色
  console.log('\n👤 创建用户...');
  for (const user of USERS) {
    const created = await prisma.user.upsert({
      where: { username: user.username },
      update: user,
      create: user,
    });

    // 分配角色
    const roleName = USER_ROLE_MAP[user.username];
    if (roleName) {
      const role = await prisma.role.findUnique({ where: { name: roleName } });
      if (role) {
        await prisma.userRole.upsert({
          where: { userId_roleId: { userId: created.id, roleId: role.id } },
          create: { userId: created.id, roleId: role.id },
          update: {},
        });
        console.log(`   ✅ ${user.nickname} (${user.username}) -> ${roleName}`);
      }
    }
  }

  // 3. 创建菜单
  console.log('\n📂 创建菜单...');
  const createdMenus: Map<string, number> = new Map();
  for (const menu of MENUS) {
    const created = await prisma.menu.upsert({
      where: { name_path: { name: menu.name, path: menu.path } },
      update: menu,
      create: menu,
    });
    createdMenus.set(`${menu.name}:${menu.path}`, created.id);
    console.log(`   ✅ ${menu.name} (${menu.path})`);
  }

  // 4. 为超级管理员分配所有菜单
  console.log('\n🔗 分配菜单权限...');
  const superAdminRole = await prisma.role.findUnique({ where: { name: 'super_admin' } });
  const operatorRole = await prisma.role.findUnique({ where: { name: 'operator' } });

  if (superAdminRole) {
    for (const [key, menuId] of createdMenus) {
      await prisma.roleMenu.upsert({
        where: { roleId_menuId: { roleId: superAdminRole.id, menuId } },
        create: { roleId: superAdminRole.id, menuId },
        update: {},
      });
    }
    console.log(`   ✅ super_admin -> 全部 ${createdMenus.size} 个菜单`);
  }

  if (operatorRole) {
    let count = 0;
    for (const [key, menuId] of createdMenus) {
      const menu = MENUS.find(
        (m) => `${m.name}:${m.path}` === key && OPERATOR_PERMISSIONS.includes(m.permission),
      );
      if (menu) {
        await prisma.roleMenu.upsert({
          where: { roleId_menuId: { roleId: operatorRole.id, menuId } },
          create: { roleId: operatorRole.id, menuId },
          update: {},
        });
        count++;
      }
    }
    console.log(`   ✅ operator -> ${count} 个菜单`);
  }

  // 5. 创建系统配置
  console.log('\n⚙️  创建系统配置...');
  for (const config of SYSTEM_CONFIGS) {
    await prisma.systemConfig.upsert({
      where: { category_configKey: { category: config.category, configKey: config.configKey } },
      update: config,
      create: config,
    });
  }
  console.log(`   ✅ ${SYSTEM_CONFIGS.length} 条配置项`);

  console.log('\n✨ 种子数据初始化完成！');
  console.log('');
  console.log('默认账号:');
  console.log('  超级管理员: admin / admin123');
  console.log('  操作员:     operator / operator123');
}

main()
  .catch((e) => {
    console.error('❌ 种子数据初始化失败:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
