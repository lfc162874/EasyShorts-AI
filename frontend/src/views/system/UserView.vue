<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { listRoles, listUsers, saveUser } from "@/api/modules/system";
import { userStatusOptions } from "@/constants/permissions";
import type { RoleItem, UserProfile, UserUpsertForm } from "@/types/system";

const loading = ref(false);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const users = ref<UserProfile[]>([]);
const roles = ref<RoleItem[]>([]);
const total = ref(0);
const query = reactive({
  page: 1,
  page_size: 20,
});

const form = reactive<UserUpsertForm>({
  username: "",
  password: "",
  email: "",
  phone: "",
  nickname: "",
  role_ids: [],
  is_superuser: false,
  status: "ACTIVE",
});

const rules: FormRules<UserUpsertForm> = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  role_ids: [{ required: true, message: "请选择角色", trigger: "change" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }],
};

const dialogTitle = computed(() =>
  mode.value === "create" ? "新增用户" : "编辑用户",
);

const resetForm = () => {
  editingId.value = null;
  form.username = "";
  form.password = "";
  form.email = "";
  form.phone = "";
  form.nickname = "";
  form.role_ids = [];
  form.is_superuser = false;
  form.status = "ACTIVE";
};

const loadUsers = async () => {
  loading.value = true;
  try {
    const response = await listUsers(query);
    users.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const loadRoles = async () => {
  const response = await listRoles();
  roles.value = response.data.items;
};

const openCreate = () => {
  mode.value = "create";
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row: UserProfile) => {
  mode.value = "edit";
  editingId.value = row.id;
  form.username = row.username;
  form.password = "";
  form.email = row.email ?? "";
  form.phone = row.phone ?? "";
  form.nickname = row.nickname ?? "";
  form.role_ids = row.roles.map((role) => role.id);
  form.is_superuser = row.is_superuser;
  form.status = row.status;
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (mode.value === "create" && !form.password) {
    ElMessage.warning("请输入初始密码");
    return;
  }
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const payload: UserUpsertForm =
    mode.value === "create"
      ? {
          username: form.username,
          password: form.password,
          email: form.email || null,
          phone: form.phone || null,
          nickname: form.nickname || null,
          role_ids: form.role_ids,
          is_superuser: form.is_superuser,
          status: form.status,
        }
      : {
          id: editingId.value ?? undefined,
          password: form.password || undefined,
          email: form.email || null,
          phone: form.phone || null,
          nickname: form.nickname || null,
          role_ids: form.role_ids,
          is_superuser: form.is_superuser,
          status: form.status,
        };

  await saveUser(payload);
  ElMessage.success(mode.value === "create" ? "用户已创建" : "用户已更新");
  dialogVisible.value = false;
  await loadUsers();
};

onMounted(async () => {
  await Promise.all([loadUsers(), loadRoles()]);
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="用户管理"
      description="后端已经提供用户列表、新建和更新接口，这里直接按真实字段维护账号与角色。"
    >
      <el-button
        v-permission="'system:user:list'"
        type="primary"
        @click="openCreate"
      >
        新增用户
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="users"
      >
        <el-table-column
          prop="username"
          label="用户名"
          min-width="160"
        />
        <el-table-column
          prop="nickname"
          label="昵称"
          min-width="160"
        />
        <el-table-column
          prop="email"
          label="邮箱"
          min-width="200"
        />
        <el-table-column
          prop="phone"
          label="手机号"
          min-width="140"
        />
        <el-table-column
          label="角色"
          min-width="220"
        >
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role.id"
              effect="plain"
              style="margin-right: 8px"
            >
              {{ role.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="超级管理员"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.is_superuser ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
        <el-table-column
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column
          prop="last_login_at"
          label="最近登录"
          min-width="180"
        />
        <el-table-column
          prop="created_at"
          label="创建时间"
          min-width="180"
        />
        <el-table-column
          prop="updated_at"
          label="更新时间"
          min-width="180"
        />
        <el-table-column
          label="操作"
          width="120"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-permission="'system:user:list'"
              link
              type="primary"
              @click="openEdit(row)"
            >
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          layout="total, prev, pager, next"
          :total="total"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="720px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <div class="form-grid">
          <el-form-item
            label="用户名"
            prop="username"
          >
            <el-input
              v-model="form.username"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
          <el-form-item
            label="初始密码"
            prop="password"
          >
            <el-input
              v-model="form.password"
              type="password"
              show-password
              :placeholder="mode === 'create' ? '请输入初始密码' : '留空表示不修改'"
            />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="邮箱">
            <el-input v-model="form.email" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.phone" />
          </el-form-item>
        </div>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item
          label="角色"
          prop="role_ids"
        >
          <el-select
            v-model="form.role_ids"
            multiple
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="超级管理员">
            <el-switch v-model="form.is_superuser" />
          </el-form-item>
          <el-form-item
            label="状态"
            prop="status"
          >
            <el-select
              v-model="form.status"
              style="width: 100%"
            >
              <el-option
                v-for="option in userStatusOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
