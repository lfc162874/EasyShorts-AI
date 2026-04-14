<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import {
  generateNews,
  getNews,
  listNews,
  listNewsSources,
} from "@/api/modules/news";
import { newsGenerateStyleOptions, newsStatusOptions } from "@/constants/permissions";
import type { NewsDetailItem, NewsItem, NewsSourceItem } from "@/types/news";
import { formatDateTime, formatJson } from "@/utils/format";

const loading = ref(false);
const news = ref<NewsItem[]>([]);
const total = ref(0);
const sources = ref<NewsSourceItem[]>([]);
const detailVisible = ref(false);
const detailLoading = ref(false);
const detail = ref<NewsDetailItem | null>(null);
const generateStyle = ref("professional");

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: "",
  status: "" as "" | NewsItem["status"],
  source_id: "" as "" | number,
  category: "",
});

const sourceMap = computed(() =>
  Object.fromEntries(sources.value.map((item) => [item.id, item.name])),
);

const loadSources = async () => {
  const response = await listNewsSources({ page: 1, page_size: 200 });
  sources.value = response.data.items;
};

const loadNews = async () => {
  loading.value = true;
  try {
    const response = await listNews({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      status: query.status || undefined,
      source_id: query.source_id === "" ? undefined : Number(query.source_id),
      category: query.category || undefined,
    });
    news.value = response.data.items;
    total.value = response.data.total;
  } finally {
    loading.value = false;
  }
};

const openDetail = async (row: NewsItem) => {
  detailVisible.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    const response = await getNews(row.id);
    detail.value = response.data;
  } catch {
    ElMessage.error("新闻详情加载失败");
  } finally {
    detailLoading.value = false;
  }
};

const handleGenerate = async (row: NewsItem) => {
  try {
    const response = await generateNews(row.id, {
      style: generateStyle.value,
      regenerate: true,
    });
    ElMessage.success(`已提交生成任务 #${response.data.id}：${row.title}`);
    await loadNews();
  } catch {
    // 请求层会给出具体错误，这里只负责吞掉未处理的异常。
  }
};

onMounted(async () => {
  await Promise.all([loadSources(), loadNews()]);
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="新闻管理"
      description="在这里查看采集到的新闻、打开详情、触发生成任务并查看结果。"
    >
      <el-select
        v-model="generateStyle"
        style="width: 160px"
      >
        <el-option
          v-for="item in newsGenerateStyleOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </PageSectionHeader>

    <el-card shadow="never">
      <el-form
        :inline="true"
        class="toolbar-form"
      >
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            clearable
            placeholder="标题 / 摘要 / 脚本"
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
              v-for="item in newsStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
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
        <el-form-item label="分类">
          <el-input
            v-model="query.category"
            clearable
            placeholder="模型发布 / 开源生态"
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="loadNews">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="news"
      >
        <el-table-column
          prop="title"
          label="标题"
          min-width="280"
          show-overflow-tooltip
        />
        <el-table-column
          label="新闻源"
          min-width="160"
        >
          <template #default="{ row }">
            {{ sourceMap[row.source_id ?? -1] ?? row.source }}
          </template>
        </el-table-column>
        <el-table-column
          prop="category"
          label="分类"
          min-width="120"
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
          prop="hot_score"
          label="热度"
          width="100"
        />
        <el-table-column
          prop="publish_time"
          label="发布时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.publish_time) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="summary"
          label="摘要"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column
          prop="translated_title"
          label="中文标题"
          min-width="220"
          show-overflow-tooltip
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
              @click="openDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-permission="'news:generate'"
              link
              type="primary"
              :disabled="row.status === 'REJECTED'"
              @click="handleGenerate(row)"
            >
              生成
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
          @current-change="loadNews"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      size="52%"
      title="新闻详情与生成结果"
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
          <el-descriptions-item label="标题">
            {{ detail.title }}
          </el-descriptions-item>
          <el-descriptions-item label="新闻源">
            {{ detail.source_detail?.name ?? detail.source }}
          </el-descriptions-item>
          <el-descriptions-item label="来源类型">
            <StatusTag
              v-if="detail.source_detail?.source_type"
              :status="detail.source_detail.source_type"
            />
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="来源地址">
            {{ detail.source_detail?.url || detail.source_url || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ detail.category || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag :status="detail.status" />
          </el-descriptions-item>
          <el-descriptions-item label="热度">
            {{ detail.hot_score }}
          </el-descriptions-item>
          <el-descriptions-item label="语言">
            {{ detail.language }}
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">
            {{ formatDateTime(detail.publish_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(detail.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(detail.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="去重哈希" :span="2">
            {{ detail.dedup_hash || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="原文地址" :span="2">
            <a
              :href="detail.url"
              target="_blank"
              rel="noreferrer"
            >
              {{ detail.url }}
            </a>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">摘要</el-divider>
        <div class="news-block">{{ detail.summary || "暂无摘要" }}</div>

        <el-divider content-position="left">中文标题</el-divider>
        <div class="news-block">{{ detail.translated_title || "暂无中文标题" }}</div>

        <el-divider content-position="left">中文正文</el-divider>
        <div class="news-block">{{ detail.translated_content || "暂无中文正文" }}</div>

        <el-divider content-position="left">脚本</el-divider>
        <pre class="news-pre">{{ detail.script || "暂无脚本" }}</pre>

        <el-divider content-position="left">标签</el-divider>
        <div class="tag-row">
          <el-tag
            v-for="tag in detail.tags || []"
            :key="tag"
            effect="plain"
          >
            {{ tag }}
          </el-tag>
          <span v-if="!(detail.tags?.length)">暂无标签</span>
        </div>

        <el-divider content-position="left">抓取记录</el-divider>
        <el-table :data="detail.fetch_records">
          <el-table-column prop="source_name" label="新闻源" min-width="140" />
          <el-table-column prop="fetch_mode" label="模式" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.fetch_mode" />
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="total_count" label="总数" width="80" />
          <el-table-column prop="new_count" label="入库" width="80" />
          <el-table-column prop="duplicate_count" label="重复" width="80" />
          <el-table-column prop="filtered_count" label="通过" width="80" />
        </el-table>

        <el-divider content-position="left">原始数据</el-divider>
        <pre class="news-pre">{{ formatJson(detail.raw_metadata) }}</pre>
      </div>
    </el-drawer>
  </div>
</template>
