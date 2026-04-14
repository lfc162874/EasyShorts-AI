<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { newsSourceTypeOptions } from "@/constants/permissions";
import {
  getNewsSource,
  listNewsSources,
  saveNewsSource,
  syncNewsSource,
} from "@/api/modules/news";
import type {
  NewsSourceItem,
  NewsSourceQuery,
  NewsSourceUpsertForm,
} from "@/types/news";
import { formatDateTime, formatJson } from "@/utils/format";

const loading = ref(false);
const dialogVisible = ref(false);
const detailVisible = ref(false);
const detailLoading = ref(false);
const formRef = ref<FormInstance>();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const sources = ref<NewsSourceItem[]>([]);
const detail = ref<NewsSourceItem | null>(null);
const total = ref(0);
const extraText = ref("{}");

const query = reactive<NewsSourceQuery>({
  page: 1,
  page_size: 20,
  keyword: "",
  source_type: undefined,
  is_enabled: undefined,
});

const form = reactive<NewsSourceUpsertForm>({
  source_key: "",
  name: "",
  source_type: "RSS",
  url: "",
  category: "",
  language: "en",
  fetch_interval_minutes: 360,
  is_enabled: true,
  extra: {},
});

const rules: FormRules<NewsSourceUpsertForm> = {
  source_key: [{ required: true, message: "请输入来源标识", trigger: "blur" }],
  name: [{ required: true, message: "请输入来源名称", trigger: "blur" }],
  url: [{ required: true, message: "请输入来源地址", trigger: "blur" }],
  source_type: [{ required: true, message: "请选择来源类型", trigger: "change" }],
  language: [{ required: true, message: "请输入语言标识", trigger: "blur" }],
};

const dialogTitle = computed(() =>
  mode.value === "create" ? "新增新闻源" : "编辑新闻源",
);

const resetForm = () => {
  editingId.value = null;
  form.source_key = "";
  form.name = "";
  form.source_type = "RSS";
  form.url = "";
  form.category = "";
  form.language = "en";
  form.fetch_interval_minutes = 360;
  form.is_enabled = true;
  form.extra = {};
  extraText.value = "{}";
};

