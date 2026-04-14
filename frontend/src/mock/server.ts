import type { PaginationQuery } from "@/types/common";
import type {
  ConfigRecord,
  FileAsset,
  LoginPayload,
  LoginResult,
  LogEntry,
  MenuForm,
  MenuItem,
  RoleForm,
  RoleItem,
  TaskJob,
  UserForm,
  UserProfile,
} from "@/types/system";
import {
  dashboardStats,
  dashboardTimeline,
  defaultConfigs,
  defaultFiles,
  defaultLogs,
  defaultMenus,
  defaultRoles,
  defaultTasks,
  defaultUsers,
} from "@/mock/data";
import { pagedResponse, successResponse, wait } from "@/utils/request";

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

const currentUserKey = "easyshorts-user";

let users = clone(defaultUsers);
let roles = clone(defaultRoles);
let menus = clone(defaultMenus);
let configs = clone(defaultConfigs);
let files = clone(defaultFiles);
let logs = clone(defaultLogs);
let tasks = clone(defaultTasks);

const nextId = (items: Array<{ id: number }>) =>
  items.length ? Math.max(...items.map((item) => item.id)) + 1 : 1;

const applyKeywordFilter = <T>(
  items: T[],
  keyword = "",
) => {
  if (!keyword.trim()) {
    return items;
  }

  return items.filter((item) =>
    JSON.stringify(item).toLowerCase().includes(keyword.toLowerCase()),
  );
};

const applyPagination = <T>(
  items: T[],
  query: PaginationQuery = {},
) => {
  const page = query.page ?? 1;
  const pageSize = query.page_size ?? 10;
  const start = (page - 1) * pageSize;
  return {
    page,
    pageSize,
    total: items.length,
    items: items.slice(start, start + pageSize),
  };
};

const pushLog = (entry: Omit<LogEntry, "id" | "created_at" | "request_id">) => {
  logs = [
    {
      id: nextId(logs),
      created_at: new Date().toLocaleString("zh-CN", { hour12: false }),
      request_id: `req_${Math.random().toString(36).slice(2, 9)}`,
      ...entry,
    },
    ...logs,
  ];
};

