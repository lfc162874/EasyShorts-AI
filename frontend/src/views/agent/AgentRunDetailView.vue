<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import AgentFlowBoard from "@/components/AgentFlowBoard.vue";
import ArtifactViewer from "@/components/ArtifactViewer.vue";
import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { getAgentRun, retryAgentRun, retryAgentRunStep } from "@/api/modules/agent";
import type { AgentRunDetailItem, AgentRunStepItem } from "@/types/agent";
import { formatDateTime } from "@/utils/format";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const actionLoading = ref(false);
const detail = ref<AgentRunDetailItem | null>(null);
const selectedStepId = ref<number | null>(null);

const runId = computed(() => Number(route.params.id));

const readRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
};

const runResult = computed(() => readRecord(detail.value?.result));
const hotTopicResult = computed(() => readRecord(runResult.value?.hot_topic));
const pushPlanResult = computed(() => readRecord(runResult.value?.push_plan));

const selectedStep = computed<AgentRunStepItem | null>(() => {
  const steps = detail.value?.steps ?? [];
  if (!steps.length) {
    return null;
  }
  if (selectedStepId.value) {
    const matched = steps.find((step) => step.id === selectedStepId.value);
    if (matched) {
      return matched;
    }
  }
  return steps.find((step) => step.step_code === detail.value?.current_step) ?? steps[0] ?? null;
});

const runDuration = computed(() => {
  if (!detail.value?.started_at) {
    return "-";
  }
  const start = new Date(detail.value.started_at).getTime();
  const end = detail.value.finished_at ? new Date(detail.value.finished_at).getTime() : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end)) {
    return "-";
  }
  const duration = Math.max(end - start, 0);
  if (duration < 1000) {
    return `${duration} ms`;
  }
  if (duration < 60_000) {
    return `${(duration / 1000).toFixed(1)} s`;
  }
  return `${(duration / 60_000).toFixed(1)} min`;
});

const hotTopicId = computed(() => {
  const rawId = hotTopicResult.value?.id;
  const parsed = Number(rawId);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
});

const pushPlanId = computed(() => {
  const rawId = pushPlanResult.value?.id;
  const parsed = Number(rawId);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
});

const loadData = async () => {
  if (!Number.isFinite(runId.value) || runId.value <= 0) {
    ElMessage.error("Agent 运行编号无效");
    await router.replace("/agent/runs");
    return;
  }

  loading.value = true;
  try {
    const response = await getAgentRun(runId.value);
    detail.value = response.data;
    selectedStepId.value =
      response.data.steps.find((step) => step.step_code === response.data.current_step)?.id ||
      response.data.steps[0]?.id ||
      null;
  } finally {
    loading.value = false;
  }
};

const refreshData = async () => {
  await loadData();
};

const goBack = () => {
  void router.push("/agent/runs");
};

const goToHotTopic = () => {
  if (!hotTopicId.value) {
    return;
  }
  void router.push(`/agent/hot-topics/${hotTopicId.value}`);
};

const goToPushPlan = () => {
  if (!pushPlanId.value) {
    return;
  }
  void router.push(`/agent/push-plans/${pushPlanId.value}`);
};

const selectStep = (step: AgentRunStepItem) => {
  selectedStepId.value = step.id;
};

const handleRetryRun = async () => {
  if (!detail.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确认重试 Agent 运行 #${detail.value.id} 吗？`,
      "重试运行",
      { type: "warning" },
    );
  } catch {
    return;
  }

  actionLoading.value = true;
  try {
    const response = await retryAgentRun(detail.value.id, {
      model_name: detail.value.model_name,
      force: true,
    });
    ElMessage.success(`已提交重试任务 #${response.data.id}`);
  } finally {
    actionLoading.value = false;
  }
};

const handleRetryStep = async () => {
  if (!detail.value || !selectedStep.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确认重试步骤「${selectedStep.value.agent_name}」吗？`,
      "重试步骤",
      { type: "warning" },
    );
  } catch {
    return;
  }

  actionLoading.value = true;
  try {
    const response = await retryAgentRunStep(detail.value.id, selectedStep.value.id, {
      model_name: selectedStep.value.model_name,
      force: true,
    });
    ElMessage.success(`已提交步骤重试任务 #${response.data.id}`);
  } finally {
    actionLoading.value = false;
  }
};

