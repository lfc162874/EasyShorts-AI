<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";

import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const formRef = ref<FormInstance>();
const form = reactive({
  username: "admin",
  password: "Admin@123456",
});

const rules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  loading.value = true;
  try {
    await authStore.loginAction(form);
    ElMessage.success("登录成功");
    const redirect = (route.query.redirect as string) || "/";
    await router.push(redirect);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="login-page">
    <div class="login-copy">
      <div class="login-badge">AI Hotspot Monitor</div>
      <h1>AI 热点监控助手后台</h1>
      <p>
        现在接入真实后端接口，先把来源管理、采集记录、内容中心与后续处理链路跑通。
      </p>

      <div class="login-panel">
        <div class="login-panel-item">
          <div class="label">默认账号</div>
          <div class="value mono-text">admin / Admin@123456</div>
        </div>
        <div class="login-panel-item">
          <div class="label">角色</div>
          <div class="value">超级管理员</div>
        </div>
        <div class="login-panel-item">
          <div class="label">接口模式</div>
          <div class="value">真实后端接口 /easy-shorts</div>
        </div>
      </div>
    </div>

    <el-card
      class="login-card"
      shadow="never"
    >
      <template #header>
        <div>
          <div class="login-card-title">账号登录</div>
          <div class="login-card-subtitle">登录后进入采集与热点分析后台</div>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item
          label="用户名"
          prop="username"
        >
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
          />
        </el-form-item>

        <el-form-item
          label="密码"
          prop="password"
        >
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            size="large"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          style="width: 100%; margin-top: 8px"
          @click="handleLogin"
        >
          进入系统
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  align-items: center;
  padding: 48px;
  gap: 48px;
}

.login-copy h1 {
  margin: 18px 0 12px;
  color: #162033;
  font-size: 48px;
  line-height: 1.1;
}

.login-copy p {
  max-width: 640px;
  margin: 0;
  color: #546179;
  font-size: 17px;
}

.login-badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(32, 159, 92, 0.12);
  color: #15814f;
  font-size: 13px;
  font-weight: 700;
}

.login-panel {
  margin-top: 32px;
  display: grid;
  gap: 14px;
}

.login-panel-item {
  padding: 16px 18px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #e5ebf4;
}

.label {
  color: #6f7b91;
  font-size: 13px;
}

.value {
  margin-top: 6px;
  color: #18212f;
  font-size: 16px;
  font-weight: 600;
}

.login-card {
  width: 100%;
  max-width: 420px;
  justify-self: end;
  border: 1px solid #e7edf5;
}

.login-card-title {
  color: #162033;
  font-size: 22px;
  font-weight: 700;
}

.login-card-subtitle {
  margin-top: 6px;
  color: #677389;
  font-size: 14px;
}
</style>
