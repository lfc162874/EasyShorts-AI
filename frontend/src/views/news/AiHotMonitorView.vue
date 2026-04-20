<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { listNews } from "@/api/modules/news";
import type { NewsItem } from "@/types/news";
import { formatDateTime } from "@/utils/format";

const loading = ref(false);
const keyword = ref("");
const onlyZh = ref(false);
const autoRefresh = ref(true);
const items = ref<NewsItem[]>([]);
let timer: number | null = null;

const sortedByHot = computed(() =>
  [...items.value].sort((a, b) => b.hot_score - a.hot_score),
);

const filteredItems = computed(() => {
  const term = keyword.value.trim().toLowerCase();
  return sortedByHot.value.filter((item) => {
    if (onlyZh.value && item.language !== "zh-CN" && item.language !== "zh") {
      return false;
    }
    if (!term) {
      return true;
    }
    const source = item.source?.toLowerCase() ?? "";
    const title = item.title?.toLowerCase() ?? "";
    const tags = item.tags?.join(",").toLowerCase() ?? "";
    return title.includes(term) || source.includes(term) || tags.includes(term);
  });
});

const top3 = computed(() => filteredItems.value.slice(0, 3));
const top20 = computed(() => filteredItems.value.slice(0, 20));
const totalCount = computed(() => filteredItems.value.length);
const maxHot = computed(() => top20.value[0]?.hot_score ?? 0);
const avgHot = computed(() => {
  if (!top20.value.length) {
    return 0;
  }
  const total = top20.value.reduce((sum, item) => sum + item.hot_score, 0);
  return Math.round((total / top20.value.length) * 10) / 10;
});
const latestTime = computed(() => {
  if (!filteredItems.value.length) {
    return "-";
  }
  const latest = [...filteredItems.value]
    .map((item) => item.publish_time ?? item.created_at)
    .filter(Boolean)
    .sort()
    .at(-1);
  return formatDateTime(latest);
});

const scoreLevel = (score: number) => {
  if (score >= 85) {
    return "high";
  }
  if (score >= 65) {
    return "mid";
  }
  return "low";
};

const loadHotNews = async () => {
  loading.value = true;
  try {
    const response = await listNews({ page: 1, page_size: 120 });
    items.value = response.data.items;
  } finally {
    loading.value = false;
  }
};

const openArticle = (url?: string | null) => {
  if (!url) {
    return;
  }
  window.open(url, "_blank");
};

const startTimer = () => {
  if (timer) {
    window.clearInterval(timer);
  }
  if (!autoRefresh.value) {
    return;
  }
  timer = window.setInterval(() => {
    void loadHotNews();
  }, 30000);
};

onMounted(async () => {
  await loadHotNews();
  startTimer();
});

onBeforeUnmount(() => {
  if (timer) {
    window.clearInterval(timer);
  }
});
</script>

