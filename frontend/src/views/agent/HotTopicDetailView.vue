<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import AgentFlowBoard from "@/components/AgentFlowBoard.vue";
import ArtifactViewer from "@/components/ArtifactViewer.vue";
import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { getAgentRun, getHotTopic } from "@/api/modules/agent";
import type { AgentRunDetailItem, HotTopicDetailItem, HotTopicNewsItem } from "@/types/agent";
import { formatDateTime } from "@/utils/format";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const topic = ref<HotTopicDetailItem | null>(null);
const relatedRun = ref<AgentRunDetailItem | null>(null);
const relatedRunLoading = ref(false);

const topicId = computed(() => Number(route.params.id));

const readRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
};

const relatedRunId = computed(() => {
  const rawId = readRecord(topic.value?.extra ?? null)?.agent_run_id;
  const parsed = Number(rawId);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
});

const loadData = async () => {
  if (!Number.isFinite(topicId.value) || topicId.value <= 0) {
    ElMessage.error("热点编号无效");
    await router.replace("/agent/hot-topics");
    return;
  }

  loading.value = true;
  relatedRunLoading.value = true;
  try {
    const response = await getHotTopic(topicId.value);
    topic.value = response.data;

    if (relatedRunId.value) {
      const runResponse = await getAgentRun(relatedRunId.value);
      relatedRun.value = runResponse.data;
    } else {
      relatedRun.value = null;
    }
  } finally {
    loading.value = false;
    relatedRunLoading.value = false;
  }
};

const refreshData = async () => {
  await loadData();
};

const goBack = () => {
  void router.push("/agent/hot-topics");
};

const goToRun = () => {
  if (!relatedRunId.value) {
    return;
  }
  void router.push(`/agent/runs/${relatedRunId.value}`);
};

const openOriginal = (url: string) => {
  window.open(url, "_blank", "noopener,noreferrer");
};

const goToContent = (item: HotTopicNewsItem) => {
  window.open(item.url, "_blank", "noopener,noreferrer");
};

const stepStats = computed(() => {
  const steps = relatedRun.value?.steps ?? [];
  return [
    { label: "关联内容", value: String(topic.value?.news_count ?? 0), hint: "热点关联的原始内容数" },
    { label: "来源数", value: String(topic.value?.source_count ?? 0), hint: "热点来自多少个来源" },
    { label: "运行步骤", value: String(steps.length), hint: "关联 Agent 运行包含的步骤数" },
    { label: "运行工件", value: String(relatedRun.value?.artifacts.length ?? 0), hint: "本次运行工件数量" },
  ];
});

const relatedRunActiveStepId = computed(() => {
  const run = relatedRun.value;
  if (!run) {
    return null;
  }
  return run.steps.find((step) => step.step_code === run.current_step)?.id ?? null;
});

watch(
  () => route.params.id,
  async () => {
    await loadData();
  },
);

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      :title="topic?.title || '热点详情'"
      description="查看单个热点的完整结果、关联内容和智能处理链路。"
    >
      <el-button @click="goBack">返回热点池</el-button>
      <el-button @click="refreshData">刷新</el-button>
      <el-button
        v-if="relatedRunId"
        type="primary"
        plain
        @click="goToRun"
      >
        查看运行链路
      </el-button>
    </PageSectionHeader>

    <div class="grid-cards">
      <MetricCard
        v-for="metric in stepStats"
        :key="metric.label"
        :label="metric.label"
        :value="metric.value"
        :hint="metric.hint"
      />
    </div>

    <el-card
      v-loading="loading"
      shadow="never"
    >
      <template #header>热点概览</template>
      <el-descriptions
        v-if="topic"
        :column="2"
        border
      >
        <el-descriptions-item label="状态">
          <StatusTag :status="topic.status" />
        </el-descriptions-item>
        <el-descriptions-item label="分类">
          {{ topic.category || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="热度分">
          {{ topic.score }}
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <StatusTag :status="topic.priority" />
        </el-descriptions-item>
        <el-descriptions-item label="趋势">
          <StatusTag :status="topic.trend || 'STABLE'" />
        </el-descriptions-item>
        <el-descriptions-item label="模型名称">
          {{ topic.model_name }}
        </el-descriptions-item>
        <el-descriptions-item label="提示词版本">
          {{ topic.prompt_version }}
        </el-descriptions-item>
        <el-descriptions-item label="热点键值">
          <span class="mono-text">{{ topic.topic_key }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="主内容 ID">
          {{ topic.primary_news_id ?? "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="理由" :span="2">
          <div class="news-block">{{ topic.reason || "暂无推荐理由" }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="摘要" :span="2">
          <div class="news-block">{{ topic.summary || "暂无摘要" }}</div>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">标签</el-divider>
      <div class="tag-row">
        <el-tag
          v-for="tag in topic?.tags || []"
          :key="tag"
          effect="plain"
        >
          {{ tag }}
        </el-tag>
        <span v-if="!(topic?.tags?.length)">暂无标签</span>
      </div>
    </el-card>

    <el-card
      v-loading="relatedRunLoading"
      shadow="never"
    >
      <template #header>Agent处理结果</template>
      <template v-if="relatedRun">
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="运行 ID">
            {{ relatedRun.id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag :status="relatedRun.status" />
          </el-descriptions-item>
          <el-descriptions-item label="当前步骤">
            {{ relatedRun.current_step || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="模型名称">
            {{ relatedRun.model_name }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatDateTime(relatedRun.started_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ formatDateTime(relatedRun.finished_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="输入摘要" :span="2">
            <div class="news-block">{{ relatedRun.input_summary || "暂无输入摘要" }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="输出摘要" :span="2">
            <div class="news-block">{{ relatedRun.output_summary || "暂无输出摘要" }}</div>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">流程图</el-divider>
        <AgentFlowBoard
          :steps="relatedRun.steps"
          :active-step-id="relatedRunActiveStepId"
        />

        <el-divider content-position="left">运行结果</el-divider>
        <ArtifactViewer
          title="Agent运行输出"
          :content-json="relatedRun.result"
          empty-text="暂无运行输出"
        />
      </template>
      <div
        v-else
        class="empty-helper"
      >
        这条热点还没有关联到 Agent 运行记录。
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>关联内容</template>
      <el-table :data="topic?.items ?? []">
        <el-table-column
          prop="title"
          label="内容标题"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column
          prop="source_name"
          label="来源"
          min-width="160"
        />
        <el-table-column
          prop="weight"
          label="权重"
          width="90"
        />
        <el-table-column
          prop="is_primary"
          label="主内容"
          width="90"
        >
          <template #default="{ row }">
            <StatusTag :status="row.is_primary ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="关联时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="150"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="openOriginal(row.url)"
            >
              原文
            </el-button>
            <el-button
              link
              type="primary"
              @click="goToContent(row)"
            >
              打开内容
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>扩展信息</template>
      <ArtifactViewer
        title="热点扩展配置"
        :content-json="topic?.extra"
        empty-text="暂无扩展信息"
      />
    </el-card>
  </div>
</template>
