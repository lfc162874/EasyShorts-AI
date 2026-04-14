<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { menuTypeOptions } from "@/constants/permissions";
import { listMenus, saveMenu } from "@/api/modules/system";
import type { MenuNode, MenuUpsertForm } from "@/types/system";

const loading = ref(false);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const menus = ref<MenuNode[]>([]);

const form = reactive<MenuUpsertForm>({
  parent_id: null,
  name: "",
  title: "",
  path: "",
  component: "",
  icon: "",
  permission_code: "",
  menu_type: "MENU",
  sort_order: 0,
  hidden: false,
});

const rules: FormRules<MenuUpsertForm> = {
  name: [{ required: true, message: "请输入菜单标识", trigger: "blur" }],
  title: [{ required: true, message: "请输入菜单标题", trigger: "blur" }],
  menu_type: [{ required: true, message: "请选择菜单类型", trigger: "change" }],
};

const dialogTitle = computed(() =>
  mode.value === "create" ? "新增菜单" : "编辑菜单",
);

const flattenMenus = (items: MenuNode[], list: MenuNode[] = []): MenuNode[] => {
  for (const item of items) {
    list.push(item);
    if (item.children?.length) {
      flattenMenus(item.children, list);
    }
  }
  return list;
};

const parentOptions = computed(() => flattenMenus(menus.value));

const resetForm = () => {
  editingId.value = null;
  form.parent_id = null;
  form.name = "";
  form.title = "";
  form.path = "";
  form.component = "";
  form.icon = "";
  form.permission_code = "";
  form.menu_type = "MENU";
  form.sort_order = 0;
  form.hidden = false;
};

const loadData = async () => {
  loading.value = true;
  try {
    const response = await listMenus();
    menus.value = response.data.items;
  } finally {
    loading.value = false;
  }
};

const openCreate = () => {
  mode.value = "create";
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row: MenuNode) => {
  mode.value = "edit";
  editingId.value = row.id;
  form.parent_id = row.parent_id;
  form.name = row.name;
  form.title = row.title;
  form.path = row.path ?? "";
  form.component = row.component ?? "";
  form.icon = row.icon ?? "";
  form.permission_code = row.permission_code ?? "";
  form.menu_type = row.menu_type;
  form.sort_order = row.sort_order;
  form.hidden = row.hidden;
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const payload: MenuUpsertForm =
    mode.value === "create"
      ? {
          parent_id: form.parent_id,
          name: form.name,
          title: form.title,
          path: form.path || null,
          component: form.component || null,
          icon: form.icon || null,
          permission_code: form.permission_code || null,
          menu_type: form.menu_type,
          sort_order: form.sort_order,
          hidden: form.hidden,
        }
      : {
          id: editingId.value ?? undefined,
          parent_id: form.parent_id,
          name: form.name,
          title: form.title,
          path: form.path || null,
          component: form.component || null,
          icon: form.icon || null,
          permission_code: form.permission_code || null,
          menu_type: form.menu_type,
          sort_order: form.sort_order,
          hidden: form.hidden,
        };

  await saveMenu(payload);
  ElMessage.success(mode.value === "create" ? "菜单已创建" : "菜单已更新");
  dialogVisible.value = false;
  await loadData();
};

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="菜单管理"
      description="后端返回树形菜单结构，这里可以直接维护目录、菜单和按钮。"
    >
      <el-button
        v-permission="'system:menu:list'"
        type="primary"
        @click="openCreate"
      >
        新增菜单
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="menus"
        row-key="id"
        :tree-props="{ children: 'children' }"
      >
        <el-table-column
          prop="title"
          label="菜单标题"
          min-width="180"
        />
        <el-table-column
          prop="name"
          label="菜单标识"
          min-width="180"
        />
        <el-table-column
          prop="path"
          label="路径"
          min-width="220"
        />
        <el-table-column
          prop="component"
          label="组件"
          min-width="220"
        />
        <el-table-column
          prop="permission_code"
          label="权限码"
          min-width="220"
        />
        <el-table-column
          label="类型"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.menu_type" />
          </template>
        </el-table-column>
        <el-table-column
          prop="sort_order"
          label="排序"
          width="90"
        />
        <el-table-column
          label="隐藏"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.hidden ? 'DISABLED' : 'ACTIVE'" />
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="120"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-permission="'system:menu:list'"
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
      width="760px"
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
            label="菜单标识"
            prop="name"
          >
            <el-input
              v-model="form.name"
              :disabled="mode === 'edit'"
            />
          </el-form-item>
          <el-form-item
            label="菜单标题"
            prop="title"
          >
            <el-input v-model="form.title" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="路径">
            <el-input v-model="form.path" />
          </el-form-item>
          <el-form-item label="组件">
            <el-input v-model="form.component" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="图标">
            <el-input v-model="form.icon" />
          </el-form-item>
          <el-form-item label="权限码">
            <el-input v-model="form.permission_code" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item
            label="菜单类型"
            prop="menu_type"
          >
            <el-select
              v-model="form.menu_type"
              style="width: 100%"
            >
              <el-option
                v-for="option in menuTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="父级菜单">
            <el-select
              v-model="form.parent_id"
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="item in parentOptions"
                :key="item.id"
                :label="item.title"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="排序">
            <el-input-number
              v-model="form.sort_order"
              :min="0"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="隐藏">
            <el-switch v-model="form.hidden" />
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