export const mockServer = {
  async login(payload: LoginPayload) {
    await wait();

    const user =
      users.find((item) => item.username === payload.username) ?? users[0];

    const result: LoginResult = {
      token: "mock-jwt-token",
      refresh_token: "mock-refresh-token",
      user,
    };

    return successResponse(result, "登录成功");
  },

  async getCurrentUser() {
    await wait(180);
    const storedUser = window.localStorage.getItem(currentUserKey);
    if (storedUser) {
      return successResponse(JSON.parse(storedUser) as UserProfile);
    }
    return successResponse(users[0]);
  },

  async getDashboard() {
    await wait(220);
    return successResponse({
      stats: dashboardStats,
      timeline: dashboardTimeline,
      system_health: {
        api: "正常",
        redis: "正常",
        worker: "有 1 个任务重试中",
        upload: "mock-oss 可用",
      },
    });
  },

  async listUsers(query: PaginationQuery) {
    await wait();
    const filtered = applyKeywordFilter(users, query.keyword);
    const { items, page, pageSize, total } = applyPagination(filtered, query);
    return {
      ...pagedResponse(items, page, pageSize),
      data: {
        items,
        page,
        page_size: pageSize,
        total,
      },
    };
  },

  async saveUser(payload: UserForm) {
    await wait();

    if (payload.id) {
      users = users.map((item) =>
        item.id === payload.id
          ? {
              ...item,
              ...payload,
              permissions:
                payload.roles.includes("超级管理员")
                  ? defaultUsers[0].permissions
                  : defaultUsers[1].permissions,
            }
          : item,
      );
      pushLog({
        module: "system-user",
        operator: "admin",
        result: "success",
        type: "operation",
        message: `更新了用户 ${payload.username}。`,
      });
      return successResponse(null, "用户已更新");
    }

    users = [
      {
        id: nextId(users),
        username: payload.username,
        nickname: payload.nickname,
        email: payload.email,
        status: payload.status,
        roles: payload.roles,
        permissions:
          payload.roles.includes("超级管理员")
            ? defaultUsers[0].permissions
            : defaultUsers[1].permissions,
        last_login_at: "-",
      },
      ...users,
    ];

    pushLog({
      module: "system-user",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `创建了用户 ${payload.username}。`,
    });
    return successResponse(null, "用户已创建");
  },

  async deleteUser(id: number) {
    await wait();
    const target = users.find((item) => item.id === id);
    users = users.filter((item) => item.id !== id);
    pushLog({
      module: "system-user",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `删除了用户 ${target?.username ?? id}。`,
    });
    return successResponse(null, "用户已删除");
  },

  async listRoles(query: PaginationQuery) {
    await wait();
    const filtered = applyKeywordFilter(roles, query.keyword);
    const { items, page, pageSize, total } = applyPagination(filtered, query);
    return {
      ...pagedResponse(items, page, pageSize),
      data: {
        items,
        page,
        page_size: pageSize,
        total,
      },
    };
  },

  async saveRole(payload: RoleForm) {
    await wait();

    if (payload.id) {
      roles = roles.map((item) => (item.id === payload.id ? { ...item, ...payload } : item));
      pushLog({
        module: "system-role",
        operator: "admin",
        result: "success",
        type: "operation",
        message: `更新了角色 ${payload.name}。`,
      });
      return successResponse(null, "角色已更新");
    }

    roles = [
      {
        id: nextId(roles),
        created_at: new Date().toLocaleString("zh-CN", { hour12: false }),
        ...payload,
      },
      ...roles,
    ];
    pushLog({
      module: "system-role",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `创建了角色 ${payload.name}。`,
    });
    return successResponse(null, "角色已创建");
  },

  async deleteRole(id: number) {
    await wait();
    const target = roles.find((item) => item.id === id);
    roles = roles.filter((item) => item.id !== id);
    pushLog({
      module: "system-role",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `删除了角色 ${target?.name ?? id}。`,
    });
    return successResponse(null, "角色已删除");
  },

  async listMenus() {
    await wait();
    return successResponse<MenuItem[]>(menus);
  },

  async saveMenu(payload: MenuForm) {
    await wait();
    if (payload.id) {
      menus = menus.map((item) => (item.id === payload.id ? { ...item, ...payload } : item));
      pushLog({
        module: "system-menu",
        operator: "admin",
        result: "success",
        type: "operation",
        message: `更新了菜单 ${payload.name}。`,
      });
      return successResponse(null, "菜单已更新");
    }

    menus = [{ id: nextId(menus), ...payload }, ...menus];
    pushLog({
      module: "system-menu",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `新增了菜单 ${payload.name}。`,
    });
    return successResponse(null, "菜单已创建");
  },

  async deleteMenu(id: number) {
    await wait();
    const target = menus.find((item) => item.id === id);
    menus = menus.filter((item) => item.id !== id);
    pushLog({
      module: "system-menu",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `删除了菜单 ${target?.name ?? id}。`,
    });
    return successResponse(null, "菜单已删除");
  },

  async listConfigs(group?: ConfigRecord["group"]) {
    await wait();
    return successResponse(
      group ? configs.filter((item) => item.group === group) : configs,
    );
  },

  async saveConfig(payload: ConfigRecord) {
    await wait();
    configs = configs.map((item) =>
      item.id === payload.id
        ? {
            ...item,
            value: payload.value,
            description: payload.description,
            updated_at: new Date().toLocaleString("zh-CN", { hour12: false }),
          }
        : item,
    );
    pushLog({
      module: "system-config",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `更新了配置 ${payload.key}。`,
    });
    return successResponse(null, "配置已更新");
  },

  async listFiles(query: PaginationQuery & { file_type?: string }) {
    await wait();
    const filtered = applyKeywordFilter(files, query.keyword).filter((item) =>
      query.file_type ? item.file_type === query.file_type : true,
    );
    const { items, page, pageSize, total } = applyPagination(filtered, query);
    return {
      ...pagedResponse(items, page, pageSize),
      data: {
        items,
        page,
        page_size: pageSize,
        total,
      },
    };
  },

  async uploadFile(file: File) {
    await wait(500);

    const fileType = file.type.startsWith("image/")
      ? "image"
      : file.type.startsWith("audio/")
        ? "audio"
        : "video";

    const asset: FileAsset = {
      id: nextId(files),
      file_name: file.name,
      file_type: fileType,
      size_text: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
      source: "local-upload",
      status: "ready",
      url: URL.createObjectURL(file),
      created_at: new Date().toLocaleString("zh-CN", { hour12: false }),
    };

    files = [asset, ...files];
    pushLog({
      module: "file-upload",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `上传了文件 ${file.name}。`,
    });

    return successResponse(asset, "上传成功");
  },

  async listLogs(query: PaginationQuery & { type?: string }) {
    await wait();
    const filtered = applyKeywordFilter(logs, query.keyword).filter((item) =>
      query.type ? item.type === query.type : true,
    );
    const { items, page, pageSize, total } = applyPagination(filtered, query);
    return {
      ...pagedResponse(items, page, pageSize),
      data: {
        items,
        page,
        page_size: pageSize,
        total,
      },
    };
  },

  async listTasks(query: PaginationQuery & { status?: string }) {
    await wait();
    const filtered = applyKeywordFilter(tasks, query.keyword).filter((item) =>
      query.status ? item.status === query.status : true,
    );
    const { items, page, pageSize, total } = applyPagination(filtered, query);
    return {
      ...pagedResponse(items, page, pageSize),
      data: {
        items,
        page,
        page_size: pageSize,
        total,
      },
    };
  },

  async retryTask(id: number) {
    await wait();
    tasks = tasks.map((item) =>
      item.id === id
        ? {
            ...item,
            status: "running",
            retry_count: item.retry_count + 1,
            last_error: "",
            updated_at: new Date().toLocaleString("zh-CN", { hour12: false }),
          }
        : item,
    );
    pushLog({
      module: "task-retry",
      operator: "admin",
      result: "success",
      type: "operation",
      message: `重试任务 ${id}。`,
    });
    return successResponse(null, "任务已重新投递");
  },
};
