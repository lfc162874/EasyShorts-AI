<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import ArtifactViewer from "@/components/ArtifactViewer.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { listAgentModels, triggerAgentRun } from "@/api/modules/agent";
import {
  getNews,
  listNews,
  listNewsSources,
} from "@/api/modules/news";
import { newsStatusOptions } from "@/constants/permissions";
import type { AgentModelItem } from "@/types/agent";
import type { NewsDetailItem, NewsItem, NewsSourceItem } from "@/types/news";
import { resolveAgentModelOptions, resolveDefaultAgentModel } from "@/utils/agent";
import { formatDateTime } from "@/utils/format";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const news = ref<NewsItem[]>([]);
const total = ref(0);
const sources = ref<NewsSourceItem[]>([]);
const modelOptions = ref<AgentModelItem[]>([]);
const detailVisible = ref(false);
const detailLoading = ref(false);
const detail = ref<NewsDetailItem | null>(null);
const selectedModel = ref("");
const processingId = ref<number | null>(null);

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: "",
  status: "" as "" | NewsItem["status"],
  source_id: "" as "" | number,
  category: "",
});

const sourceMap = computed(() =>
  Object.fromEntries(sources.value.map((item) => [item.id, item.name])),
);

const selectedSource = computed(() =>
  sources.value.find((item) => item.id === Number(query.source_id)) ?? null,
);

const rawMetadata = computed(() => readRecord(detail.value?.raw_metadata));

const parseRouteId = (value: unknown): number | null => {
  const rawValue = Array.isArray(value) ? value[0] : value;
  const parsed = Number(rawValue);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
};

const applyRouteFilters = () => {
  query.source_id = parseRouteId(route.query.source_id) ?? "";
};

const loadSources = async () => {
  const response = await listNewsSources({ page: 1, page_size: 200 });
  sources.value = response.data.items;
};

const loadModels = async () => {
  const response = await listAgentModels();
  modelOptions.value = resolveAgentModelOptions(response.data);
  selectedModel.value = resolveDefaultAgentModel(modelOptions.value, selectedModel.value);
};

const loadNews = async () => {
  loading.value = true;
  try {
    const response = await listNews({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      status: query.status || undefined,
      source_id: query.source_id === "" ? undefined : Number(query.source_id),
      category: query.category || undefined,
    });
    news.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const openDetail = async (row: NewsItem) => {
  detailVisible.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    const response = await getNews(row.id);
    detail.value = response.data;
  } catch {
    ElMessage.error("内容详情加载失败");
  } finally {
    detailLoading.value = false;
  }
};

const handleGenerate = async (row: NewsItem) => {
  processingId.value = row.id;
  try {
    const response = await triggerAgentRun(row.id, {
      model_name: selectedModel.value || undefined,
      force: true,
    });
    ElMessage.success(`已提交 Agent 运行任务 #${response.data.id}：${row.title}`);
    await loadNews();
  } catch {
    // 请求层会给出具体错误，这里只负责吞掉未处理的异常。
  } finally {
    processingId.value = null;
  }
};

const goToSourceDetail = () => {
  if (!selectedSource.value) {
    return;
  }
  void router.push(`/news/sources/${selectedSource.value.id}`);
};

const goToRecords = () => {
  if (!selectedSource.value) {
    return;
  }
  void router.push({
    path: "/news/records",
    query: { source_id: String(selectedSource.value.id) },
  });
};

const openOriginal = (url: string) => {
  window.open(url, "_blank", "noopener,noreferrer");
};

const goToAgentRuns = () => {
  void router.push("/agent/runs");
};

const readRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
};

const rawContent = computed(() => {
  const raw = rawMetadata.value;
  const candidate =
    raw?.raw_content ?? raw?.content ?? raw?.raw_summary ?? raw?.summary ?? null;
  return typeof candidate === "string" ? candidate : null;
});

const analysisInfo = computed(() => readRecord(rawMetadata.value?.analysis));

const mergedSources = computed(() => {
  const items = rawMetadata.value?.merged_sources;
  if (!Array.isArray(items)) {
    return [];
  }
  return items.filter((item): item is Record<string, unknown> => {
    return Boolean(item && typeof item === "object" && !Array.isArray(item));
  });
});

const promptBundle = computed(() => readRecord(rawMetadata.value?.prompt_bundle));

