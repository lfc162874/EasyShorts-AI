<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { formatJson } from "@/utils/format";

const props = defineProps<{
  title: string;
  contentText?: string | null;
  contentJson?: unknown;
  emptyText?: string;
}>();

const hasText = computed(() => Boolean(props.contentText && props.contentText.trim()));
const hasJson = computed(() => props.contentJson !== null && props.contentJson !== undefined);
const hasMultiple = computed(() => hasText.value && hasJson.value);
const activeTab = ref<"json" | "text">(hasJson.value ? "json" : "text");

watch([hasText, hasJson], ([text, json]) => {
  if (json && !text) {
    activeTab.value = "json";
  }
  if (text && !json) {
    activeTab.value = "text";
  }
});
</script>

<template>
  <el-card
    shadow="never"
    class="artifact-viewer"
  >
    <template #header>
      <div class="artifact-viewer__header">
        <span>{{ title }}</span>
      </div>
    </template>

    <div v-if="hasMultiple">
      <el-tabs
        v-model="activeTab"
        class="artifact-viewer__tabs"
      >
        <el-tab-pane
          label="结构化"
          name="json"
        >
          <pre class="news-pre">{{ formatJson(contentJson) }}</pre>
        </el-tab-pane>
        <el-tab-pane
          label="文本"
          name="text"
        >
          <div class="news-block">{{ contentText }}</div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template v-else-if="hasJson">
      <pre class="news-pre">{{ formatJson(contentJson) }}</pre>
    </template>

    <template v-else-if="hasText">
      <div class="news-block">{{ contentText }}</div>
    </template>

    <div
      v-else
      class="empty-helper"
    >
      {{ emptyText ?? "暂无内容" }}
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.artifact-viewer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.artifact-viewer__tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}
</style>
