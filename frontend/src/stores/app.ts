import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { listMenus } from "@/api/modules/system";
import type { MenuNode } from "@/types/system";

const sortMenus = (items: MenuNode[]): MenuNode[] =>
  [...items].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);

const collectChildPaths = (items: MenuNode[], paths = new Set<string>()): Set<string> => {
  for (const item of items) {
    if (item.children?.length) {
      collectChildPaths(item.children, paths);
    }
    if (item.parent_id !== null && item.path) {
      paths.add(item.path);
    }
  }
  return paths;
};

const menuTitleOverrides: Record<string, string> = {
  "/news/list": "内容中心",
  "/news/sources": "来源管理",
  "/news/records": "采集记录",
};

const adminPath = (path: string) => {
  if (path === "/dashboard") {
    return "/admin/dashboard";
  }
  if (path.startsWith("/system") || path.startsWith("/assets")) {
    return `/admin${path}`;
  }
  return path;
};

const shouldHideInAdmin = (path?: string | null) => {
  if (!path) {
    return false;
  }
  return (
    path.startsWith("/news") ||
    path.startsWith("/agent") ||
    path === "/sources" ||
    path === "/crawl-records" ||
    path === "/articles"
  );
};

const normalizeMenus = (items: MenuNode[]): MenuNode[] =>
  items.map((item) => {
    const children = normalizeMenus(item.children ?? []);
    const path = item.path ? adminPath(item.path) : item.path;
    const title = item.path ? (menuTitleOverrides[item.path] ?? item.title) : item.title;
    const hiddenByPath = shouldHideInAdmin(item.path);
    const visibleChildren = children.filter((child) => !child.hidden);
    const hidden =
      item.hidden ||
      hiddenByPath ||
      (item.menu_type === "DIRECTORY" && visibleChildren.length === 0);

    return {
      ...item,
      path,
      title,
      hidden,
      children,
    };
  });

export const useAppStore = defineStore("app", () => {
  const sidebarCollapsed = ref(false);
  const menus = ref<MenuNode[]>([]);

  const topMenus = computed(() => {
    const childPaths = collectChildPaths(menus.value);
    return sortMenus(
      menus.value.filter(
        (item) =>
          item.parent_id === null &&
          item.hidden === false &&
          (!item.path || !childPaths.has(item.path)),
      ),
    );
  });

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value;
  };

  const fetchMenus = async () => {
    const response = await listMenus();
    menus.value = normalizeMenus(response.data.items);
  };

  return {
    sidebarCollapsed,
    menus,
    topMenus,
    toggleSidebar,
    fetchMenus,
  };
});
