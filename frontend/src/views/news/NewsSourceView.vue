<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { newsSourceTypeOptions } from "@/constants/permissions";
import {
  listNewsSources,
  saveNewsSource,
  syncNewsSource,
} from "@/api/modules/news";
import type {
  NewsSourceItem,
  NewsSourceQuery,
  NewsSourceExtraConfig,
  NewsSourceUpsertForm,
} from "@/types/news";
import { formatDateTime } from "@/utils/format";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const syncingId = ref<number | null>(null);
const updatingId = ref<number | null>(null);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const mode = ref<"create" | "edit">("create");
const editingId = ref<number | null>(null);
const sources = ref<NewsSourceItem[]>([]);
const total = ref(0);
const extraText = ref("");

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

const dialogTitle = computed(() => (mode.value === "create" ? "新增来源" : "编辑来源"));

const buildExtraExample = (sourceType: NewsSourceItem["source_type"]) => {
  if (sourceType === "WEB") {
    return JSON.stringify(
      {
        mode: "list",
        article_urls: [
          "https://example.com/news/1",
          "https://example.com/news/2",
        ],
        max_items: 10,
        link_patterns: ["/news/", "/blog/"],
        exclude_link_patterns: ["/tag/", "/category/"],
      },
      null,
      2,
    );
  }

  if (sourceType === "MANUAL") {
    return JSON.stringify(
      {
        items: [
          {
            title: "OpenAI 发布新功能",
            link: "https://example.com/article/1",
            content: "这里是手工导入的正文内容或摘要。",
            published_at: "2026-04-15T08:00:00Z",
            author: "EasyShorts",
            guid: "manual-article-1",
          },
        ],
      },
      null,
      2,
    );
  }

  return JSON.stringify(
    {
      weight: 25,
    },
    null,
    2,
  );
};

const extraGuide = computed(() => {
  if (form.source_type === "WEB") {
    return {
      title: "WEB 来源配置",
      description:
        "WEB 源支持直接提供文章页地址，也支持通过链接规则自动发现文章。",
      fields: [
        "mode",
        "article_urls / urls",
        "max_items",
        "link_patterns",
        "exclude_link_patterns",
      ],
    };
  }

  if (form.source_type === "MANUAL") {
    return {
      title: "MANUAL 来源配置",
      description: "MANUAL 源支持导入结构化条目数组，适合人工维护热点列表。",
      fields: [
        "items / entries",
        "title",
        "link / url",
        "content / description / summary",
        "published_at / date",
        "author / creator",
      ],
    };
  }

  return {
    title: "RSS / ATOM 来源配置",
    description: "RSS 与 ATOM 源通常只需要一个可选的热度权重。",
    fields: ["weight"],
  };
});

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
  extraText.value = buildExtraExample(form.source_type);
};

const parseRouteId = (value: unknown): number | null => {
  const rawValue = Array.isArray(value) ? value[0] : value;
  const parsed = Number(rawValue);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
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
  extraText.value = JSON.stringify(
    row.extra ?? JSON.parse(buildExtraExample(row.source_type)),
    null,
    2,
  );
  dialogVisible.value = true;
};

const maybeOpenEditFromRoute = async () => {
  const editId = parseRouteId(route.query.edit);
  if (!editId) {
    return;
  }

  const target = sources.value.find((item) => item.id === editId);
  if (!target) {
    return;
  }

  openEdit(target);

  const nextQuery = { ...route.query };
  delete nextQuery.edit;
  await router.replace({
    path: route.path,
    query: nextQuery,
  });
};

const goToSourceDetail = (row: NewsSourceItem) => {
  void router.push(`/news/sources/${row.id}`);
};

const goToRecords = (row: NewsSourceItem) => {
  void router.push({
    path: "/news/records",
    query: { source_id: String(row.id) },
  });
};

const goToArticles = (row: NewsSourceItem) => {
  void router.push({
    path: "/news/list",
    query: { source_id: String(row.id) },
  });
};

const handleSync = async (row: NewsSourceItem) => {
  syncingId.value = row.id;
  try {
    const response = await syncNewsSource(row.id);
    const task = response.data;
    if (task.status === "SUCCESS" && task.result) {
      const result = task.result as Record<string, unknown>;
      const newCount = Number(result.new_count ?? 0);
      const duplicateCount = Number(result.duplicate_count ?? 0);
      const filteredCount = Number(result.filtered_count ?? result.rejected_count ?? 0);
      ElMessage.success(
        `已执行 ${row.name}，新增 ${newCount} 条，重复 ${duplicateCount} 条，过滤 ${filteredCount} 条`,
      );
    } else {
      ElMessage.success(`已提交采集任务 #${task.id}：${row.name}`);
    }
    await loadSources();
  } catch {
    // 请求层会给出具体错误，这里只负责吞掉未处理的异常。
  } finally {
    syncingId.value = null;
  }
};

