<script setup lang="ts">
import { computed } from "vue";
import {
  Collection,
  Connection,
  DataLine,
  Document,
  FolderOpened,
  Link,
  Menu as MenuIcon,
  Operation,
  Position,
  Platform,
  Cpu,
  Setting,
  User,
  UserFilled,
  TrendCharts,
  VideoCamera,
} from "@element-plus/icons-vue";

import type { MenuNode } from "@/types/system";

const props = defineProps<{
  menus: MenuNode[];
}>();

const visibleMenus = computed(() =>
  [...props.menus]
    .filter((menu) => !menu.hidden)
    .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id),
);

const iconMap: Record<string, unknown> = {
  dashboard: DataLine,
  system: Setting,
  users: User,
  user: User,
  roles: UserFilled,
  role: UserFilled,
  menus: MenuIcon,
  menu: MenuIcon,
  configs: Setting,
  config: Setting,
  platform: Platform,
  "platform-accounts": Platform,
  logs: Document,
  tasks: Operation,
  files: FolderOpened,
  file: FolderOpened,
  video: VideoCamera,
  videos: VideoCamera,
  collection: Collection,
  link: Link,
  cpu: Cpu,
  connection: Connection,
  "trend-charts": TrendCharts,
  position: Position,
};

const resolveIcon = (icon?: string | null) => iconMap[icon?.toLowerCase() ?? ""] ?? MenuIcon;

const isDirectory = (menu: MenuNode) =>
  menu.menu_type === "DIRECTORY" || (menu.children?.length ?? 0) > 0;
</script>

<template>
  <template
    v-for="menu in visibleMenus"
    :key="menu.id"
  >
    <el-sub-menu
      v-if="isDirectory(menu)"
      :index="menu.path || `menu-${menu.id}`"
    >
      <template #title>
        <el-icon><component :is="resolveIcon(menu.icon)" /></el-icon>
        <span>{{ menu.title }}</span>
      </template>
      <SidebarMenuTree :menus="menu.children" />
    </el-sub-menu>

    <el-menu-item
      v-else
      :index="menu.path || `menu-${menu.id}`"
    >
      <el-icon><component :is="resolveIcon(menu.icon)" /></el-icon>
      <span>{{ menu.title }}</span>
    </el-menu-item>
  </template>
</template>