<template>
  <div class="hot-monitor">
    <div class="monitor-hero">
      <div class="monitor-hero__left">
        <div class="monitor-badge">AI 热点监控</div>
        <h1 class="monitor-title">最热新闻实时雷达</h1>
        <p class="monitor-subtitle">
          追踪全量内容热度，按 Hot Score 自动排序，帮助你快速定位“现在最值得处理”的新闻。
        </p>
      </div>

      <div class="monitor-hero__right">
        <div class="metric-card">
          <div class="metric-card__label">样本总量</div>
          <div class="metric-card__value">{{ totalCount }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__label">最高热度</div>
          <div class="metric-card__value">{{ maxHot }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__label">平均热度</div>
          <div class="metric-card__value">{{ avgHot }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__label">最近更新</div>
          <div class="metric-card__value metric-card__value--small">{{ latestTime }}</div>
        </div>
      </div>
    </div>

    <el-card
      shadow="never"
      class="monitor-toolbar"
    >
      <div class="monitor-toolbar__row">
        <el-input
          v-model="keyword"
          clearable
          placeholder="搜索标题 / 来源 / 标签"
          style="width: 280px"
        />
        <el-switch
          v-model="onlyZh"
          inline-prompt
          active-text="仅中文"
          inactive-text="全部语言"
        />
        <el-switch
          v-model="autoRefresh"
          inline-prompt
          active-text="自动刷新"
          inactive-text="手动刷新"
          @change="startTimer"
        />
        <el-button
          :loading="loading"
          @click="loadHotNews"
        >
          立即刷新
        </el-button>
      </div>
    </el-card>

    <div class="top3-grid">
      <el-card
        v-for="(item, idx) in top3"
        :key="item.id"
        shadow="never"
        class="top3-card"
      >
        <div class="top3-card__rank">TOP {{ idx + 1 }}</div>
        <div class="top3-card__title">{{ item.title }}</div>
        <div class="top3-card__meta">
          <span>{{ item.source }}</span>
          <span>{{ formatDateTime(item.publish_time ?? item.created_at) }}</span>
        </div>
        <div class="top3-card__footer">
          <el-tag
            effect="light"
            :type="scoreLevel(item.hot_score) === 'high' ? 'danger' : scoreLevel(item.hot_score) === 'mid' ? 'warning' : 'info'"
          >
            热度 {{ item.hot_score }}
          </el-tag>
          <el-button
            v-if="item.url"
            text
            @click="openArticle(item.url)"
          >
            查看原文
          </el-button>
        </div>
      </el-card>
    </div>

    <el-card
      shadow="never"
      class="monitor-table"
    >
      <el-table
        :data="top20"
        :loading="loading"
        size="large"
      >
        <el-table-column
          label="#"
          width="70"
        >
          <template #default="{ $index }">
            <span class="rank-index">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="title"
          label="新闻标题"
          min-width="360"
          show-overflow-tooltip
        />
        <el-table-column
          prop="source"
          label="来源"
          min-width="160"
          show-overflow-tooltip
        />
        <el-table-column
          label="标签"
          min-width="180"
        >
          <template #default="{ row }">
            <div class="tag-list">
              <el-tag
                v-for="tag in (row.tags || []).slice(0, 3)"
                :key="tag"
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          label="Hot Score"
          width="140"
        >
          <template #default="{ row }">
            <span
              class="hot-score"
              :class="`hot-score--${scoreLevel(row.hot_score)}`"
            >
              {{ row.hot_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          label="发布时间"
          width="200"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.publish_time ?? row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.hot-monitor {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.monitor-hero {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(129, 140, 248, 0.24);
  background:
    radial-gradient(circle at 0% 0%, rgba(79, 70, 229, 0.28) 0%, transparent 40%),
    radial-gradient(circle at 92% 12%, rgba(6, 182, 212, 0.16) 0%, transparent 36%),
    linear-gradient(135deg, #0b1020 0%, #121a35 52%, #0b1020 100%);
}

.monitor-badge {
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(129, 140, 248, 0.32);
  background: rgba(99, 102, 241, 0.14);
  color: rgba(224, 231, 255, 0.95);
  font-size: 12px;
  font-weight: 700;
}

.monitor-title {
  margin: 12px 0 0;
  color: #f8fafc;
  font-size: 32px;
  line-height: 1.1;
}

.monitor-subtitle {
  margin: 10px 0 0;
  max-width: 760px;
  color: rgba(226, 232, 240, 0.82);
  font-size: 14px;
  line-height: 1.7;
}

.monitor-hero__right {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.metric-card {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.45);
}

.metric-card__label {
  color: rgba(203, 213, 225, 0.75);
  font-size: 12px;
}

.metric-card__value {
  margin-top: 8px;
  color: #f8fafc;
  font-size: 24px;
  font-weight: 800;
}

.metric-card__value--small {
  font-size: 14px;
  font-weight: 700;
}

.monitor-toolbar__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.top3-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.top3-card {
  border-radius: 16px;
}

.top3-card__rank {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(124, 58, 237, 0.12);
  color: rgba(109, 40, 217, 0.9);
  font-size: 12px;
  font-weight: 700;
}

.top3-card__title {
  margin-top: 10px;
  color: #0f172a;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.45;
}

.top3-card__meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
  color: #64748b;
  font-size: 12px;
}

.top3-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.rank-index {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(124, 58, 237, 0.1);
  color: rgba(109, 40, 217, 0.92);
  font-weight: 700;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hot-score {
  font-weight: 800;
}

.hot-score--high {
  color: #dc2626;
}

.hot-score--mid {
  color: #d97706;
}

.hot-score--low {
  color: #0369a1;
}

@media (max-width: 1100px) {
  .monitor-hero {
    grid-template-columns: 1fr;
  }

  .top3-grid {
    grid-template-columns: 1fr;
  }
}
</style>
