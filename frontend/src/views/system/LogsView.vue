<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { listErrorLogs, listOperationLogs } from "@/api/modules/system";
import type { ErrorLogItem, OperationLogItem } from "@/types/system";

const activeTab = ref<"operations" | "errors">("operations");
const loading = ref(false);
const operationLogs = ref<OperationLogItem[]>([]);
const errorLogs = ref<ErrorLogItem[]>([]);
const total = ref(0);
const query = reactive({
  page: 1,
  page_size: 20,
});

const loadOperations = async () => {
  loading.value = true;
  try {
    const response = await listOperationLogs(query);
    operationLogs.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const loadErrors = async () => {
  loading.value = true;
  try {
    const response = await listErrorLogs(query);
    errorLogs.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const loadData = async () => {
  if (activeTab.value === "operations") {
    await loadOperations();
    return;
  }
  await loadErrors();
};

watch(activeTab, async () => {
  query.page = 1;
  await loadData();
});

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="日志中心"
      description="后端已经拆成操作日志与错误日志两个列表，这里按标签页切换查看。"
    />

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane
          label="操作日志"
          name="operations"
        />
        <el-tab-pane
          label="错误日志"
          name="errors"
        />
      </el-tabs>

      <el-table
        v-loading="loading"
        :data="activeTab === 'operations' ? operationLogs : errorLogs"
        style="margin-top: 8px"
      >
        <template v-if="activeTab === 'operations'">
          <el-table-column
            prop="module"
            label="模块"
            min-width="140"
          />
          <el-table-column
            prop="action"
            label="动作"
            min-width="140"
          />
          <el-table-column
            prop="operator_name"
            label="操作者"
            min-width="140"
          />
          <el-table-column
            prop="path"
            label="路径"
            min-width="220"
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
            prop="request_id"
            label="Request ID"
            min-width="160"
          />
          <el-table-column
            prop="created_at"
            label="时间"
            min-width="180"
          />
        </template>

        <template v-else>
          <el-table-column
            prop="error_type"
            label="错误类型"
            min-width="180"
          />
          <el-table-column
            prop="error_code"
            label="错误码"
            width="110"
          />
          <el-table-column
            prop="error_message"
            label="错误信息"
            min-width="320"
          />
          <el-table-column
            prop="path"
            label="路径"
            min-width="220"
          />
          <el-table-column
            prop="method"
            label="方法"
            width="100"
          />
          <el-table-column
            prop="request_id"
            label="Request ID"
            min-width="160"
          />
          <el-table-column
            prop="created_at"
            label="时间"
            min-width="180"
          />
        </template>
      </el-table>

      <div class="pagination-row">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          layout="total, prev, pager, next"
          :total="total"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>
