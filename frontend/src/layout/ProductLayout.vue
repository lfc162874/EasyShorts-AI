<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowDown } from "@element-plus/icons-vue";

import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const viewportWidth = ref(window.innerWidth);
const isMobile = computed(() => viewportWidth.value < 960);
const isHome = computed(() => route.path === "/");
const isHotMonitor = computed(() => route.path.startsWith("/news/hot-monitor"));
const isLandingLike = computed(() => isHome.value || isHotMonitor.value);
const showSmartNav = computed(
  () => (route.path.startsWith("/news") || route.path.startsWith("/agent")) && !isHotMonitor.value,
);

const activeTopNav = computed(() => {
  if (route.path.startsWith("/admin")) {
    return "/admin/dashboard";
  }
  if (isHotMonitor.value) {
    return "/news/hot-monitor";
  }
  if (showSmartNav.value) {
    return "/news/list";
  }
  return "/";
});

const activeSmartNav = computed(() => {
  if (route.path.startsWith("/news/hot-monitor")) {
    return "/news/hot-monitor";
  }
  if (route.path.startsWith("/news/sources")) {
    return "/news/sources";
  }
  if (route.path.startsWith("/news/records")) {
    return "/news/records";
  }
  if (route.path.startsWith("/news")) {
    return "/news/list";
  }
  if (route.path.startsWith("/agent/runs")) {
    return "/agent/runs";
  }
  if (route.path.startsWith("/agent/hot-topics")) {
    return "/agent/hot-topics";
  }
  if (route.path.startsWith("/agent/push-plans")) {
    return "/agent/push-plans";
  }
  if (route.path.startsWith("/agent/config")) {
    return "/agent/config";
  }
  return "/news/list";
});

const handleLogout = async () => {
  await authStore.logoutAction();
  await router.push("/login");
};

const handleResize = () => {
  viewportWidth.value = window.innerWidth;
};

onMounted(() => {
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
});
</script>