const loadSources = async () => {
  loading.value = true;
  try {
    const response = await listNewsSources({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      source_type: query.source_type || undefined,
      is_enabled: query.is_enabled,
    });
    sources.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const openCreate = () => {
  mode.value = "create";
  resetForm();
  dialogVisible.value = true;
};

const openEdit = (row: NewsSourceItem) => {
  mode.value = "edit";
  editingId.value = row.id;
  form.source_key = row.source_key;
  form.name = row.name;
  form.source_type = row.source_type;
  form.url = row.url;
  form.category = row.category ?? "";
  form.language = row.language;
  form.fetch_interval_minutes = row.fetch_interval_minutes;
  form.is_enabled = row.is_enabled;
  form.extra = row.extra ?? {};
  extraText.value = JSON.stringify(row.extra ?? {}, null, 2);
  dialogVisible.value = true;
};

const openDetail = async (row: NewsSourceItem) => {
  detailVisible.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    const response = await getNewsSource(row.id);
    detail.value = response.data;
  } catch {
    ElMessage.error("新闻源详情加载失败");
  } finally {
    detailLoading.value = false;
  }
};

const handleSync = async (row: NewsSourceItem) => {
  try {
    const response = await syncNewsSource(row.id);
    ElMessage.success(`已提交同步任务 #${response.data.id}：${row.name}`);
  } catch {
    // 请求层会给出具体错误，这里只负责吞掉未处理的异常。
  }
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  let parsedExtra: Record<string, unknown> | null = null;
  try {
    parsedExtra = extraText.value.trim()
      ? (JSON.parse(extraText.value) as Record<string, unknown>)
      : null;
  } catch {
    ElMessage.error("扩展字段 JSON 格式不正确");
    return;
  }

  const payload: NewsSourceUpsertForm =
    mode.value === "create"
      ? {
          source_key: form.source_key,
          name: form.name,
          source_type: form.source_type,
          url: form.url,
          category: form.category || null,
          language: form.language,
          fetch_interval_minutes: form.fetch_interval_minutes,
          is_enabled: form.is_enabled,
          extra: parsedExtra,
        }
      : {
          id: editingId.value ?? undefined,
          source_key: form.source_key,
          name: form.name,
          source_type: form.source_type,
          url: form.url,
          category: form.category || null,
          language: form.language,
          fetch_interval_minutes: form.fetch_interval_minutes,
          is_enabled: form.is_enabled,
          extra: parsedExtra,
        };

  await saveNewsSource(payload);
  ElMessage.success(mode.value === "create" ? "新闻源已创建" : "新闻源已更新");
  dialogVisible.value = false;
  await loadSources();
};

onMounted(loadSources);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="新闻源管理"
      description="这里维护 AI 新闻数据源，支持新增、编辑和手动同步。"
    >
      <el-button
        v-permission="'news:source:create'"
        type="primary"
        @click="openCreate"
      >
        新增新闻源
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-form
        :inline="true"
        class="toolbar-form"
      >
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            clearable
            placeholder="来源名称 / 地址 / 标识"
            style="width: 220px"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="query.source_type"
            clearable
            placeholder="全部"
            style="width: 140px"
          >
            <el-option
              v-for="item in newsSourceTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="query.is_enabled"
            clearable
            placeholder="全部"
            style="width: 120px"
          >
            <el-option label="启用" :value="true" />
            <el-option label="停用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadSources">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="sources"
      >
        <el-table-column
          prop="name"
          label="名称"
          min-width="180"
        />
        <el-table-column
          prop="source_key"
          label="标识"
          min-width="160"
        />
        <el-table-column
          label="类型"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.source_type" />
          </template>
        </el-table-column>
        <el-table-column
          prop="url"
          label="地址"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column
          prop="category"
          label="分类"
          min-width="120"
        />
        <el-table-column
          prop="language"
          label="语言"
          width="100"
        />
        <el-table-column
          prop="fetch_interval_minutes"
          label="抓取间隔"
          width="120"
        >
          <template #default="{ row }">
            {{ row.fetch_interval_minutes }} 分钟
          </template>
        </el-table-column>
        <el-table-column
          label="状态"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.is_enabled ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
        <el-table-column
          prop="last_fetched_at"
          label="最近抓取"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.last_fetched_at) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="last_error_message"
          label="最近错误"
          min-width="240"
          show-overflow-tooltip
        />
        <el-table-column
          prop="updated_at"
          label="更新时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="240"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-permission="'news:source:list'"
              link
              type="primary"
              @click="openDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-permission="'news:source:update'"
              link
              type="primary"
              @click="openEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-permission="'news:source:sync'"
              link
              type="primary"
              @click="handleSync(row)"
            >
              同步
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
          @current-change="loadSources"
        />
      </div>
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
        label-width="120px"
      >
        <el-form-item
          label="来源标识"
          prop="source_key"
        >
          <el-input
            v-model="form.source_key"
            :disabled="mode === 'edit'"
            placeholder="openai_blog"
          />
        </el-form-item>
        <el-form-item
          label="来源名称"
          prop="name"
        >
          <el-input
            v-model="form.name"
            placeholder="OpenAI Blog"
          />
        </el-form-item>
        <el-form-item
          label="来源类型"
          prop="source_type"
        >
          <el-select v-model="form.source_type">
            <el-option
              v-for="item in newsSourceTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="来源地址"
          prop="url"
        >
          <el-input
            v-model="form.url"
            placeholder="https://example.com/rss.xml"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-input
            v-model="form.category"
            placeholder="模型发布 / 开源生态"
          />
        </el-form-item>
        <el-form-item
          label="语言"
          prop="language"
        >
          <el-input
            v-model="form.language"
            placeholder="en / zh"
          />
        </el-form-item>
        <el-form-item label="抓取间隔">
          <el-input-number
            v-model="form.fetch_interval_minutes"
            :min="5"
            :max="10080"
          />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
        <el-form-item label="扩展配置">
          <el-input
            v-model="extraText"
            :rows="6"
            type="textarea"
            placeholder='{"weight": 25}'
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

    <el-drawer
      v-model="detailVisible"
      size="48%"
      title="新闻源详情"
    >
      <el-skeleton
        v-if="detailLoading"
        :rows="8"
        animated
      />
      <div v-else-if="detail">
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="来源标识">
            {{ detail.source_key }}
          </el-descriptions-item>
          <el-descriptions-item label="来源名称">
            {{ detail.name }}
          </el-descriptions-item>
          <el-descriptions-item label="来源类型">
            <StatusTag :status="detail.source_type" />
          </el-descriptions-item>
          <el-descriptions-item label="启用状态">
            <StatusTag :status="detail.is_enabled ? 'ACTIVE' : 'DISABLED'" />
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ detail.category || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="语言">
            {{ detail.language }}
          </el-descriptions-item>
          <el-descriptions-item label="抓取地址" :span="2">
            <a
              :href="detail.url"
              target="_blank"
              rel="noreferrer"
            >
              {{ detail.url }}
            </a>
          </el-descriptions-item>
          <el-descriptions-item label="抓取间隔">
            {{ detail.fetch_interval_minutes }} 分钟
          </el-descriptions-item>
          <el-descriptions-item label="最近抓取">
            {{ formatDateTime(detail.last_fetched_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="最近成功">
            {{ formatDateTime(detail.last_success_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(detail.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item
            label="最近错误"
            :span="2"
          >
            {{ detail.last_error_message || "暂无错误" }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">扩展配置</el-divider>
        <pre class="news-pre">{{ formatJson(detail.extra) }}</pre>
      </div>
    </el-drawer>
  </div>
</template>
