import {
  listConfigs,
  listMenus,
  listOperationLogs,
  listPlatformAccounts,
  listRoles,
  listTasks,
  listUsers,
} from "@/api/modules/system";
import { getHealth } from "@/api/modules/health";
import type { MenuNode } from "@/types/system";
import type { DashboardOverview } from "@/types/system";

const flattenMenus = (items: MenuNode[]): number =>
  items.reduce(
    (count, item) => count + 1 + flattenMenus(item.children ?? []),
    0,
  );

export const getDashboardOverview = async (): Promise<DashboardOverview> => {
  const [
    health,
    users,
    roles,
    menus,
    configs,
    accounts,
    operations,
    tasks,
  ] = await Promise.all([
    getHealth(),
    listUsers({ page: 1, page_size: 1 }),
    listRoles({ page: 1, page_size: 1 }),
    listMenus(),
    listConfigs({ page: 1, page_size: 1 }),
    listPlatformAccounts({ page: 1, page_size: 1 }),
    listOperationLogs({ page: 1, page_size: 5 }),
    listTasks({ page: 1, page_size: 5 }),
  ]);

  return {
    health: health.data,
    metrics: [
      {
        label: "用户总数",
        value: String(users.data.total),
        hint: "系统账号与运营账号",
        trend: "基于 /system/users",
      },
      {
        label: "角色总数",
        value: String(roles.data.total),
        hint: "RBAC 角色配置",
        trend: "基于 /system/roles",
      },
      {
        label: "菜单总数",
        value: String(flattenMenus(menus.data.items)),
        hint: "含目录、菜单与按钮",
        trend: "基于 /system/menus",
      },
      {
        label: "配置项",
        value: String(configs.data.total),
        hint: "Prompt、平台、参数",
        trend: "基于 /system/configs",
      },
      {
        label: "平台账号",
        value: String(accounts.data.total),
        hint: "抖音、快手等账号",
        trend: "基于 /system/platform-accounts",
      },
      {
        label: "运行任务",
        value: String(tasks.data.total),
        hint: "任务中心最新状态",
        trend: "基于 /system/tasks",
      },
    ],
    activity: operations.data.items,
    recent_tasks: tasks.data.items,
  };
};
