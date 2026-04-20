<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  status: string;
}>();

const labelMap: Record<string, string> = {
  ACTIVE: "启用",
  DISABLED: "停用",
  DIRECTORY: "目录",
  MENU: "菜单",
  BUTTON: "按钮",
  UNAUTHORIZED: "未授权",
  AUTHORIZED: "已授权",
  EXPIRED: "已过期",
  RSS: "RSS",
  ATOM: "ATOM",
  WEB: "网页",
  MANUAL: "手动",
  SCHEDULED: "定时",
  PENDING: "待执行",
  RUNNING: "执行中",
  SUCCESS: "成功",
  FAILED: "失败",
  RETRYING: "重试中",
  CANCELLED: "已取消",
  NEW: "待处理",
  DEDUPED: "已去重",
  FILTERED: "已筛选",
  REJECTED: "已拒绝",
  SCRIPT_READY: "脚本就绪",
  ARCHIVED: "已归档",
  IGNORED: "忽略",
  WAITING: "待执行",
  SKIPPED: "已跳过",
  single_article: "单条内容",
  digest: "简报",
  push_plan: "推送计划",
  news: "内容",
  hot_topic: "热点",
  IMMEDIATE: "即时推送",
  EXECUTED: "已执行",
  HIGH: "高",
  MEDIUM: "中",
  LOW: "低",
  RISING: "上升",
  WATCH: "持续",
  STABLE: "稳定",
  BOOLEAN: "布尔",
  INTEGER: "整数",
  FLOAT: "浮点",
  JSON: "JSON",
  SECRET: "密钥",
  STRING: "字符串",
  IMAGE: "图片",
  AUDIO: "音频",
  VIDEO: "视频",
  DOCUMENT: "文档",
  OTHER: "其他",
};

const typeMap: Record<string, "success" | "warning" | "danger" | "info"> = {
  ACTIVE: "success",
  DISABLED: "info",
  DIRECTORY: "info",
  MENU: "success",
  BUTTON: "warning",
  UNAUTHORIZED: "info",
  AUTHORIZED: "success",
  EXPIRED: "warning",
  RSS: "info",
  ATOM: "info",
  WEB: "info",
  MANUAL: "info",
  SCHEDULED: "info",
  PENDING: "info",
  RUNNING: "warning",
  SUCCESS: "success",
  FAILED: "danger",
  RETRYING: "warning",
  CANCELLED: "info",
  NEW: "info",
  DEDUPED: "success",
  FILTERED: "success",
  REJECTED: "danger",
  SCRIPT_READY: "success",
  ARCHIVED: "info",
  IGNORED: "info",
  WAITING: "info",
  SKIPPED: "info",
  single_article: "info",
  digest: "info",
  push_plan: "info",
  news: "info",
  hot_topic: "info",
  IMMEDIATE: "success",
  EXECUTED: "success",
  HIGH: "danger",
  MEDIUM: "warning",
  LOW: "info",
  RISING: "success",
  WATCH: "warning",
  STABLE: "info",
  BOOLEAN: "info",
  INTEGER: "info",
  FLOAT: "info",
  JSON: "info",
  SECRET: "warning",
  IMAGE: "success",
  AUDIO: "success",
  VIDEO: "success",
  DOCUMENT: "info",
  OTHER: "info",
};

const type = computed(() => typeMap[props.status] ?? "info");
const label = computed(() => labelMap[props.status] ?? props.status);
</script>

<template>
  <el-tag
    :type="type"
    effect="light"
    round
  >
    {{ label }}
  </el-tag>
</template>
