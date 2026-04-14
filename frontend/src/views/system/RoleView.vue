<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { listMenus, listRoles, saveRole } from "@/api/modules/system";
import type { MenuNode, RoleItem, RoleUpsertForm } from "@/types/system";

const loading = ref(false);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const menuTreeRef = ref();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const roles = ref<RoleItem[]>([]);
const menus = ref<MenuNode[]>([]);

const form = reactive<RoleUpsertForm>({
  name: "",
  code: "",
  description: "",
  menu_ids: [],
  is_system: false,
});

const rules: FormRules<RoleUpsertForm> = {
  name: [{ required: true, message: "请输入角色名", trigger: "blur" }],
  code: [{ required: true, message: "请输入角色编码", trigger: "blur" }],
};

const resetForm = () => {
  editingId.value = null;
  form.name = "";
  form.code = "";
  form.description = "";
  form.menu_ids = [];
  form.is_system = false;
};

const loadRoles = async () => {
  loading.value = true;
  try {
    const response = await listRoles();
    roles.value = response.data.items;
  } finally {
    loading.value = false;
  }
};

const loadMenus = async () => {
  const response = await listMenus();
  menus.value = response.data.items;
};

const openCreate = async () => {
  mode.value = "create";
  resetForm();
  dialogVisible.value = true;
  await nextTick();
  menuTreeRef.value?.setCheckedKeys([]);
};

const openEdit = async (row: RoleItem) => {
  mode.value = "edit";
  editingId.value = row.id;
  form.name = row.name;
  form.code = row.code;
  form.description = row.description ?? "";
  form.menu_ids = [...row.menu_ids];
  form.is_system = row.is_system;
  dialogVisible.value = true;
  await nextTick();
  menuTreeRef.value?.setCheckedKeys(row.menu_ids);
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const checkedIds = menuTreeRef.value?.getCheckedKeys(false) ?? form.menu_ids;
  const payload: RoleUpsertForm =
    mode.value === "create"
      ? {
          name: form.name,
          code: form.code,
          description: form.description || null,
          menu_ids: checkedIds,
          is_system: form.is_system,
        }
      : {
          id: editingId.value ?? undefined,
          name: form.name,
          code: form.code,
          description: form.description || null,
          menu_ids: checkedIds,
          is_system: form.is_system,
        };

  await saveRole(payload);
  ElMessage.success(mode.value === "create" ? "角色已创建" : "角色已更新");
  dialogVisible.value = false;
  await loadRoles();
};

onMounted(async () => {
  await Promise.all([loadRoles(), loadMenus()]);
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="角色管理"
      description="后端角色以菜单 ID 为绑定核心，这里直接维护角色基本信息和菜单勾选。"
    >
      <el-button
        v-permission="'system:role:list'"
        type="primary"
        @click="openCreate"
      >
        新增角色
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="roles"
      >
        <el-table-column
          prop="name"
          label="角色名"
          min-width="180"
        />
        <el-table-column
          prop="code"
          label="角色编码"
          min-width="180"
        />
        <el-table-column
          prop="description"
          label="说明"
          min-width="260"
        />
        <el-table-column
          label="系统角色"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.is_system ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
        <el-table-column
          label="菜单数"
          width="100"
        >
          <template #default="{ row }">{{ row.menu_ids.length }}</template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="120"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-permission="'system:role:list'"
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
      :title="mode === 'create' ? '新增角色' : '编辑角色'"
      width="780px"
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
            label="角色名"
            prop="name"
          >
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item
            label="角色编码"
            prop="code"
          >
            <el-input
              v-model="form.code"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
        </div>
        <el-form-item label="说明">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="系统角色">
          <el-switch v-model="form.is_system" />
        </el-form-item>
        <el-form-item label="菜单绑定">
          <el-tree
            ref="menuTreeRef"
            :data="menus"
            node-key="id"
            show-checkbox
            default-expand-all
            :check-strictly="false"
            :props="{ label: 'title', children: 'children' }"
            style="width: 100%"
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
