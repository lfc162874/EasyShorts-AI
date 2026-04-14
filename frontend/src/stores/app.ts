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
    menus.value = response.data.items;
  };

  return {
    sidebarCollapsed,
    menus,
    topMenus,
    toggleSidebar,
    fetchMenus,
  };
});
