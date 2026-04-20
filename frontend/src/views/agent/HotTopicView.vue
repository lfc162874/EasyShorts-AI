<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { listHotTopics } from "@/api/modules/agent";
import { hotTopicStatusOptions } from "@/constants/permissions";
import type { HotTopicItem, HotTopicStatus } from "@/types/agent";
import { formatDateTime } from "@/utils/format";

const router = useRouter();

const loading = ref(false);
const topics = ref<HotTopicItem[]>([]);
const total = ref(0);

const query = reactive({
  page: 1,
  page_size: 20,
  status: "" as "" | HotTopicStatus,
  category: "",
  keyword: "",
});

const loadTopics = async () => {
  loading.value = true;
  try {
    const response = await listHotTopics({
      page: query.page,
      page_size: query.page_size,
      status: query.status || undefined,
      category: query.category || undefined,
      keyword: query.keyword || undefined,
    });
    topics.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const refreshData = async () => {
  await loadTopics();
};

const goToDetail = (row: HotTopicItem) => {
  void router.push(`/agent/hot-topics/${row.id}`);
};

const goToRun = (row: HotTopicItem) => {
  const rawRunId = row.extra?.agent_run_id;
  const runId = Number(rawRunId);
  if (!Number.isInteger(runId) || runId <= 0) {
    return;
  }
  void router.push(`/agent/runs/${runId}`);
};

const metrics = computed(() => {
  const highScore = topics.value.filter((item) => item.score >= 80).length;
  const highPriority = topics.value.filter((item) => item.priority === "HIGH").length;
  const averageScore = topics.value.length
    ? Math.round(topics.value.reduce((sum, item) => sum + item.score, 0) / topics.value.length)
    : 0;

  return [
    { label: "热点总数", value: String(total.value), hint: "当前筛选条件下的热点结果" },
    { label: "高分热点", value: String(highScore), hint: "当前页评分 80 以上的热点" },
    { label: "高优先级", value: String(highPriority), hint: "当前页 HIGH 优先级热点" },
    { label: "平均热度", value: String(averageScore), hint: "当前页平均评分" },
  ];
});

onMounted(loadTopics);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="热点池"
      description="查看 Agent 聚合后的热点结果、评分、标签和趋势判断。"
    >
      <el-button @click="refreshData">刷新</el-button>
    </PageSectionHeader>

    <div class="grid-cards">
      <MetricCard
        v-for="metric in metrics"
        :key="metric.label"
        :label="metric.label"
        :value="metric.value"
        :hint="metric.hint"
      />
    </div>

    <el-card shadow="never">
      <el-form
        :inline="true"
        class="toolbar-form"
      >
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            clearable
            placeholder="标题 / 摘要 / 理由"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="query.status"
            clearable
            placeholder="全部"
            style="width: 140px"
          >
            <el-option
              v-for="item in hotTopicStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input
            v-model="query.category"
            clearable
            placeholder="AI Agent / 开源生态"
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="loadTopics">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="topics"
      >
        <el-table-column
          prop="title"
          label="热点标题"
          min-width="260"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <el-link
              type="primary"
              @click="goToDetail(row)"
            >
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column
          prop="category"
          label="分类"
          width="130"
        />
        <el-table-column
          label="标签"
          min-width="220"
        >
          <template #default="{ row }">
            <div class="tag-row">
              <el-tag
                v-for="tag in row.tags || []"
                :key="tag"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
              <span v-if="!(row.tags?.length)">暂无标签</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="score"
          label="热度分"
          width="100"
        />
        <el-table-column
          prop="priority"
          label="优先级"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.priority" />
          </template>
        </el-table-column>
        <el-table-column
          prop="trend"
          label="趋势"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.trend || 'STABLE'" />
          </template>
        </el-table-column>
        <el-table-column
          prop="news_count"
          label="内容数量"
          width="100"
        />
        <el-table-column
          prop="source_count"
          label="来源数"
          width="90"
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
          prop="model_name"
          label="模型"
          min-width="160"
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
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="goToDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-if="row.extra?.agent_run_id"
              link
              type="primary"
              @click="goToRun(row)"
            >
              运行链路
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
          @current-change="loadTopics"
        />
      </div>
    </el-card>
  </div>
</template>