<template>
  <div
    class="product-theme"
    :class="{ 'product-theme--landing': isLandingLike }"
  >
    <el-container class="product-layout">
      <el-header class="product-layout__header">
        <div class="brand">
          <div class="brand__mark">ES</div>
          <div class="brand__text">
            <div class="brand__title">EasyShorts AI</div>
            <div class="brand__subtitle">智能处理平台</div>
          </div>
        </div>

        <el-menu
          v-if="!isMobile"
          mode="horizontal"
          :default-active="activeTopNav"
          router
          class="top-nav"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item
            index="/news/hot-monitor"
            v-permission="'news:list'"
          >
            AI热点监控
          </el-menu-item>
          <el-menu-item
            index="/news/list"
            v-permission="['news:list','agent:run:list','agent:hot-topic:list','agent:push-plan:list','agent:config:list']"
          >
            智能处理
          </el-menu-item>
          <el-menu-item
            index="/admin/dashboard"
            v-permission="['dashboard:view','system:user:list','system:role:list','system:menu:list','system:config:list']"
          >
            后台管理
          </el-menu-item>
        </el-menu>

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
              <el-dropdown-item @click="router.push('/')">回到首页</el-dropdown-item>
              <el-dropdown-item @click="router.push('/admin/dashboard')">后台管理</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-container class="product-layout__body">
        <el-aside
          v-if="showSmartNav && !isMobile"
          width="260px"
          class="product-layout__aside"
        >
          <div class="aside-header">
            <div class="aside-title">智能处理</div>
            <div class="aside-subtitle">内容→Agent→热点→推送</div>
          </div>

          <el-scrollbar class="aside-nav">
            <el-menu
              :default-active="activeSmartNav"
              router
              class="smart-menu"
            >
              <el-menu-item
                index="/news/list"
                v-permission="'news:list'"
              >
                内容中心
              </el-menu-item>
              <el-menu-item
                index="/news/hot-monitor"
                v-permission="'news:list'"
              >
                AI热点监控
              </el-menu-item>
              <el-menu-item
                index="/news/sources"
                v-permission="'news:source:list'"
              >
                来源管理
              </el-menu-item>
              <el-menu-item
                index="/news/records"
                v-permission="'news:fetch-record:list'"
              >
                采集记录
              </el-menu-item>
              <el-menu-item
                index="/agent/runs"
                v-permission="'agent:run:list'"
              >
                运行中心
              </el-menu-item>
              <el-menu-item
                index="/agent/hot-topics"
                v-permission="'agent:hot-topic:list'"
              >
                热点池
              </el-menu-item>
              <el-menu-item
                index="/agent/push-plans"
                v-permission="'agent:push-plan:list'"
              >
                推送计划
              </el-menu-item>
              <el-menu-item
                index="/agent/config"
                v-permission="'agent:config:list'"
              >
                模型配置
              </el-menu-item>
            </el-menu>
          </el-scrollbar>
        </el-aside>

        <el-main class="product-layout__main">
          <div class="product-layout__content">
            <div
              class="product-surface"
              :class="{ 'product-surface--home': isLandingLike }"
            >
              <router-view />
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped lang="scss">
.product-theme {
  --app-bg: #f4f7fb;
  --app-surface: rgba(255, 255, 255, 0.92);
  --app-surface-strong: rgba(255, 255, 255, 0.96);
  --app-border: rgba(148, 163, 184, 0.28);
  --app-text: #0b1220;
  --app-muted: rgba(71, 85, 105, 0.9);
  --app-primary: #7c3aed;
  --app-primary-strong: #6d28d9;
  --el-color-primary: #7c3aed;
  --el-color-primary-dark-2: #6d28d9;
  --el-color-primary-light-3: #9b6ef2;
  --el-color-primary-light-5: #b894f7;
  --el-color-primary-light-7: #d8c4fb;
  --el-color-primary-light-8: #e8dcfd;
  --el-color-primary-light-9: #f4efff;
  min-height: 100vh;
  background:
    radial-gradient(circle at 16% 6%, rgba(124, 58, 237, 0.08) 0%, transparent 52%),
    radial-gradient(circle at 92% 16%, rgba(34, 211, 238, 0.06) 0%, transparent 52%),
    radial-gradient(circle at 44% 96%, rgba(236, 72, 153, 0.05) 0%, transparent 56%),
    linear-gradient(180deg, #f6f8fc 0%, #f4f7fb 60%, #f6f8fc 100%);
}

.product-theme--landing {
  --app-bg: #050814;
  --app-border: rgba(148, 163, 184, 0.22);
  background:
    radial-gradient(circle at 12% 12%, rgba(124, 58, 237, 0.28) 0%, transparent 46%),
    radial-gradient(circle at 88% 22%, rgba(34, 211, 238, 0.14) 0%, transparent 46%),
    radial-gradient(circle at 38% 92%, rgba(236, 72, 153, 0.12) 0%, transparent 50%),
    linear-gradient(180deg, #050814 0%, #070a18 55%, #050814 100%);
}

.product-layout {
  height: 100vh;
}

.product-layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  height: 74px;
  padding: 0 22px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
}

.product-theme--landing .product-layout__header {
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(5, 8, 20, 0.78);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand__mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 12px;
  background: rgba(124, 58, 237, 0.12);
  color: rgba(124, 58, 237, 0.92);
  font-size: 14px;
  font-weight: 700;
}

.product-theme--landing .brand__mark {
  background:
    radial-gradient(circle at 30% 30%, rgba(124, 58, 237, 0.44) 0%, rgba(124, 58, 237, 0.14) 55%),
    radial-gradient(circle at 70% 70%, rgba(34, 211, 238, 0.22) 0%, rgba(34, 211, 238, 0.06) 60%);
  color: rgba(255, 255, 255, 0.94);
}

.brand__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand__title {
  color: rgba(15, 23, 42, 0.92);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
}

.product-theme--landing .brand__title {
  color: rgba(255, 255, 255, 0.92);
}

.brand__subtitle {
  color: rgba(71, 85, 105, 0.78);
  font-size: 12px;
}

.product-theme--landing .brand__subtitle {
  color: rgba(226, 232, 240, 0.7);
}

.top-nav {
  flex: 1;
  justify-content: center;
  background: transparent;
  border-bottom: 0;
}

:deep(.top-nav.el-menu--horizontal) {
  border-bottom: 0;
}

:deep(.top-nav .el-menu-item) {
  height: 46px;
  margin: 0 6px;
  border-radius: 999px;
  color: rgba(71, 85, 105, 0.9);
}

:deep(.product-theme--landing .top-nav .el-menu-item) {
  color: rgba(226, 232, 240, 0.86);
}

:deep(.top-nav .el-menu-item.is-active) {
  background: rgba(124, 58, 237, 0.14);
  color: rgba(109, 40, 217, 0.98);
}

:deep(.product-theme--landing .top-nav .el-menu-item.is-active) {
  background: rgba(124, 58, 237, 0.18);
  color: rgba(255, 255, 255, 0.96);
}

:deep(.top-nav .el-menu-item:not(.is-active):hover) {
  background: rgba(148, 163, 184, 0.16);
  color: rgba(15, 23, 42, 0.92);
}

:deep(.product-theme--landing .top-nav .el-menu-item:not(.is-active):hover) {
  background: rgba(148, 163, 184, 0.12);
  color: rgba(255, 255, 255, 0.92);
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  cursor: pointer;
}

.product-theme--landing .user-chip {
  background: rgba(15, 23, 42, 0.58);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.28);
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
  color: rgba(15, 23, 42, 0.92);
  font-size: 14px;
  font-weight: 600;
}

