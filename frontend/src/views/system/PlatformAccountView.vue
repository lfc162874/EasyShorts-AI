<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { platformAuthStatusOptions } from "@/constants/permissions";
import { listPlatformAccounts, savePlatformAccount } from "@/api/modules/system";
import type {
  PlatformAccountItem,
  PlatformAccountUpsertForm,
} from "@/types/system";

const loading = ref(false);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const accounts = ref<PlatformAccountItem[]>([]);
const extraText = ref("{}");

const form = reactive<PlatformAccountUpsertForm>({
  platform: "",
  display_name: "",
  account_id: "",
  auth_status: "UNAUTHORIZED",
  access_token: "",
  refresh_token: "",
  expires_at: "",
  extra: {},
  is_enabled: true,
});

const rules: FormRules<PlatformAccountUpsertForm> = {
  platform: [{ required: true, message: "请输入平台标识", trigger: "blur" }],
  display_name: [{ required: true, message: "请输入展示名称", trigger: "blur" }],
  account_id: [{ required: true, message: "请输入账号 ID", trigger: "blur" }],
  auth_status: [{ required: true, message: "请选择授权状态", trigger: "change" }],
};

const dialogTitle = computed(() =>
  mode.value === "create" ? "新增平台账号" : "编辑平台账号",
);

const resetForm = () => {
  editingId.value = null;
  form.platform = "";
  form.display_name = "";
  form.account_id = "";
  form.auth_status = "UNAUTHORIZED";
  form.access_token = "";
  form.refresh_token = "";
  form.expires_at = "";
  form.extra = {};
  form.is_enabled = true;
  extraText.value = "{}";
};

const loadData = async () => {
  loading.value = true;
  try {
    const response = await listPlatformAccounts();
    accounts.value = response.data.items;
  } finally {
    loading.value = false;
  }
};

const openCreate = () => {
  mode.value = "create";
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row: PlatformAccountItem) => {
  mode.value = "edit";
  editingId.value = row.id;
  form.platform = row.platform;
  form.display_name = row.display_name;
  form.account_id = row.account_id;
  form.auth_status = row.auth_status;
  form.access_token = row.access_token ?? "";
  form.refresh_token = row.refresh_token ?? "";
  form.expires_at = row.expires_at ?? "";
  form.extra = row.extra ?? {};
  extraText.value = JSON.stringify(row.extra ?? {}, null, 2);
  form.is_enabled = row.is_enabled;
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  let parsedExtra: Record<string, unknown> | null = null;
  try {
    parsedExtra = extraText.value.trim() ? (JSON.parse(extraText.value) as Record<string, unknown>) : null;
  } catch {
    ElMessage.error("扩展字段 JSON 格式不正确");
    return;
  }

  const payload: PlatformAccountUpsertForm =
    mode.value === "create"
      ? {
          platform: form.platform,
          display_name: form.display_name,
          account_id: form.account_id,
          auth_status: form.auth_status,
          access_token: form.access_token || null,
          refresh_token: form.refresh_token || null,
          expires_at: form.expires_at || null,
          extra: parsedExtra,
          is_enabled: form.is_enabled,
        }
      : {
          id: editingId.value ?? undefined,
          display_name: form.display_name,
          auth_status: form.auth_status,
          access_token: form.access_token || null,
          refresh_token: form.refresh_token || null,
          expires_at: form.expires_at || null,
          extra: parsedExtra,
          is_enabled: form.is_enabled,
          platform: form.platform,
          account_id: form.account_id,
        };

  await savePlatformAccount(payload);
  ElMessage.success(mode.value === "create" ? "平台账号已创建" : "平台账号已更新");
  dialogVisible.value = false;
  await loadData();
};

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="平台账号"
      description="后端已经提供抖音、快手等账号的管理接口，这里直接维护授权状态与令牌信息。"
    >
      <el-button
        v-permission="'system:platform-account:list'"
        type="primary"
        @click="openCreate"
      >
        新增平台账号
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="accounts"
      >
        <el-table-column
          prop="platform"
          label="平台"
          width="140"
        />
        <el-table-column
          prop="display_name"
          label="展示名称"
          min-width="180"
        />
        <el-table-column
          prop="account_id"
          label="账号 ID"
          min-width="180"
        />
        <el-table-column
          label="授权状态"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.auth_status" />
          </template>
        </el-table-column>
        <el-table-column
          prop="access_token"
          label="访问令牌"
          min-width="140"
        />
        <el-table-column
          prop="refresh_token"
          label="刷新令牌"
          min-width="140"
        />
        <el-table-column
          prop="expires_at"
          label="过期时间"
          min-width="180"
        />
        <el-table-column
          label="启用"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.is_enabled ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
        <el-table-column
          prop="updated_at"
          label="最近更新"
          min-width="180"
        />
        <el-table-column
          label="操作"
          width="120"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-permission="'system:platform-account:list'"
              link
              type="primary"
              @click="openEdit(row)"
            >
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="820px"
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
            label="平台标识"
            prop="platform"
          >
            <el-input
              v-model="form.platform"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
          <el-form-item
            label="展示名称"
            prop="display_name"
          >
            <el-input v-model="form.display_name" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item
            label="账号 ID"
            prop="account_id"
          >
            <el-input
              v-model="form.account_id"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
          <el-form-item
            label="授权状态"
            prop="auth_status"
          >
            <el-select
              v-model="form.auth_status"
              style="width: 100%"
            >
              <el-option
                v-for="option in platformAuthStatusOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="访问令牌">
            <el-input
              v-model="form.access_token"
              type="textarea"
              :rows="3"
            />
          </el-form-item>
          <el-form-item label="刷新令牌">
            <el-input
              v-model="form.refresh_token"
              type="textarea"
              :rows="3"
            />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="过期时间">
            <el-date-picker
              v-model="form.expires_at"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ss"
              format="YYYY-MM-DD HH:mm:ss"
              placeholder="选择过期时间"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="form.is_enabled" />
          </el-form-item>
        </div>
        <el-form-item label="扩展字段 JSON">
          <el-input
            v-model="extraText"
            type="textarea"
            :rows="5"
          />
        </el-form-item>
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
