<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import {
  getNewsSource,
  listNews,
  listNewsFetchRecords,
  saveNewsSource,
  syncNewsSource,
} from "@/api/modules/news";
import type { NewsFetchRecordItem, NewsItem, NewsSourceItem, NewsSourceUpsertForm } from "@/types/news";
import { formatDateTime, formatJson } from "@/utils/format";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const actionLoading = ref(false);
const source = ref<NewsSourceItem | null>(null);
const records = ref<NewsFetchRecordItem[]>([]);
const articles = ref<NewsItem[]>([]);

const sourceId = computed(() => Number(route.params.id));

const loadData = async () => {
  if (!Number.isFinite(sourceId.value) || sourceId.value <= 0) {
    ElMessage.error("来源编号无效");
    await router.replace("/news/sources");
    return;
  }

  loading.value = true;
  try {
    const [sourceResponse, recordResponse, articleResponse] = await Promise.all([
      getNewsSource(sourceId.value),
      listNewsFetchRecords({ page: 1, page_size: 5, source_id: sourceId.value }),
      listNews({ page: 1, page_size: 8, source_id: sourceId.value }),
    ]);

    source.value = sourceResponse.data;
    records.value = recordResponse.data.items;
    articles.value = articleResponse.data.items;
  } finally {
    loading.value = false;
  }
};

const handleSync = async () => {
  if (!source.value) return;
  actionLoading.value = true;
  try {
    const response = await syncNewsSource(source.value.id);
    ElMessage.success(`已提交采集任务 #${response.data.id}：${source.value.name}`);
    await loadData();
  } finally {
    actionLoading.value = false;
  }
};

const handleToggleStatus = async () => {
  if (!source.value) return;
  const nextEnabled = !source.value.is_enabled;
  const actionText = nextEnabled ? "启用" : "停用";

  try {
    await ElMessageBox.confirm(
      `确认${actionText}来源「${source.value.name}」吗？`,
      `${actionText}来源`,
      {
        type: "warning",
      },
    );
  } catch {
    return;
  }

  const payload: NewsSourceUpsertForm = {
    id: source.value.id,
    source_key: source.value.source_key,
    name: source.value.name,
    source_type: source.value.source_type,
    url: source.value.url,
    category: source.value.category,
    language: source.value.language,
    fetch_interval_minutes: source.value.fetch_interval_minutes,
    is_enabled: nextEnabled,
    extra: source.value.extra,
  };

  actionLoading.value = true;
  try {
    await saveNewsSource(payload);
    ElMessage.success(`来源已${actionText}`);
    await loadData();
  } finally {
    actionLoading.value = false;
  }
};

const goToRecords = () => {
  void router.push({
    path: "/news/records",
    query: { source_id: String(sourceId.value) },
  });
};

const goToArticles = () => {
  void router.push({
    path: "/news/list",
    query: { source_id: String(sourceId.value) },
  });
};

const goBack = () => {
  void router.push("/news/sources");
};

const editSource = () => {
  void router.push({
    path: "/news/sources",
    query: { edit: String(sourceId.value) },
  });
};

