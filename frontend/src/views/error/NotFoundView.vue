<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();
</script>

<template>
  <div class="error-page">
    <el-result
      icon="info"
      title="页面不存在"
      sub-title="这个地址还没有对应页面，或者你刚刚敲错了一个字母。"
    >
      <template #extra>
        <el-button
          type="primary"
          @click="router.push('/')"
        >
          回到首页
        </el-button>
      </template>
    </el-result>
  </div>
</template>

<style scoped>
.error-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
}
</style>
