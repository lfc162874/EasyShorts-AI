<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { configValueTypeOptions } from "@/constants/permissions";
import { listConfigs, saveConfig } from "@/api/modules/system";
import type { ConfigUpsertForm, SystemConfigItem } from "@/types/system";

const loading = ref(false);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const configs = ref<SystemConfigItem[]>([]);
const activeCategory = ref<string>("prompt");

const form = reactive<ConfigUpsertForm>({
  category: "",
  config_key: "",
  config_value: "",
  value_type: "STRING",
  description: "",
  is_secret: false,
  is_enabled: true,
});

const rules: FormRules<ConfigUpsertForm> = {
  category: [{ required: true, message: "请输入分类", trigger: "blur" }],
  config_key: [{ required: true, message: "请输入配置键", trigger: "blur" }],
  config_value: [{ required: true, message: "请输入配置值", trigger: "blur" }],
  value_type: [{ required: true, message: "请选择类型", trigger: "change" }],
};

const categories = computed(() => {
  const unique = new Set(configs.value.map((item) => item.category));
  return Array.from(unique);
});

const filteredConfigs = computed(() =>
  activeCategory.value
    ? configs.value.filter((item) => item.category === activeCategory.value)
    : configs.value,
);

const dialogTitle = computed(() =>
  mode.value === "create" ? "新增配置" : "编辑配置",
);

const resetForm = () => {
  editingId.value = null;
  form.category = "";
  form.config_key = "";
  form.config_value = "";
  form.value_type = "STRING";
  form.description = "";
  form.is_secret = false;
  form.is_enabled = true;
};

const loadData = async () => {
  loading.value = true;
  try {
    const response = await listConfigs();
    configs.value = response.data.items;
    if (!categories.value.includes(activeCategory.value)) {
      activeCategory.value = categories.value[0] ?? "";
    }
  } finally {
    loading.value = false;
  }
};

const openCreate = () => {
  mode.value = "create";
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row: SystemConfigItem) => {
  mode.value = "edit";
  editingId.value = row.id;
  form.category = row.category;
  form.config_key = row.config_key;
  form.config_value = row.is_secret ? "" : row.config_value;
  form.value_type = row.value_type;
  form.description = row.description ?? "";
  form.is_secret = row.is_secret;
  form.is_enabled = row.is_enabled;
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const payload: ConfigUpsertForm =
    mode.value === "create"
      ? {
          category: form.category,
          config_key: form.config_key,
          config_value: form.config_value,
          value_type: form.value_type,
          description: form.description || null,
          is_secret: form.is_secret,
          is_enabled: form.is_enabled,
        }
      : {
          id: editingId.value ?? undefined,
          category: form.category,
          config_key: form.config_key,
          config_value: form.config_value,
          value_type: form.value_type,
          description: form.description || null,
          is_secret: form.is_secret,
          is_enabled: form.is_enabled,
        };

  await saveConfig(payload);
  ElMessage.success(mode.value === "create" ? "配置已创建" : "配置已更新");
  dialogVisible.value = false;
  await loadData();
};

watch(categories, (value) => {
  if (!activeCategory.value && value[0]) {
    activeCategory.value = value[0];
  }
});

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="系统配置"
      description="Prompt、平台账号、通用参数都在这套真实配置结构里维护。"
    >
      <el-button
        v-permission="'system:config:list'"
        type="primary"
        @click="openCreate"
      >
        新增配置
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-tabs
        v-model="activeCategory"
      >
        <el-tab-pane
          v-for="category in categories"
          :key="category"
          :label="category"
          :name="category"
        />
      </el-tabs>

      <el-table
        v-loading="loading"
        :data="filteredConfigs"
      >
        <el-table-column
          prop="category"
          label="分类"
          min-width="120"
        />
        <el-table-column
          prop="config_key"
          label="配置键"
          min-width="220"
        />
        <el-table-column
          label="配置值"
          min-width="260"
        >
          <template #default="{ row }">
            <span v-if="row.is_secret">***</span>
            <span v-else>{{ row.config_value }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="value_type"
          label="类型"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.value_type" />
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="说明"
          min-width="240"
        />
        <el-table-column
          label="密钥"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.is_secret ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
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
              v-permission="'system:config:list'"
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
      width="720px"
      @closed="resetForm"
    >
      <el-alert
        v-if="form.is_secret"
        title="当前配置被标记为密钥，编辑时请重新输入配置值。"
        type="warning"
        :closable="false"
        style="margin-bottom: 16px"
      />
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <div class="form-grid">
          <el-form-item
            label="分类"
            prop="category"
          >
            <el-input
              v-model="form.category"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
          <el-form-item
            label="配置键"
            prop="config_key"
          >
            <el-input
              v-model="form.config_key"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
        </div>
        <el-form-item
          label="配置值"
          prop="config_value"
        >
          <el-input
            v-model="form.config_value"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <div class="form-grid">
          <el-form-item
            label="值类型"
            prop="value_type"
          >
            <el-select
              v-model="form.value_type"
              style="width: 100%"
            >
              <el-option
                v-for="option in configValueTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="form.description" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="密钥">
            <el-switch v-model="form.is_secret" />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="form.is_enabled" />
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
