<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowDown, Fold, Expand } from "@element-plus/icons-vue";

import SidebarMenuTree from "@/components/SidebarMenuTree.vue";
import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

const appStore = useAppStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const viewportWidth = ref(window.innerWidth);

const activePath = computed(() => route.path);
const breadcrumbs = computed(() =>
  route.matched
    .filter((item) => item.meta.title)
    .map((item) => item.meta.title as string),
);
const sidebarCollapsed = computed(() => appStore.sidebarCollapsed || viewportWidth.value < 960);

const handleLogout = async () => {
  await authStore.logoutAction();
  await router.push("/login");
};

const handleResize = () => {
  viewportWidth.value = window.innerWidth;
};

onMounted(async () => {
  window.addEventListener("resize", handleResize);
  if (!appStore.menus.length) {
    await appStore.fetchMenus();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
});
</script>

<template>
  <el-container class="admin-layout">
    <el-aside
      :width="sidebarCollapsed ? '84px' : '260px'"
      class="admin-layout__aside"
    >
      <div class="brand">
        <div class="brand__mark">ES</div>
        <div
          v-if="!sidebarCollapsed"
          class="brand__text"
        >
          <div class="brand__title">EasyShorts AI</div>
          <div class="brand__subtitle">管理后台</div>
        </div>
      </div>

      <el-scrollbar class="admin-layout__nav">
        <el-menu
          :collapse="sidebarCollapsed"
          :collapse-transition="false"
          :default-active="activePath"
          :unique-opened="true"
          background-color="transparent"
          text-color="var(--app-sidebar-text)"
          active-text-color="#ffffff"
          router
          class="admin-menu"
        >
          <SidebarMenuTree :menus="appStore.topMenus" />
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container class="admin-layout__body">
      <el-header class="admin-layout__header">
        <div class="header-left">
          <el-button
            circle
            text
            @click="appStore.toggleSidebar()"
          >
            <el-icon><component :is="sidebarCollapsed ? Expand : Fold" /></el-icon>
          </el-button>

          <el-breadcrumb
            separator="/"
            class="header-breadcrumb"
          >
            <el-breadcrumb-item
              v-for="breadcrumb in breadcrumbs"
              :key="breadcrumb"
            >
              {{ breadcrumb }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <el-dropdown trigger="click">
          <div class="user-chip">
            <el-avatar
              size="small"
              class="user-chip__avatar"
            >
              {{ authStore.user?.nickname?.slice(0, 1) ?? "A" }}
            </el-avatar>
            <div class="user-chip__meta">
              <div class="user-chip__name">
                {{ authStore.user?.nickname ?? "未登录" }}
              </div>
              <div class="user-chip__role">
                {{ authStore.user?.roles?.map((role) => role.name).join(" / ") ?? "-" }}
              </div>
            </div>
            <el-icon><ArrowDown /></el-icon>
          </div>

          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="admin-layout__main">
        <div class="admin-layout__content">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped lang="scss">
.admin-layout {
  height: 100vh;
  background: var(--app-bg);
}

.admin-layout__aside {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background:
    linear-gradient(180deg, var(--app-sidebar-bg) 0%, var(--app-sidebar-bg-strong) 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.14);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 72px;
  padding: 18px 18px 18px 20px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.brand__mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 10px;
  background: rgba(31, 157, 98, 0.14);
  color: #d1fae5;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0;
}

.brand__text {
  min-width: 0;
}

.brand__title {
  color: #f8fafc;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
}

.brand__subtitle {
  margin-top: 4px;
  color: var(--app-sidebar-muted);
  font-size: 12px;
}

.admin-layout__nav {
  flex: 1;
  min-height: 0;
  padding: 14px 12px 18px;
}

.admin-menu {
  border-right: 0;
}

:deep(.el-menu) {
  border-right: 0;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  height: 44px;
  margin-bottom: 6px;
  border-radius: 8px;
  line-height: 44px;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.06);
}

:deep(.el-menu-item.is-active) {
  background: rgba(31, 157, 98, 0.18);
  color: #ffffff;
}

:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  margin-right: 10px;
  color: var(--app-sidebar-muted);
}

:deep(.el-menu-item.is-active .el-icon),
:deep(.el-sub-menu.is-active > .el-sub-menu__title .el-icon) {
  color: #d1fae5;
}

.admin-layout__body {
  min-width: 0;
}

.admin-layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 68px;
  padding: 0 24px 0 28px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.header-breadcrumb {
  min-width: 0;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  cursor: pointer;
}

.user-chip__avatar {
  flex-shrink: 0;
}

.user-chip__meta {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.user-chip__name {
  color: var(--app-text);
  font-size: 14px;
  font-weight: 600;
}

.user-chip__role {
  color: var(--app-muted);
  font-size: 12px;
}

.admin-layout__main {
  overflow: auto;
  padding: 24px 28px 32px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.72) 0%, rgba(244, 247, 251, 1) 100%);
}

.admin-layout__content {
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
}
</style>
