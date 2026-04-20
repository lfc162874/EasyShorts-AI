<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";

import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { executePushPlan, listPushPlans } from "@/api/modules/agent";
import { pushPlanStatusOptions, agentBizTypeOptions } from "@/constants/permissions";
import type { PushPlanItem, PushPlanStatus } from "@/types/agent";
import { formatDateTime } from "@/utils/format";

const router = useRouter();

const loading = ref(false);
const executeLoadingId = ref<number | null>(null);
const plans = ref<PushPlanItem[]>([]);
const total = ref(0);

const query = reactive({
  page: 1,
  page_size: 20,
  status: "" as "" | PushPlanStatus,
  biz_type: "" as "" | PushPlanItem["biz_type"],
  keyword: "",
});

const loadPlans = async () => {
  loading.value = true;
  try {
    const response = await listPushPlans({
      page: query.page,
      page_size: query.page_size,
      status: query.status || undefined,
      biz_type: query.biz_type || undefined,
      keyword: query.keyword || undefined,
    });
    plans.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const refreshData = async () => {
  await loadPlans();
};

const goToDetail = (row: PushPlanItem) => {
  void router.push(`/agent/push-plans/${row.id}`);
};

const handleExecute = async (row: PushPlanItem) => {
  try {
    await ElMessageBox.confirm(
      `确认执行推送计划 #${row.id} 吗？`,
      "执行推送",
      { type: "warning" },
    );
  } catch {
    return;
  }

  executeLoadingId.value = row.id;
  try {
    await executePushPlan(row.id);
    ElMessage.success(`推送计划 #${row.id} 已执行`);
    await loadPlans();
  } finally {
    executeLoadingId.value = null;
  }
};

const metrics = computed(() => {
  const executed = plans.value.filter((item) => item.status === "EXECUTED").length;
  const scheduled = plans.value.filter((item) => item.status === "SCHEDULED").length;
  const failed = plans.value.filter((item) => item.status === "FAILED").length;
  const immediate = plans.value.filter((item) => item.push_now).length;

  return [
    { label: "计划总数", value: String(total.value), hint: "当前筛选条件下的推送计划" },
    { label: "即时推送", value: String(immediate), hint: "当前页 push_now 为 true 的计划" },
    { label: "已执行", value: String(executed), hint: "当前页已执行计划数" },
    { label: "待调度", value: String(scheduled), hint: `当前页计划中已有 ${failed} 条失败记录` },
  ];
});

onMounted(loadPlans);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="推送计划"
      description="查看 PushPlannerAgent 输出的推送决策和执行状态。"
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
            placeholder="理由 / 编号 / 模型"
            style="width: 240px"
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
              v-for="item in pushPlanStatusOptions"
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
        <el-form-item>
          <el-button @click="loadPlans">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="plans"
      >
        <el-table-column
          prop="id"
          label="计划 ID"
          width="100"
        />
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
          prop="run_id"
          label="运行 ID"
          width="100"
        />
        <el-table-column
          prop="topic_id"
          label="热点 ID"
          width="100"
        />
        <el-table-column
          prop="push_now"
          label="立即推送"
          width="100"
        >
          <template #default="{ row }">
            <StatusTag :status="row.push_now ? 'ACTIVE' : 'DISABLED'" />
          </template>
        </el-table-column>
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
          prop="push_type"
          label="推送类型"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.push_type" />
          </template>
        </el-table-column>
        <el-table-column
          label="渠道"
          min-width="180"
        >
          <template #default="{ row }">
            <div class="tag-row">
              <el-tag
                v-for="channel in row.channels || []"
                :key="channel"
                effect="plain"
              >
                {{ channel }}
              </el-tag>
              <span v-if="!(row.channels?.length)">暂无渠道</span>
            </div>
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
        <el-table-column
          prop="planned_at"
          label="计划时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.planned_at) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="executed_at"
          label="执行时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.executed_at) }}
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
              v-permission="'agent:push-plan:execute'"
              link
              type="primary"
              :loading="executeLoadingId === row.id"
              :disabled="row.status === 'EXECUTED' || row.status === 'CANCELLED'"
              @click="handleExecute(row)"
            >
              执行
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
          @current-change="loadPlans"
        />
      </div>
    </el-card>
  </div>
</template>
