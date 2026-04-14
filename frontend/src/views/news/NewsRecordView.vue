<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { getNewsFetchRecord, listNewsFetchRecords, listNewsSources } from "@/api/modules/news";
import { taskStatusOptions } from "@/constants/permissions";
import type { NewsFetchRecordItem, NewsSourceItem } from "@/types/news";
import { formatDateTime, formatJson } from "@/utils/format";

const loading = ref(false);
const detailVisible = ref(false);
const detailLoading = ref(false);
const records = ref<NewsFetchRecordItem[]>([]);
const sources = ref<NewsSourceItem[]>([]);
const detail = ref<NewsFetchRecordItem | null>(null);
const total = ref(0);

const query = reactive({
  page: 1,
  page_size: 20,
  source_id: "" as "" | number,
  status: "" as "" | NewsFetchRecordItem["status"],
});

const loadSources = async () => {
  const response = await listNewsSources({ page: 1, page_size: 200 });
  sources.value = response.data.items;
};

const loadRecords = async () => {
  loading.value = true;
  try {
    const response = await listNewsFetchRecords({
      page: query.page,
      page_size: query.page_size,
      source_id: query.source_id === "" ? undefined : Number(query.source_id),
      status: query.status || undefined,
    });
    records.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const openDetail = async (row: NewsFetchRecordItem) => {
  detailVisible.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    const response = await getNewsFetchRecord(row.id);
    detail.value = response.data;
  } catch {
    ElMessage.error("抓取记录详情加载失败");
  } finally {
    detailLoading.value = false;
  }
};

onMounted(async () => {
  await loadSources();
  await loadRecords();
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="抓取记录"
      description="每次新闻源同步都会留下记录，方便查看抓取数量、重复项和异常信息。"
    />

    <el-card shadow="never">
      <el-form
        :inline="true"
        class="toolbar-form"
      >
        <el-form-item label="新闻源">
          <el-select
            v-model="query.source_id"
            clearable
            placeholder="全部"
            style="width: 220px"
          >
            <el-option
              v-for="item in sources"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="query.status"
            clearable
            placeholder="全部"
            style="width: 140px"
          >
            <el-option
              v-for="item in taskStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadRecords">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="records"
      >
        <el-table-column
          prop="source_name"
          label="新闻源"
          min-width="180"
        />
        <el-table-column
          prop="fetch_mode"
          label="模式"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.fetch_mode" />
          </template>
        </el-table-column>
        <el-table-column
          label="状态"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column
          prop="total_count"
          label="总数"
          width="90"
        />
        <el-table-column
          prop="new_count"
          label="入库"
          width="90"
        />
        <el-table-column
          prop="duplicate_count"
          label="重复"
          width="90"
        />
        <el-table-column
          prop="filtered_count"
          label="通过"
          width="90"
        />
        <el-table-column
          prop="error_count"
          label="错误"
          width="90"
        />
        <el-table-column
          prop="request_id"
          label="请求 ID"
          min-width="180"
        />
        <el-table-column
          prop="error_message"
          label="错误信息"
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
          width="100"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="openDetail(row)"
            >
              详情
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
          @current-change="loadRecords"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      size="48%"
      title="抓取记录详情"
    >
      <el-skeleton
        v-if="detailLoading"
        :rows="8"
        animated
      />
      <div v-else-if="detail">
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="新闻源">
            {{ detail.source_name || detail.source_id }}
          </el-descriptions-item>
          <el-descriptions-item label="抓取模式">
            <StatusTag :status="detail.fetch_mode" />
          </el-descriptions-item>
          <el-descriptions-item label="任务状态">
            <StatusTag :status="detail.status" />
          </el-descriptions-item>
          <el-descriptions-item label="任务编号">
            {{ detail.task_job_id || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="请求 ID">
            {{ detail.request_id || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatDateTime(detail.started_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ formatDateTime(detail.finished_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(detail.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="总数">
            {{ detail.total_count }}
          </el-descriptions-item>
          <el-descriptions-item label="入库">
            {{ detail.new_count }}
          </el-descriptions-item>
          <el-descriptions-item label="重复">
            {{ detail.duplicate_count }}
          </el-descriptions-item>
          <el-descriptions-item label="通过">
            {{ detail.filtered_count }}
          </el-descriptions-item>
          <el-descriptions-item label="错误">
            {{ detail.error_count }}
          </el-descriptions-item>
          <el-descriptions-item
            label="错误信息"
            :span="2"
          >
            {{ detail.error_message || "暂无错误" }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">扩展数据</el-divider>
        <pre class="news-pre">{{ formatJson(detail.extra) }}</pre>
      </div>
    </el-drawer>
  </div>
</template>
