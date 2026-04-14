<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <div class="page-header">
    <div>
      <h1 class="page-title">{{ title }}</h1>
      <p
        v-if="description"
        class="page-subtitle"
      >
        {{ description }}
      </p>
    </div>
    <div class="page-actions">
      <slot />
    </div>
  </div>
</template>

<style scoped lang="scss">
.page-header {
  padding-top: 2px;
}

.page-actions {
  justify-content: flex-end;
}
</style>