.product-theme--landing .user-chip__name {
  color: rgba(255, 255, 255, 0.92);
}

.user-chip__role {
  color: rgba(71, 85, 105, 0.76);
  font-size: 12px;
}

.product-theme--landing .user-chip__role {
  color: rgba(226, 232, 240, 0.7);
}

.product-layout__body {
  min-width: 0;
  min-height: 0;
}

.product-layout__aside {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 74px);
  overflow: hidden;
  padding: 18px 16px 22px;
  border-right: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(16px);
}

.product-theme--landing .product-layout__aside {
  border-right: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(5, 8, 20, 0.68);
}

.aside-header {
  padding: 12px 12px 14px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.86);
}

.product-theme--landing .aside-header {
  background: rgba(15, 23, 42, 0.46);
}

.aside-title {
  color: rgba(15, 23, 42, 0.92);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
}

.product-theme--landing .aside-title {
  color: rgba(255, 255, 255, 0.92);
}

.aside-subtitle {
  margin-top: 6px;
  color: rgba(71, 85, 105, 0.72);
  font-size: 12px;
}

.product-theme--landing .aside-subtitle {
  color: rgba(226, 232, 240, 0.68);
}

.aside-nav {
  flex: 1;
  min-height: 0;
  margin-top: 14px;
}

.smart-menu {
  background: transparent;
  border-right: 0;
}

:deep(.smart-menu .el-menu-item) {
  height: 44px;
  margin-bottom: 8px;
  border-radius: 14px;
  color: rgba(71, 85, 105, 0.9);
}

:deep(.product-theme--landing .smart-menu .el-menu-item) {
  color: rgba(226, 232, 240, 0.86);
}

:deep(.smart-menu .el-menu-item.is-active) {
  background: rgba(124, 58, 237, 0.14);
  color: rgba(109, 40, 217, 0.98);
}

:deep(.product-theme--landing .smart-menu .el-menu-item.is-active) {
  background: rgba(124, 58, 237, 0.18);
  color: rgba(255, 255, 255, 0.96);
}

:deep(.smart-menu .el-menu-item:not(.is-active):hover) {
  background: rgba(148, 163, 184, 0.16);
  color: rgba(15, 23, 42, 0.92);
}

:deep(.product-theme--landing .smart-menu .el-menu-item:not(.is-active):hover) {
  background: rgba(148, 163, 184, 0.12);
  color: rgba(255, 255, 255, 0.92);
}

.product-layout__main {
  overflow: auto;
  min-width: 0;
  min-height: 0;
  padding: 20px 22px 30px;
  background: transparent;
}

.product-layout__content {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.product-surface {
  padding: 18px;
}

.product-surface--home {
  padding: 0;
}

:deep(.product-theme:not(.product-theme--landing) .el-card) {
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.92);
  box-shadow:
    0 10px 30px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

:deep(.product-theme:not(.product-theme--landing) .el-card__body) {
  padding: 18px;
}

:deep(.product-theme:not(.product-theme--landing) .page-shell) {
  gap: 14px;
}

:deep(.product-theme:not(.product-theme--landing) .page-header) {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.92);
  box-shadow:
    0 10px 30px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

:deep(.product-theme:not(.product-theme--landing) .page-title) {
  font-size: 22px;
}
</style>