const agentProcessing = computed(() => {
  return readRecord(rawMetadata.value?.agent_processing);
});

const agentRunId = computed(() => {
  const rawRunId = agentProcessing.value?.run_id;
  const parsed = Number(rawRunId);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
});

const processingArtifacts = computed(() => {
  const processing = agentProcessing.value;
  if (!processing) {
    return [];
  }

  return [
    {
      key: "hotspot",
      title: "热点判断",
      contentJson: readRecord(processing.hotspot),
    },
    {
      key: "classification",
      title: "标签分类",
      contentJson: readRecord(processing.classification),
    },
    {
      key: "summary",
      title: "智能摘要结果",
      contentJson: readRecord(processing.summary),
    },
    {
      key: "enrichment",
      title: "补充分析",
      contentJson: readRecord(processing.enrichment),
    },
    {
      key: "push_planner",
      title: "推送规划",
      contentJson: readRecord(processing.push_planner),
    },
  ].filter((item) => item.contentJson);
});

const contentStages = computed(() => {
  const current = detail.value;
  if (!current) {
    return [];
  }
  return [
    {
      title: "正文清洗",
      status: current.content ? ("SUCCESS" as const) : ("PENDING" as const),
      summary: current.content ? "清洗后的正文已沉淀为可分析内容" : "暂无清洗正文",
      meta: current.content ? `${current.content.length} 字符` : "",
    },
    {
      title: "去重",
      status: current.dedup_hash ? ("SUCCESS" as const) : ("PENDING" as const),
      summary:
        mergedSources.value.length > 1
          ? `已合并 ${mergedSources.value.length} 个来源`
          : current.dedup_hash
            ? "已完成去重指纹生成"
            : "尚未生成去重哈希",
      meta: current.dedup_hash || "",
    },
    {
      title: "翻译",
      status: current.translated_title || current.translated_content ? ("SUCCESS" as const) : ("PENDING" as const),
      summary: current.translated_title || current.translated_content ? "中译结果可用于后续摘要与推送" : "暂无翻译结果",
      meta: current.language || "",
    },
    {
      title: "摘要",
      status: current.summary ? ("SUCCESS" as const) : ("PENDING" as const),
      summary: current.summary || "暂无摘要",
      meta: current.summary ? `${current.summary.length} 字符` : "",
    },
    {
      title: "标签分类",
      status: current.tags?.length ? ("SUCCESS" as const) : ("PENDING" as const),
      summary: current.tags?.length ? current.tags.join("、") : "暂无标签",
      meta: analysisInfo.value?.category ? `分类：${String(analysisInfo.value.category)}` : "",
    },
    {
      title: "过滤",
      status: current.status === "REJECTED" ? ("REJECTED" as const) : ("SUCCESS" as const),
      summary:
        current.status === "REJECTED"
          ? current.filter_reason || "内容已被拦截"
          : "已通过质量与相关性筛选",
      meta: analysisInfo.value?.hot_score ? `热度：${String(analysisInfo.value.hot_score)}` : "",
    },
  ];
});

const goToAgentRun = () => {
  if (!agentRunId.value) {
    return;
  }
  void router.push(`/agent/runs/${agentRunId.value}`);
};

watch(
  () => route.query.source_id,
  async () => {
    applyRouteFilters();
    await loadNews();
  },
);

