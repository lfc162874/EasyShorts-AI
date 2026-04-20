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
    component: () => import("@/layout/ProductLayout.vue"),
    children: [
      {
        path: "",
        name: "home",
        component: () => import("@/views/product/ProductHomeView.vue"),
        meta: { title: "首页" },
      },
      {
        path: "/news",
        redirect: "/news/list",
      },
      {
        path: "/news/list",
        name: "news-list",
        component: () => import("@/views/news/NewsView.vue"),
        meta: { title: "内容中心", permission: "news:list" },
      },
      {
        path: "/news/hot-monitor",
        name: "news-hot-monitor",
        component: () => import("@/views/news/AiHotMonitorView.vue"),
        meta: { title: "AI热点监控", permission: "news:list" },
      },
      {
        path: "/news/sources",
        name: "news-sources",
        component: () => import("@/views/news/NewsSourceView.vue"),
        meta: { title: "来源管理", permission: "news:source:list" },
      },
      {
        path: "/news/sources/:id",
        name: "news-source-detail",
        component: () => import("@/views/news/NewsSourceDetailView.vue"),
        meta: { title: "来源详情", permission: "news:source:list" },
      },
      {
        path: "/news/records",
        name: "news-records",
        component: () => import("@/views/news/NewsRecordView.vue"),
        meta: { title: "采集记录", permission: "news:fetch-record:list" },
      },
      {
        path: "/agent",
        redirect: "/agent/runs",
      },
      {
        path: "/agent/runs",
        name: "agent-runs",
        component: () => import("@/views/agent/AgentRunView.vue"),
        meta: { title: "Agent运行", permission: "agent:run:list" },
      },
      {
        path: "/agent/runs/:id",
        name: "agent-run-detail",
        component: () => import("@/views/agent/AgentRunDetailView.vue"),
        meta: { title: "运行详情", permission: "agent:run:list" },
      },
      {
        path: "/agent/hot-topics",
        name: "agent-hot-topics",
        component: () => import("@/views/agent/HotTopicView.vue"),
        meta: { title: "热点池", permission: "agent:hot-topic:list" },
      },
      {
        path: "/agent/hot-topics/:id",
        name: "agent-hot-topic-detail",
        component: () => import("@/views/agent/HotTopicDetailView.vue"),
        meta: { title: "热点详情", permission: "agent:hot-topic:list" },
      },
      {
        path: "/agent/push-plans",
        name: "agent-push-plans",
        component: () => import("@/views/agent/PushPlanView.vue"),
        meta: { title: "推送计划", permission: "agent:push-plan:list" },
      },
      {
        path: "/agent/push-plans/:id",
        name: "agent-push-plan-detail",
        component: () => import("@/views/agent/PushPlanDetailView.vue"),
        meta: { title: "推送详情", permission: "agent:push-plan:list" },
      },
      {
        path: "/agent/config",
        name: "agent-config",
        component: () => import("@/views/agent/AgentConfigView.vue"),
        meta: { title: "模型配置", permission: "agent:config:list" },
      },
      {
        path: "/sources",
        redirect: "/news/sources",
      },
      {
        path: "/crawl-records",
        redirect: "/news/records",
      },
      {
        path: "/articles",
        redirect: "/news/list",
      },
    ],
  },
  {
    path: "/admin",
    component: () => import("@/layout/AdminLayout.vue"),
    redirect: "/admin/dashboard",
    children: [
      {
        path: "dashboard",
        name: "admin-dashboard",
        component: () => import("@/views/dashboard/DashboardView.vue"),
        meta: { title: "工作台", permission: "dashboard:view" },
      },
      {
        path: "system/users",
        name: "system-users",
        component: () => import("@/views/system/UserView.vue"),
        meta: { title: "用户管理", permission: "system:user:list" },
      },
      {
        path: "system/roles",
        name: "system-roles",
        component: () => import("@/views/system/RoleView.vue"),
        meta: { title: "角色管理", permission: "system:role:list" },
      },
      {
        path: "system/menus",
        name: "system-menus",
        component: () => import("@/views/system/MenuView.vue"),
        meta: { title: "菜单管理", permission: "system:menu:list" },
      },
      {
        path: "system/configs",
        name: "system-configs",
        component: () => import("@/views/system/ConfigView.vue"),
        meta: { title: "系统配置", permission: "system:config:list" },
      },
      {
        path: "system/platform-accounts",
        name: "system-platform-accounts",
        component: () => import("@/views/system/PlatformAccountView.vue"),
        meta: { title: "平台账号", permission: "system:platform-account:list" },
      },
      {
        path: "system/files",
        name: "system-files",
        component: () => import("@/views/assets/FileCenterView.vue"),
        meta: { title: "文件中心", permission: "system:file:upload" },
      },
      {
        path: "assets/files",
        redirect: "/admin/system/files",
      },
      {
        path: "system/logs",
        name: "system-logs",
        component: () => import("@/views/system/LogsView.vue"),
        meta: { title: "日志中心", permission: "system:log:list" },
      },
      {
        path: "system/tasks",
        name: "system-tasks",
        component: () => import("@/views/system/TasksView.vue"),
        meta: { title: "任务中心", permission: "system:task:list" },
      },
    ],
  },
  {
    path: "/dashboard",
    redirect: "/admin/dashboard",
  },
  {
    path: "/system/:pathMatch(.*)*",
    redirect: (to) => {
      const rest = Array.isArray(to.params.pathMatch)
        ? to.params.pathMatch.join("/")
        : (to.params.pathMatch as string);
      return `/admin/system/${rest}`;
    },
  },
  {
    path: "/assets/:pathMatch(.*)*",
    redirect: (to) => {
      const rest = Array.isArray(to.params.pathMatch)
        ? to.params.pathMatch.join("/")
        : (to.params.pathMatch as string);
      return `/admin/assets/${rest}`;
    },
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
      next("/");
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
    try {
      await authStore.fetchCurrentUser();
    } catch {
      next(`/login?redirect=${encodeURIComponent(to.fullPath)}`);
      return;
    }
  }

  if (to.path.startsWith("/admin") && !appStore.menus.length) {
    try {
      await appStore.fetchMenus();
    } catch {
      next(`/login?redirect=${encodeURIComponent(to.fullPath)}`);
      return;
    }
  }

  const permission = to.meta.permission as string | undefined;
  if (permission && !authStore.permissions.includes(permission) && !authStore.isSuperAdmin) {
    next("/403");
    return;
  }

  next();
});
