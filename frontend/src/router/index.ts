import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { pinia } from "@/stores";
import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/auth/LoginView.vue"),
    meta: { title: "登录" },
  },
  {
    path: "/",
    component: () => import("@/layout/AdminLayout.vue"),
    redirect: "/dashboard",
    children: [
      {
        path: "/dashboard",
        name: "dashboard",
        component: () => import("@/views/dashboard/DashboardView.vue"),
        meta: { title: "工作台", permission: "dashboard:view" },
      },
      {
        path: "/system/users",
        name: "system-users",
        component: () => import("@/views/system/UserView.vue"),
        meta: { title: "用户管理", permission: "system:user:list" },
      },
      {
        path: "/system/roles",
        name: "system-roles",
        component: () => import("@/views/system/RoleView.vue"),
        meta: { title: "角色管理", permission: "system:role:list" },
      },
      {
        path: "/system/menus",
        name: "system-menus",
        component: () => import("@/views/system/MenuView.vue"),
        meta: { title: "菜单管理", permission: "system:menu:list" },
      },
      {
        path: "/system/configs",
        name: "system-configs",
        component: () => import("@/views/system/ConfigView.vue"),
        meta: { title: "系统配置", permission: "system:config:list" },
      },
      {
        path: "/system/platform-accounts",
        name: "system-platform-accounts",
        component: () => import("@/views/system/PlatformAccountView.vue"),
        meta: { title: "平台账号", permission: "system:platform-account:list" },
      },
      {
        path: "/system/files",
        name: "system-files",
        component: () => import("@/views/assets/FileCenterView.vue"),
        meta: { title: "文件中心", permission: "system:file:upload" },
      },
      {
        path: "/assets/files",
        redirect: "/system/files",
      },
      {
        path: "/system/logs",
        name: "system-logs",
        component: () => import("@/views/system/LogsView.vue"),
        meta: { title: "日志中心", permission: "system:log:list" },
      },
      {
        path: "/system/tasks",
        name: "system-tasks",
        component: () => import("@/views/system/TasksView.vue"),
        meta: { title: "任务中心", permission: "system:task:list" },
      },
      {
        path: "/news",
        redirect: "/news/list",
      },
      {
        path: "/news/list",
        name: "news-list",
        component: () => import("@/views/news/NewsView.vue"),
        meta: { title: "新闻管理", permission: "news:list" },
      },
      {
        path: "/news/sources",
        name: "news-sources",
        component: () => import("@/views/news/NewsSourceView.vue"),
        meta: { title: "新闻源管理", permission: "news:source:list" },
      },
      {
        path: "/news/records",
        name: "news-records",
        component: () => import("@/views/news/NewsRecordView.vue"),
        meta: { title: "抓取记录", permission: "news:fetch-record:list" },
      },
    ],
  },
  {
    path: "/403",
    name: "forbidden",
    component: () => import("@/views/error/ForbiddenView.vue"),
    meta: { title: "无权限" },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("@/views/error/NotFoundView.vue"),
    meta: { title: "页面不存在" },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore(pinia);
  const appStore = useAppStore(pinia);

  if (to.path === "/login") {
    if (authStore.isLoggedIn) {
      next("/dashboard");
      return;
    }
    next();
    return;
  }

  if (!authStore.isLoggedIn) {
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`);
    return;
  }

  if (!authStore.user) {
    await authStore.fetchCurrentUser();
  }

  if (!appStore.menus.length) {
    await appStore.fetchMenus();
  }

  const permission = to.meta.permission as string | undefined;
  if (permission && !authStore.permissions.includes(permission) && !authStore.isSuperAdmin) {
    next("/403");
    return;
  }

  next();
});
