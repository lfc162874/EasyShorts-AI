<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getDashboardOverview } from "@/api/modules/dashboard";
import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import type { DashboardOverview } from "@/types/system";

const loading = ref(false);
const overview = ref<DashboardOverview | null>(null);

const loadData = async () => {
  loading.value = true;
  try {
    overview.value = await getDashboardOverview();
  } finally {
    loading.value = false;
  }
};

onMounted(loadData);
</script>

<template>
  <div
    v-loading="loading"
    class="page-shell"
  >
    <PageSectionHeader
      title="工作台"
      description="这里展示后端底座的健康状态、核心资源总量和最近的操作痕迹。"
    >
      <el-button
        type="primary"
        @click="loadData"
      >
        刷新数据
      </el-button>
    </PageSectionHeader>

    <div class="grid-cards">
      <MetricCard
        v-for="metric in overview?.metrics ?? []"
        :key="metric.label"
        :label="metric.label"
        :value="metric.value"
        :hint="metric.hint"
        :trend="metric.trend"
      />
    </div>

    <div class="responsive-two-col">
      <el-card shadow="never">
        <template #header>后端健康状态</template>
        <el-descriptions
          v-if="overview"
          :column="1"
          border
        >
          <el-descriptions-item label="服务名称">
            {{ overview.health.service }}
          </el-descriptions-item>
          <el-descriptions-item label="运行环境">
            {{ overview.health.environment }}
          </el-descriptions-item>
          <el-descriptions-item label="API 前缀">
            {{ overview.health.api_prefix }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never">
        <template #header>最近任务</template>
        <div
          v-for="task in overview?.recent_tasks ?? []"
          :key="task.id"
          class="task-preview"
        >
          <div class="task-preview__main">
            <div class="task-preview__title">{{ task.task_name }}</div>
            <div class="task-preview__meta">
              {{ task.task_type }} / {{ task.queue_name }}
            </div>
          </div>
          <StatusTag :status="task.status" />
        </div>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header>最近操作</template>
      <el-table
        v-if="overview"
        :data="overview.activity"
      >
        <el-table-column
          prop="module"
          label="模块"
          width="140"
        />
        <el-table-column
          prop="action"
          label="动作"
          width="140"
        />
        <el-table-column
          prop="operator_name"
          label="操作者"
          width="140"
        />
        <el-table-column
          prop="message"
          label="说明"
          min-width="280"
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
          prop="created_at"
          label="时间"
          min-width="180"
        />
      </el-table>
    </el-card>
  </div>
</template>
