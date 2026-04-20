<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();
</script>

<template>
  <div class="error-page">
    <el-result
      icon="warning"
      title="无权限访问"
      sub-title="当前账号没有打开这个页面的权限，请切换账号或补充角色权限。"
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