const handleToggleEnabled = async (row: NewsSourceItem) => {
  const nextEnabled = !row.is_enabled;
  const actionText = nextEnabled ? "启用" : "停用";

  try {
    await ElMessageBox.confirm(
      `确认${actionText}来源「${row.name}」吗？`,
      `${actionText}来源`,
      { type: "warning" },
    );
  } catch {
    return;
  }

  updatingId.value = row.id;
  try {
    await saveNewsSource({
      id: row.id,
      source_key: row.source_key,
      name: row.name,
      source_type: row.source_type,
      url: row.url,
      category: row.category,
      language: row.language,
      fetch_interval_minutes: row.fetch_interval_minutes,
      is_enabled: nextEnabled,
      extra: row.extra,
    });
    ElMessage.success(`来源已${actionText}`);
    await loadSources();
  } catch {
    // 请求层会处理详细错误提示。
  } finally {
    updatingId.value = null;
  }
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  let parsedExtra: NewsSourceExtraConfig | null = null;
  try {
    parsedExtra = extraText.value.trim()
      ? (JSON.parse(extraText.value) as NewsSourceExtraConfig)
      : null;
  } catch {
    ElMessage.error("扩展字段 JSON 格式不正确");
    return;
  }

  const sourceKey = form.source_key.trim().toLowerCase();
  const name = form.name.trim();
  const url = form.url.trim();
  const category = (form.category ?? "").trim();
  const language = form.language.trim();

  const payload: NewsSourceUpsertForm =
    mode.value === "create"
      ? {
          source_key: sourceKey,
          name,
          source_type: form.source_type,
          url,
          category: category || null,
          language,
          fetch_interval_minutes: form.fetch_interval_minutes,
          is_enabled: form.is_enabled,
          extra: parsedExtra,
        }
      : {
          id: editingId.value ?? undefined,
          source_key: sourceKey,
          name,
          source_type: form.source_type,
          url,
          category: category || null,
          language,
          fetch_interval_minutes: form.fetch_interval_minutes,
          is_enabled: form.is_enabled,
          extra: parsedExtra,
        };

  try {
    await saveNewsSource(payload);
    ElMessage.success(mode.value === "create" ? "来源已创建" : "来源已更新");
    dialogVisible.value = false;
    await loadSources();
  } catch {
    // 请求层会给出具体错误，这里保持对话框打开，方便用户修正配置。
  }
};

const fillExtraExample = () => {
  extraText.value = buildExtraExample(form.source_type);
};

watch(
  () => form.source_type,
  (next, prev) => {
    if (mode.value === "create") {
      extraText.value = buildExtraExample(next);
      return;
    }

    if (!prev) {
      return;
    }

    const currentExtra = extraText.value.trim();
    const previousExample = buildExtraExample(prev).trim();
    if (!currentExtra || currentExtra === previousExample) {
      extraText.value = buildExtraExample(next);
    }
  },
);

onMounted(async () => {
  await loadSources();
  await maybeOpenEditFromRoute();
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="来源管理"
      description="维护系统监控的 AI 站点、RSS 与手动来源，并可直接执行采集。"
    >
      <el-button
        v-permission="'news:source:create'"
        type="primary"
        @click="openCreate"
      >
        新增来源
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
          label="抓取频率"
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
          prop="last_success_at"
          label="最近成功"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.last_success_at) }}
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
          width="340"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-permission="'news:source:list'"
              link
              type="primary"
              @click="goToSourceDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-permission="'news:fetch-record:list'"
              link
              type="primary"
              @click="goToRecords(row)"
            >
              记录
            </el-button>
            <el-button
              v-permission="'news:list'"
              link
              type="primary"
              @click="goToArticles(row)"
            >
              内容
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
              :loading="syncingId === row.id"
              :disabled="syncingId === row.id"
              @click="handleSync(row)"
            >
              抓取
            </el-button>
            <el-button
              v-permission="'news:source:update'"
              link
              type="primary"
              :loading="updatingId === row.id"
              :disabled="updatingId === row.id"
              @click="handleToggleEnabled(row)"
            >
              {{ row.is_enabled ? "停用" : "启用" }}
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
            @blur="form.source_key = form.source_key.trim().toLowerCase()"
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
          <div style="width: 100%">
            <el-alert
              :title="extraGuide.title"
              :description="extraGuide.description"
              type="info"
              :closable="false"
              show-icon
            />
            <div
              class="tag-row"
              style="margin: 10px 0 12px"
            >
              <el-tag
                v-for="field in extraGuide.fields"
                :key="field"
                effect="plain"
              >
                {{ field }}
              </el-tag>
              <el-button
                link
                type="primary"
                @click="fillExtraExample"
              >
                插入示例配置
              </el-button>
            </div>
            <el-input
              v-model="extraText"
              :rows="8"
              type="textarea"
              :placeholder="buildExtraExample(form.source_type)"
            />
          </div>
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