const timelineType = (status: string): "primary" | "success" | "warning" | "danger" | "info" => {
  if (status === "SUCCESS") return "success";
  if (status === "FAILED") return "danger";
  if (status === "RUNNING" || status === "RETRYING") return "warning";
  return "info";
};

const stepStats = computed(() => {
  const steps = detail.value?.steps ?? [];
  return [
    { label: "步骤数", value: String(steps.length), hint: "当前 Agent 流程包含多少步骤" },
    { label: "工件数", value: String(detail.value?.artifacts.length ?? 0), hint: "本次运行保存的结构化工件" },
    { label: "运行耗时", value: runDuration.value, hint: "从开始到结束的总耗时" },
    { label: "关联内容", value: detail.value?.biz_id ?? "-", hint: "本次运行对应的内容编号" },
  ];
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
      :title="`Agent运行 #${detail?.id ?? route.params.id}`"
      description="查看每次 Agent 智能处理的步骤、工件和关联结果。"
    >
      <el-button @click="goBack">返回列表</el-button>
      <el-button @click="refreshData">刷新</el-button>
      <el-button
        v-permission="'agent:run:retry'"
        type="primary"
        :loading="actionLoading"
        @click="handleRetryRun"
      >
        重试运行
      </el-button>
      <el-button
        v-if="hotTopicId"
        plain
        type="success"
        @click="goToHotTopic"
      >
        热点详情
      </el-button>
      <el-button
        v-if="pushPlanId"
        plain
        type="success"
        @click="goToPushPlan"
      >
        推送详情
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
      <template #header>运行概览</template>
      <el-descriptions
        v-if="detail"
        :column="2"
        border
      >
        <el-descriptions-item label="状态">
          <StatusTag :status="detail.status" />
        </el-descriptions-item>
        <el-descriptions-item label="当前步骤">
          {{ detail.current_step || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="运行类型">
          <StatusTag :status="detail.run_type" />
        </el-descriptions-item>
        <el-descriptions-item label="业务类型">
          <StatusTag :status="detail.biz_type" />
        </el-descriptions-item>
        <el-descriptions-item label="业务编号">
          {{ detail.biz_id }}
        </el-descriptions-item>
        <el-descriptions-item label="模型名称">
          {{ detail.model_name }}
        </el-descriptions-item>
        <el-descriptions-item label="提示词版本">
          {{ detail.prompt_version }}
        </el-descriptions-item>
        <el-descriptions-item label="任务编号">
          {{ detail.task_job_id || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="请求 ID">
          {{ detail.request_id || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="发起人">
          {{ detail.triggered_by ?? "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(detail.started_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ formatDateTime(detail.finished_at) }}
        </el-descriptions-item>
        <el-descriptions-item
          label="输入摘要"
          :span="2"
        >
          <div class="news-block">
            {{ detail.input_summary || "暂无输入摘要" }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item
          label="输出摘要"
          :span="2"
        >
          <div class="news-block">
            {{ detail.output_summary || "暂无输出摘要" }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item
          v-if="detail.error_message"
          label="错误信息"
          :span="2"
        >
          <div class="news-block">
            {{ detail.error_message }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <div class="responsive-two-col">
      <el-card shadow="never">
        <template #header>Agent流程</template>
        <AgentFlowBoard
          :steps="detail?.steps ?? []"
          :active-step-id="selectedStep?.id ?? null"
          @select-step="selectStep"
        />

        <el-divider content-position="left">运行结果</el-divider>
        <ArtifactViewer
          title="最终输出"
          :content-json="detail?.result"
          empty-text="暂无最终输出"
        />
      </el-card>

      <el-card shadow="never">
        <template #header>步骤时间线</template>
        <el-timeline
          v-if="detail?.steps?.length"
          class="agent-timeline"
        >
          <el-timeline-item
            v-for="step in detail.steps"
            :key="step.id"
            :type="timelineType(step.status)"
            :timestamp="formatDateTime(step.finished_at || step.started_at)"
          >
            <div
              class="agent-step-entry"
              :class="{ 'is-active': selectedStep?.id === step.id }"
              @click="selectStep(step)"
            >
              <div class="agent-step-entry__head">
                <strong>{{ step.agent_name }}</strong>
                <StatusTag :status="step.status" />
              </div>
              <div class="agent-step-entry__meta">
                #{{ step.step_order }} · {{ step.step_code }} · {{ step.duration_ms ?? 0 }} ms
              </div>
              <div class="agent-step-entry__summary">
                {{ step.output_summary || step.input_summary || "暂无摘要" }}
              </div>
              <div
                v-if="step.error_message"
                class="agent-step-entry__error"
              >
                {{ step.error_message }}
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <div
          v-else
          class="empty-helper"
        >
          暂无步骤记录
        </div>
      </el-card>
    </div>

    <el-card
      v-if="selectedStep"
      shadow="never"
    >
      <template #header>
        <div class="detail-card-header">
          <span>步骤详情</span>
          <el-button
            v-permission="'agent:run:step:retry'"
            size="small"
            :loading="actionLoading"
            @click="handleRetryStep"
          >
            重试当前步骤
          </el-button>
        </div>
      </template>

      <el-descriptions
        :column="2"
        border
      >
        <el-descriptions-item label="步骤名称">
          {{ selectedStep.agent_name }}
        </el-descriptions-item>
        <el-descriptions-item label="步骤编码">
          {{ selectedStep.step_code }}
        </el-descriptions-item>
        <el-descriptions-item label="步骤顺序">
          {{ selectedStep.step_order }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag :status="selectedStep.status" />
        </el-descriptions-item>
        <el-descriptions-item label="模型名称">
          {{ selectedStep.model_name }}
        </el-descriptions-item>
        <el-descriptions-item label="提示词版本">
          {{ selectedStep.prompt_version }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(selectedStep.started_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ formatDateTime(selectedStep.finished_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="耗时">
          {{ selectedStep.duration_ms ?? 0 }} ms
        </el-descriptions-item>
        <el-descriptions-item
          v-if="selectedStep.error_message"
          label="错误信息"
        >
          {{ selectedStep.error_message }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">输入摘要</el-divider>
      <div class="news-block">{{ selectedStep.input_summary || "暂无输入摘要" }}</div>

      <div class="responsive-two-col">
        <ArtifactViewer
          title="输入负载"
          :content-json="selectedStep.payload"
          empty-text="暂无输入负载"
        />
        <ArtifactViewer
          title="输出结果"
          :content-json="selectedStep.result"
          empty-text="暂无输出结果"
        />
      </div>
    </el-card>

    <el-card
      v-if="detail?.artifacts?.length"
      shadow="never"
    >
      <template #header>运行工件</template>
      <div class="artifact-grid">
        <ArtifactViewer
          v-for="artifact in detail.artifacts"
          :key="artifact.id"
          :title="`${artifact.artifact_type} / ${artifact.artifact_key}`"
          :content-json="artifact.content_json"
          :content-text="artifact.content_text"
          :empty-text="'暂无工件内容'"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.detail-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.agent-timeline {
  padding-left: 4px;
}

.agent-step-entry {
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: #fbfcfe;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background 0.18s ease;
}

.agent-step-entry:hover {
  border-color: rgba(31, 157, 98, 0.24);
}

.agent-step-entry.is-active {
  border-color: rgba(31, 157, 98, 0.48);
  background: rgba(31, 157, 98, 0.05);
}

.agent-step-entry__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.agent-step-entry__meta,
.agent-step-entry__summary,
.agent-step-entry__error {
  margin-top: 8px;
  color: var(--app-muted);
  font-size: 13px;
  line-height: 1.65;
}

.agent-step-entry__error {
  color: #b42318;
}

.artifact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

@media (max-width: 960px) {
  .artifact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
