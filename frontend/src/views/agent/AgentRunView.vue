<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";

import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import {
  listAgentModels,
  listAgentRuns,
  retryAgentRun,
  triggerAgentRun,
} from "@/api/modules/agent";
import {
  agentBizTypeOptions,
  agentRunStatusOptions,
  agentRunTypeOptions,
} from "@/constants/permissions";
import type { AgentModelItem, AgentRunItem, AgentRunStatus } from "@/types/agent";
import { resolveAgentModelOptions, resolveDefaultAgentModel } from "@/utils/agent";
import { formatDateTime } from "@/utils/format";

const router = useRouter();

const loading = ref(false);
const actionLoading = ref(false);
const retryingId = ref<number | null>(null);
const runs = ref<AgentRunItem[]>([]);
const total = ref(0);
const modelOptions = ref<AgentModelItem[]>([]);
const triggerDialogVisible = ref(false);
const triggerNewsId = ref<number | null>(null);
const triggerForce = ref(true);
const selectedModel = ref("");

const query = reactive({
  page: 1,
  page_size: 20,
  status: "" as "" | AgentRunStatus,
  run_type: "" as "" | AgentRunItem["run_type"],
  biz_type: "" as "" | AgentRunItem["biz_type"],
  model_name: "",
  keyword: "",
});

const loadModels = async () => {
  const response = await listAgentModels();
  modelOptions.value = resolveAgentModelOptions(response.data);
  selectedModel.value = resolveDefaultAgentModel(modelOptions.value, selectedModel.value);
};

const loadRuns = async () => {
  loading.value = true;
  try {
    const response = await listAgentRuns({
      page: query.page,
      page_size: query.page_size,
      status: query.status || undefined,
      run_type: query.run_type || undefined,
      biz_type: query.biz_type || undefined,
      model_name: query.model_name || undefined,
      keyword: query.keyword || undefined,
    });
    runs.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const loadData = async () => {
  await Promise.all([loadModels(), loadRuns()]);
};

const openTriggerDialog = () => {
  triggerNewsId.value = null;
  triggerForce.value = true;
  selectedModel.value = selectedModel.value || modelOptions.value[0]?.value || "";
  triggerDialogVisible.value = true;
};

const handleTriggerRun = async () => {
  if (!triggerNewsId.value || triggerNewsId.value <= 0) {
    ElMessage.warning("请输入有效的内容编号");
    return;
  }

  actionLoading.value = true;
  try {
    const response = await triggerAgentRun(triggerNewsId.value, {
      model_name: selectedModel.value || undefined,
      force: triggerForce.value,
    });
    ElMessage.success(`已提交 Agent 运行任务 #${response.data.id}`);
    triggerDialogVisible.value = false;
    await loadRuns();
  } finally {
    actionLoading.value = false;
  }
};

const handleRetry = async (row: AgentRunItem) => {
  try {
    await ElMessageBox.confirm(
      `确认重试 Agent 运行 #${row.id} 吗？`,
      "重试运行",
      { type: "warning" },
    );
  } catch {
    return;
  }

  retryingId.value = row.id;
  try {
    const response = await retryAgentRun(row.id, {
      model_name: row.model_name,
      force: true,
    });
    ElMessage.success(`已提交重试任务 #${response.data.id}`);
    await loadRuns();
  } finally {
    retryingId.value = null;
  }
};

const goToDetail = (row: AgentRunItem) => {
  void router.push(`/agent/runs/${row.id}`);
};

const refreshData = async () => {
  await loadRuns();
};

const runStats = computed(() => {
  const running = runs.value.filter((item) => item.status === "RUNNING").length;
  const success = runs.value.filter((item) => item.status === "SUCCESS").length;
  const failed = runs.value.filter((item) => item.status === "FAILED").length;
  const averageDuration = (() => {
    const durations = runs.value
      .map((item) => {
        if (!item.started_at || !item.finished_at) {
          return null;
        }
        const start = new Date(item.started_at).getTime();
        const end = new Date(item.finished_at).getTime();
        return Number.isNaN(start) || Number.isNaN(end) ? null : Math.max(end - start, 0);
      })
      .filter((item): item is number => item !== null);
    if (!durations.length) {
      return "-";
    }
    const totalDuration = durations.reduce((sum, value) => sum + value, 0);
    const averageDurationMs = totalDuration / durations.length;
    if (averageDurationMs < 1000) {
      return `${Math.round(averageDurationMs)} ms`;
    }
    if (averageDurationMs < 60_000) {
      return `${(averageDurationMs / 1000).toFixed(1)} s`;
    }
    return `${(averageDurationMs / 60_000).toFixed(1)} min`;
  })();

  return [
    { label: "运行总数", value: String(total.value), hint: "当前筛选条件下的运行记录" },
    { label: "运行中", value: String(running), hint: "当前页中的运行中任务" },
    { label: "成功", value: String(success), hint: "当前页中的成功任务" },
    { label: "失败", value: String(failed), hint: `平均耗时：${averageDuration}` },
  ];
});

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="Agent运行"
      description="在这里查看每次内容智能处理的运行链路、步骤结果和重试记录。"
    >
      <el-button @click="refreshData">刷新</el-button>
      <el-button
        v-permission="'agent:run:create'"
        type="primary"
        @click="openTriggerDialog"
      >
        触发内容处理
      </el-button>
    </PageSectionHeader>

    <div class="grid-cards">
      <MetricCard
        v-for="metric in runStats"
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
            placeholder="输入摘要、业务编号或模型"
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
              v-for="item in agentRunStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="query.run_type"
            clearable
            placeholder="全部"
            style="width: 160px"
          >
            <el-option
              v-for="item in agentRunTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="业务">
          <el-select
            v-model="query.biz_type"
            clearable
            placeholder="全部"
            style="width: 150px"
          >
            <el-option
              v-for="item in agentBizTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select
            v-model="query.model_name"
            clearable
            filterable
            placeholder="全部"
            style="width: 220px"
          >
            <el-option
              v-for="item in modelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadRuns">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="runs"
      >
        <el-table-column
          prop="id"
          label="运行 ID"
          width="100"
        />
        <el-table-column
          prop="run_type"
          label="运行类型"
          width="130"
        >
          <template #default="{ row }">
            <StatusTag :status="row.run_type" />
          </template>
        </el-table-column>
        <el-table-column
          prop="biz_type"
          label="业务类型"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.biz_type" />
          </template>
        </el-table-column>
        <el-table-column
          prop="biz_id"
          label="关联对象"
          width="120"
        />
        <el-table-column
          prop="current_step"
          label="当前步骤"
          width="140"
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
          prop="model_name"
          label="模型"
          min-width="180"
        />
        <el-table-column
          prop="input_summary"
          label="输入摘要"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column
          prop="output_summary"
          label="输出摘要"
          min-width="260"
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
              v-permission="'agent:run:retry'"
              link
              type="primary"
              :loading="retryingId === row.id"
              @click="handleRetry(row)"
            >
              重试
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
          @current-change="loadRuns"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="triggerDialogVisible"
      title="触发内容智能处理"
      width="560px"
    >
      <el-form label-position="top">
        <el-form-item label="内容编号">
          <el-input-number
            v-model="triggerNewsId"
            :min="1"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="模型">
          <el-select
            v-model="selectedModel"
            filterable
            allow-create
            default-first-option
            placeholder="使用默认模型"
            style="width: 100%"
          >
            <el-option
              v-for="item in modelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-switch
            v-model="triggerForce"
            inline-prompt
            active-text="强制"
            inactive-text="普通"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="triggerDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="actionLoading"
          @click="handleTriggerRun"
        >
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