onMounted(async () => {
  applyRouteFilters();
  await Promise.all([loadSources(), loadModels(), loadNews()]);
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="内容中心"
      description="查看采集到的内容、打开原文，并手动触发 Agent 智能处理。"
    >
      <el-tag
        v-if="selectedSource"
        effect="plain"
      >
        当前来源：{{ selectedSource.name }}
      </el-tag>
      <el-button
        v-if="selectedSource"
        @click="goToSourceDetail"
      >
        来源详情
      </el-button>
      <el-button
        v-if="selectedSource"
        @click="goToRecords"
      >
        查看记录
      </el-button>
      <el-select
        v-model="selectedModel"
        :disabled="!modelOptions.length"
        placeholder="默认模型"
        style="width: 160px"
      >
        <el-option
          v-for="item in modelOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-button @click="goToAgentRuns">Agent运行中心</el-button>
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
            placeholder="标题 / 摘要 / 标签"
            style="width: 220px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="query.status"
            clearable
            placeholder="全部"
            style="width: 150px"
          >
            <el-option
              v-for="item in newsStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select
            v-model="query.source_id"
            clearable
            placeholder="全部"
            style="width: 220px"
          >
            <el-option
              v-for="item in sources"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input
            v-model="query.category"
            clearable
            placeholder="模型发布 / 开源生态"
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="loadNews">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="news"
      >
        <el-table-column
          prop="title"
          label="标题"
          min-width="280"
          show-overflow-tooltip
        />
        <el-table-column
          label="来源"
          min-width="160"
        >
          <template #default="{ row }">
            {{ sourceMap[row.source_id ?? -1] ?? row.source }}
          </template>
        </el-table-column>
        <el-table-column
          prop="category"
          label="分类"
          min-width="120"
        />
        <el-table-column
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column
          prop="hot_score"
          label="热度"
          width="100"
        />
        <el-table-column
          prop="publish_time"
          label="发布时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.publish_time) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="summary"
          label="摘要"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column
          prop="translated_title"
          label="中文标题"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column
          prop="language"
          label="语言"
          width="90"
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
          width="220"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="openDetail(row)"
            >
              详情
            </el-button>
            <el-button
              link
              type="primary"
              @click="openOriginal(row.url)"
            >
              原文
            </el-button>
            <el-button
              v-permission="'agent:run:create'"
              link
              type="primary"
              :disabled="row.status === 'REJECTED'"
              :loading="processingId === row.id"
              @click="handleGenerate(row)"
            >
              智能处理
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
          @current-change="loadNews"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      size="60%"
      title="内容详情"
    >
      <el-skeleton
        v-if="detailLoading"
        :rows="8"
        animated
      />
      <div
        v-else-if="detail"
        class="detail-stack"
      >
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="标题">
            {{ detail.title }}
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            {{ detail.source_detail?.name ?? detail.source }}
          </el-descriptions-item>
          <el-descriptions-item label="来源类型">
            <StatusTag
              v-if="detail.source_detail?.source_type"
              :status="detail.source_detail.source_type"
            />
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="来源地址">
            {{ detail.source_detail?.url || detail.source_url || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ detail.category || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag :status="detail.status" />
          </el-descriptions-item>
          <el-descriptions-item label="热度">
            {{ detail.hot_score }}
          </el-descriptions-item>
          <el-descriptions-item label="语言">
            {{ detail.language }}
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">
            {{ formatDateTime(detail.publish_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(detail.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(detail.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="去重哈希" :span="2">
            {{ detail.dedup_hash || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="原文地址" :span="2">
            <a
              :href="detail.url"
              target="_blank"
              rel="noreferrer"
            >
              {{ detail.url }}
            </a>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">内容处理链路</el-divider>
        <div class="content-stage-grid">
          <div
            v-for="stage in contentStages"
            :key="stage.title"
            class="content-stage-card"
          >
            <div class="content-stage-card__header">
              <div class="content-stage-card__title">{{ stage.title }}</div>
              <StatusTag :status="stage.status" />
            </div>
            <div class="content-stage-card__summary">{{ stage.summary }}</div>
            <div
              v-if="stage.meta"
              class="content-stage-card__meta"
            >
              {{ stage.meta }}
            </div>
          </div>
        </div>

        <div class="responsive-two-col">
          <ArtifactViewer
            title="原始正文"
            :content-text="rawContent"
            empty-text="暂无原始正文"
          />
          <ArtifactViewer
            title="清洗后正文"
            :content-text="detail.content"
            empty-text="暂无清洗正文"
          />
        </div>

        <el-divider content-position="left">智能摘要</el-divider>
        <div class="news-block">{{ detail.summary || "暂无摘要" }}</div>

        <div class="responsive-two-col">
          <ArtifactViewer
            title="中文标题"
            :content-text="detail.translated_title"
            empty-text="暂无中文标题"
          />
          <ArtifactViewer
            title="分析信息"
            :content-json="analysisInfo"
            empty-text="暂无分析信息"
          />
        </div>

        <ArtifactViewer
          title="中文正文"
          :content-text="detail.translated_content"
          empty-text="暂无中文正文"
        />

        <el-divider content-position="left">处理脚本</el-divider>
        <pre class="news-pre">{{ detail.script || "暂无处理结果" }}</pre>

        <el-divider content-position="left">标签</el-divider>
        <div class="tag-row">
          <el-tag
            v-for="tag in detail.tags || []"
            :key="tag"
            effect="plain"
          >
            {{ tag }}
          </el-tag>
          <span v-if="!(detail.tags?.length)">暂无标签</span>
        </div>

        <el-divider content-position="left">过滤原因</el-divider>
        <div class="news-block">{{ detail.filter_reason || "暂无过滤原因" }}</div>

        <el-divider
          v-if="mergedSources.length"
          content-position="left"
        >
          多来源合并
        </el-divider>
        <el-table
          v-if="mergedSources.length"
          :data="mergedSources"
          size="small"
        >
          <el-table-column label="来源" min-width="140">
            <template #default="{ row }">
              {{ row.source_name || row.source_key || "-" }}
            </template>
          </el-table-column>
          <el-table-column label="模式" width="120">
            <template #default="{ row }">
              <StatusTag
                v-if="row.fetch_mode"
                :status="String(row.fetch_mode)"
              />
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="原文链接" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <a
                v-if="row.url"
                :href="String(row.url)"
                target="_blank"
                rel="noreferrer"
              >
                {{ String(row.url) }}
              </a>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="合并时间" min-width="180">
            <template #default="{ row }">
              {{ formatDateTime(String(row.merged_at || "")) }}
            </template>
          </el-table-column>
        </el-table>

        <el-divider content-position="left">Agent处理结果</el-divider>
        <div
          v-if="agentProcessing"
          class="detail-stack"
        >
          <div class="agent-summary-card">
            <div class="agent-summary-card__header">
              <div class="agent-summary-card__title">本条内容已进入 Agent 链路</div>
              <div class="linked-actions">
                <el-button
                  v-if="agentRunId"
                  link
                  type="primary"
                  @click="goToAgentRun"
                >
                  查看运行详情
                </el-button>
              </div>
            </div>
            <div class="agent-summary-card__meta">
              <span v-if="agentRunId">运行 #{{ agentRunId }}</span>
              <span v-if="agentProcessing.model_name">模型：{{ agentProcessing.model_name }}</span>
              <span v-if="agentProcessing.prompt_version">Prompt：{{ agentProcessing.prompt_version }}</span>
              <span v-if="agentProcessing.hot_topic_id">热点 #{{ agentProcessing.hot_topic_id }}</span>
              <span v-if="agentProcessing.push_plan_id">推送 #{{ agentProcessing.push_plan_id }}</span>
              <span v-if="agentProcessing.status">状态：{{ agentProcessing.status }}</span>
            </div>
          </div>

          <div class="artifact-grid">
            <ArtifactViewer
              v-for="item in processingArtifacts"
              :key="item.key"
              :title="item.title"
              :content-json="item.contentJson"
              empty-text="暂无结果"
            />
          </div>
        </div>
        <div
          v-else
          class="empty-helper"
        >
          还没有 Agent 处理结果，可以从列表页手动触发。
        </div>

        <el-divider content-position="left">采集记录</el-divider>
        <el-table :data="detail.fetch_records">
          <el-table-column prop="source_name" label="来源" min-width="140" />
          <el-table-column prop="fetch_mode" label="模式" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.fetch_mode" />
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="total_count" label="总数" width="80" />
          <el-table-column prop="new_count" label="新增" width="80" />
          <el-table-column prop="duplicate_count" label="重复" width="80" />
          <el-table-column prop="filtered_count" label="过滤" width="80" />
        </el-table>

        <div class="responsive-two-col">
          <ArtifactViewer
            title="提示词快照"
            :content-json="promptBundle"
            empty-text="暂无提示词快照"
          />
          <ArtifactViewer
            title="原始数据"
            :content-json="detail.raw_metadata"
            empty-text="暂无原始数据"
          />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped lang="scss">
.detail-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.content-stage-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.content-stage-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 132px;
  padding: 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.content-stage-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.content-stage-card__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--app-text);
}

.content-stage-card__summary {
  color: var(--app-text);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.content-stage-card__meta {
  color: var(--app-muted);
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.agent-summary-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #fbfcfe;
}

.agent-summary-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.agent-summary-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
}

.agent-summary-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  color: var(--app-muted);
  font-size: 13px;
}

.linked-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.artifact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

@media (max-width: 960px) {
  .content-stage-grid,
  .artifact-grid {
    grid-template-columns: 1fr;
  }

  .agent-summary-card__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
