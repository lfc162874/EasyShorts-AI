<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { createDemoTask, listTasks } from "@/api/modules/system";
import type { DemoTaskPayload, TaskJobItem } from "@/types/system";

const loading = ref(false);
const tasks = ref<TaskJobItem[]>([]);
const total = ref(0);
const dialogVisible = ref(false);
const demoMessage = ref("hello");
const query = reactive({
  page: 1,
  page_size: 20,
});

const loadData = async () => {
  loading.value = true;
  try {
    const response = await listTasks(query);
    tasks.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const openDemoDialog = () => {
  demoMessage.value = "hello";
  dialogVisible.value = true;
};

const handleCreateDemoTask = async () => {
  const payload: DemoTaskPayload = {
    payload: { message: demoMessage.value },
  };
  await createDemoTask(payload);
  ElMessage.success("演示任务已派发");
  dialogVisible.value = false;
  await loadData();
};

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="任务中心"
      description="任务列表来自后端真实 Celery 任务记录，演示任务可以立即验证链路。"
    >
      <el-button
        v-permission="'system:task:list'"
        type="primary"
        @click="openDemoDialog"
      >
        派发演示任务
      </el-button>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="tasks"
      >
        <el-table-column
          prop="task_name"
          label="任务名称"
          min-width="220"
        />
        <el-table-column
          prop="task_type"
          label="任务类型"
          width="120"
        />
        <el-table-column
          prop="queue_name"
          label="队列"
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
          prop="progress"
          label="进度"
          width="100"
        >
          <template #default="{ row }">
            {{ row.progress }}%
          </template>
        </el-table-column>
        <el-table-column
          prop="retry_count"
          label="重试"
          width="90"
        />
        <el-table-column
          prop="celery_task_id"
          label="Celery ID"
          min-width="180"
        />
        <el-table-column
          prop="request_id"
          label="Request ID"
          min-width="160"
        />
        <el-table-column
          prop="error_message"
          label="错误信息"
          min-width="240"
        />
        <el-table-column
          prop="started_at"
          label="开始时间"
          min-width="180"
        />
        <el-table-column
          prop="finished_at"
          label="结束时间"
          min-width="180"
        />
        <el-table-column
          prop="created_at"
          label="创建时间"
          min-width="180"
        />
        <el-table-column
          prop="updated_at"
          label="更新时间"
          min-width="180"
        />
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

    <el-dialog
      v-model="dialogVisible"
      title="派发演示任务"
      width="520px"
    >
      <el-form label-position="top">
        <el-form-item label="消息内容">
          <el-input
            v-model="demoMessage"
            placeholder="输入一个简单消息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleCreateDemoTask"
        >
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
