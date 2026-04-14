import type { Directive } from "vue";

import { useAuthStore } from "@/stores/auth";
import { pinia } from "@/stores";

export const permissionDirective: Directive<HTMLElement, string | string[]> = {
  mounted(el, binding) {
    const authStore = useAuthStore(pinia);
    const required = Array.isArray(binding.value)
      ? binding.value
      : [binding.value];
    const allowed = required.some((permission) =>
      authStore.permissions.includes(permission),
    );

    if (!allowed) {
      el.remove();
    }
  },
};
