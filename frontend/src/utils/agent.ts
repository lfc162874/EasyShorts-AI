import type { AgentModelItem } from "@/types/agent";

export const resolveAgentModelOptions = (
  items: AgentModelItem[] | null | undefined,
  fallbackModels: string[] = [],
): AgentModelItem[] => {
  const merged = new Map<string, AgentModelItem>();

  (items ?? []).forEach((item) => {
    if (!item?.value) {
      return;
    }
    merged.set(item.value, {
      value: item.value,
      label: item.label || item.value,
      is_default: Boolean(item.is_default),
    });
  });

  fallbackModels.forEach((value) => {
    if (!value || merged.has(value)) {
      return;
    }
    merged.set(value, {
      value,
      label: value,
      is_default: false,
    });
  });

  return [...merged.values()];
};

export const resolveDefaultAgentModel = (
  items: AgentModelItem[],
  preferred?: string | null,
): string => {
  if (preferred && items.some((item) => item.value === preferred)) {
    return preferred;
  }

  return items.find((item) => item.is_default)?.value || items[0]?.value || "";
};
