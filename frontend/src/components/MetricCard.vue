<script setup lang="ts">
defineProps<{
  label: string;
  value: string;
  hint: string;
  trend?: string;
}>();
</script>

<template>
  <el-card
    class="metric-card"
    shadow="never"
  >
    <div class="metric-card__body">
      <div class="metric-card__label">{{ label }}</div>
      <div class="metric-card__value">{{ value }}</div>
      <div class="metric-card__hint">{{ hint }}</div>
      <div
        v-if="trend"
        class="metric-card__trend"
      >
        {{ trend }}
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.metric-card {
  height: 100%;
  border: 1px solid var(--app-border);
  border-radius: 8px;
}

.metric-card__body {
  display: flex;
  min-height: 154px;
  flex-direction: column;
  gap: 12px;
}

.metric-card__label {
  color: var(--app-muted);
  font-size: 14px;
  font-weight: 600;
}

.metric-card__value {
  color: var(--app-text);
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.metric-card__hint {
  color: var(--app-muted);
  font-size: 14px;
  line-height: 1.6;
}

.metric-card__trend {
  color: var(--app-primary);
  font-size: 13px;
  font-weight: 600;
}
</style>