const openOriginal = (url: string) => {
  window.open(url, "_blank", "noopener,noreferrer");
};

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      :title="source?.name || '来源详情'"
      description="集中查看单个来源的配置、最近采集表现和最新内容。"
    >
      <el-button @click="goBack">返回来源管理</el-button>
      <el-button
        plain
        @click="editSource"
      >
        编辑来源
      </el-button>
      <el-button
        type="success"
        plain
        :loading="actionLoading"
        @click="handleToggleStatus"
      >
        {{ source?.is_enabled ? "停用来源" : "启用来源" }}
      </el-button>
      <el-button
        type="primary"
        :loading="actionLoading"
        @click="handleSync"
      >
        立即抓取
      </el-button>
    </PageSectionHeader>

    <el-skeleton
      v-if="loading"
      :rows="10"
      animated
    />

    <template v-else-if="source">
      <div class="responsive-two-col">
        <el-card shadow="never">
          <template #header>来源概况</template>
          <el-descriptions
            :column="2"
            border
          >
            <el-descriptions-item label="来源名称">
              {{ source.name }}
            </el-descriptions-item>
            <el-descriptions-item label="来源标识">
              {{ source.source_key }}
            </el-descriptions-item>
            <el-descriptions-item label="来源类型">
              <StatusTag :status="source.source_type" />
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <StatusTag :status="source.is_enabled ? 'ACTIVE' : 'DISABLED'" />
            </el-descriptions-item>
            <el-descriptions-item label="来源分类">
              {{ source.category || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="语言">
              {{ source.language }}
            </el-descriptions-item>
            <el-descriptions-item label="抓取频率">
              {{ source.fetch_interval_minutes }} 分钟
            </el-descriptions-item>
            <el-descriptions-item label="最近抓取">
              {{ formatDateTime(source.last_fetched_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最近成功">
              {{ formatDateTime(source.last_success_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDateTime(source.updated_at) }}
            </el-descriptions-item>
            <el-descriptions-item
              label="来源地址"
              :span="2"
            >
              <el-link
                :href="source.url"
                target="_blank"
                type="primary"
              >
                {{ source.url }}
              </el-link>
            </el-descriptions-item>
            <el-descriptions-item
              label="最近错误"
              :span="2"
            >
              {{ source.last_error_message || "暂无错误" }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <template #header>快速操作</template>
          <div class="quick-actions">
            <el-button
              type="primary"
              plain
              @click="goToRecords"
            >
              查看采集记录
            </el-button>
            <el-button
              type="primary"
              plain
              @click="goToArticles"
            >
              查看采集内容
            </el-button>
            <div class="quick-actions__hint">
              当前页面用于看单个来源的总体情况；更细的排查可以跳到记录页和内容页继续查。
            </div>
          </div>

          <el-divider content-position="left">扩展配置</el-divider>
          <pre class="news-pre">{{ formatJson(source.extra) }}</pre>
        </el-card>
      </div>

      <el-card shadow="never">
        <template #header>最近采集记录</template>
        <el-table :data="records">
          <el-table-column
            prop="id"
            label="记录 ID"
            width="90"
          />
          <el-table-column
            prop="fetch_mode"
            label="触发方式"
            width="110"
          >
            <template #default="{ row }">
              <StatusTag :status="row.fetch_mode" />
            </template>
          </el-table-column>
          <el-table-column
            label="状态"
            width="110"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="total_count" label="总数" width="80" />
          <el-table-column prop="new_count" label="新增" width="80" />
          <el-table-column prop="duplicate_count" label="重复" width="80" />
          <el-table-column prop="filtered_count" label="过滤" width="80" />
          <el-table-column
            prop="error_message"
            label="错误信息"
            min-width="220"
            show-overflow-tooltip
          />
          <el-table-column
            prop="started_at"
            label="开始时间"
            min-width="180"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.started_at) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="finished_at"
            label="结束时间"
            min-width="180"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.finished_at) }}
            </template>
          </el-table-column>
        </el-table>

        <div
          v-if="!records.length"
          class="empty-helper"
        >
          这个来源还没有采集记录，先执行一次“立即抓取”试试。
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>最近采集内容</template>
        <el-table :data="articles">
          <el-table-column
            prop="title"
            label="标题"
            min-width="280"
            show-overflow-tooltip
          />
          <el-table-column
            prop="category"
            label="分类"
            min-width="120"
          />
          <el-table-column
            label="状态"
            width="110"
          >
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column
            prop="hot_score"
            label="热度分"
            width="90"
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
            min-width="240"
            show-overflow-tooltip
          />
          <el-table-column
            label="操作"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="openOriginal(row.url)"
              >
                原文
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div
          v-if="!articles.length"
          class="empty-helper"
        >
          这个来源还没有采集到内容。
        </div>
      </el-card>
    </template>
  </div>
</template>

<style scoped lang="scss">
.quick-actions {
  display: grid;
  gap: 12px;
}

.quick-actions__hint {
  color: var(--app-muted);
  font-size: 13px;
  line-height: 1.6;
}
</style>
