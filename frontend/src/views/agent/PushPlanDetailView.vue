<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import ArtifactViewer from "@/components/ArtifactViewer.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { executePushPlan, getPushPlan } from "@/api/modules/agent";
import type { PushPlanDetailItem } from "@/types/agent";
import { formatDateTime } from "@/utils/format";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const actionLoading = ref(false);
const detail = ref<PushPlanDetailItem | null>(null);

const planId = computed(() => Number(route.params.id));

const readRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
};

const goBack = () => {
  void router.push("/agent/push-plans");
};

const goToTopic = () => {
  if (!detail.value?.topic?.id) {
    return;
  }
  void router.push(`/agent/hot-topics/${detail.value.topic.id}`);
};

const goToRun = () => {
  if (!detail.value?.run?.id) {
    return;
  }
  void router.push(`/agent/runs/${detail.value.run.id}`);
};

const loadData = async () => {
  if (!Number.isFinite(planId.value) || planId.value <= 0) {
    ElMessage.error("推送计划编号无效");
    await router.replace("/agent/push-plans");
    return;
  }

  loading.value = true;
  try {
    const response = await getPushPlan(planId.value);
    detail.value = response.data;
  } finally {
    loading.value = false;
  }
};

const refreshData = async () => {
  await loadData();
};

const handleExecute = async () => {
  if (!detail.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确认执行推送计划 #${detail.value.id} 吗？`,
      "执行推送",
      { type: "warning" },
    );
  } catch {
    return;
  }

  actionLoading.value = true;
  try {
    await executePushPlan(detail.value.id);
    ElMessage.success(`推送计划 #${detail.value.id} 已执行`);
    await loadData();
  } finally {
    actionLoading.value = false;
  }
};

const runExtras = computed(() => readRecord(detail.value?.extra ?? null));
const topicExtras = computed(() => readRecord(detail.value?.topic?.extra ?? null));

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
      :title="`推送计划 #${detail?.id ?? route.params.id}`"
      description="查看推送决策、关联热点和执行状态。"
    >
      <el-button @click="goBack">返回列表</el-button>
      <el-button @click="refreshData">刷新</el-button>
      <el-button
        v-permission="'agent:push-plan:execute'"
        type="primary"
        :loading="actionLoading"
        :disabled="detail?.status === 'EXECUTED' || detail?.status === 'CANCELLED'"
        @click="handleExecute"
      >
        执行推送
      </el-button>
      <el-button
        v-if="detail?.topic?.id"
        plain
        type="success"
        @click="goToTopic"
      >
        热点详情
      </el-button>
      <el-button
        v-if="detail?.run?.id"
        plain
        type="success"
        @click="goToRun"
      >
        运行详情
      </el-button>
    </PageSectionHeader>

    <el-card
      v-loading="loading"
      shadow="never"
    >
      <template #header>计划概览</template>
      <el-descriptions
        v-if="detail"
        :column="2"
        border
      >
        <el-descriptions-item label="状态">
          <StatusTag :status="detail.status" />
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <StatusTag :status="detail.priority" />
        </el-descriptions-item>
        <el-descriptions-item label="推送类型">
          <StatusTag :status="detail.push_type" />
        </el-descriptions-item>
        <el-descriptions-item label="立即推送">
          <StatusTag :status="detail.push_now ? 'ACTIVE' : 'DISABLED'" />
        </el-descriptions-item>
        <el-descriptions-item label="业务类型">
          <StatusTag :status="detail.biz_type" />
        </el-descriptions-item>
        <el-descriptions-item label="关联编号">
          {{ detail.biz_id }}
        </el-descriptions-item>
        <el-descriptions-item label="运行 ID">
          {{ detail.run_id ?? "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="热点 ID">
          {{ detail.topic_id ?? "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="模型名称">
          {{ detail.model_name }}
        </el-descriptions-item>
        <el-descriptions-item label="提示词版本">
          {{ detail.prompt_version }}
        </el-descriptions-item>
        <el-descriptions-item label="计划时间">
          {{ formatDateTime(detail.planned_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="执行时间">
          {{ formatDateTime(detail.executed_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="理由" :span="2">
          <div class="news-block">{{ detail.reason || "暂无推送理由" }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="渠道" :span="2">
          <div class="tag-row">
            <el-tag
              v-for="channel in detail.channels || []"
              :key="channel"
              effect="plain"
            >
              {{ channel }}
            </el-tag>
            <span v-if="!(detail.channels?.length)">暂无渠道</span>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <div class="responsive-two-col">
      <el-card shadow="never">
        <template #header>关联热点</template>
        <template v-if="detail?.topic">
          <el-descriptions
            :column="2"
            border
          >
            <el-descriptions-item label="标题">
              {{ detail.topic.title }}
            </el-descriptions-item>
            <el-descriptions-item label="分类">
              {{ detail.topic.category || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="热度分">
              {{ detail.topic.score }}
            </el-descriptions-item>
            <el-descriptions-item label="优先级">
              <StatusTag :status="detail.topic.priority" />
            </el-descriptions-item>
            <el-descriptions-item label="趋势">
              <StatusTag :status="detail.topic.trend || 'STABLE'" />
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <StatusTag :status="detail.topic.status" />
            </el-descriptions-item>
            <el-descriptions-item label="摘要" :span="2">
              <div class="news-block">{{ detail.topic.summary || "暂无摘要" }}</div>
            </el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">标签</el-divider>
          <div class="tag-row">
            <el-tag
              v-for="tag in detail.topic.tags || []"
              :key="tag"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
            <span v-if="!(detail.topic.tags?.length)">暂无标签</span>
          </div>
        </template>
        <div
          v-else
          class="empty-helper"
        >
          这条计划没有关联热点。
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>关联运行</template>
        <template v-if="detail?.run">
          <el-descriptions
            :column="2"
            border
          >
            <el-descriptions-item label="运行状态">
              <StatusTag :status="detail.run.status" />
            </el-descriptions-item>
            <el-descriptions-item label="当前步骤">
              {{ detail.run.current_step || "-" }}
            </el-descriptions-item>
            <el-descriptions-item label="模型名称">
              {{ detail.run.model_name }}
            </el-descriptions-item>
            <el-descriptions-item label="业务编号">
              {{ detail.run.biz_id }}
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              {{ formatDateTime(detail.run.started_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="结束时间">
              {{ formatDateTime(detail.run.finished_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">运行输出</el-divider>
          <ArtifactViewer
            title="Agent运行结果"
            :content-json="detail.run.result"
            empty-text="暂无运行结果"
          />
        </template>
        <div
          v-else
          class="empty-helper"
        >
          这条计划没有关联运行。
        </div>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header>扩展信息</template>
      <ArtifactViewer
        title="计划扩展配置"
        :content-json="runExtras"
        empty-text="暂无扩展信息"
      />
      <el-divider content-position="left">热点扩展</el-divider>
      <ArtifactViewer
        title="关联热点扩展"
        :content-json="topicExtras"
        empty-text="暂无热点扩展信息"
      />
    </el-card>
  </div>
</template>
