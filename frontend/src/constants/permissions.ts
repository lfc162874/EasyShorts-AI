import type { OptionItem } from "@/types/common";

export const userStatusOptions: OptionItem[] = [
  { label: "启用", value: "ACTIVE" },
  { label: "停用", value: "DISABLED" },
];

export const roleTypeOptions: OptionItem[] = [
  { label: "系统角色", value: "true" },
  { label: "普通角色", value: "false" },
];

export const menuTypeOptions: OptionItem[] = [
  { label: "目录", value: "DIRECTORY" },
  { label: "菜单", value: "MENU" },
  { label: "按钮", value: "BUTTON" },
];

export const configValueTypeOptions: OptionItem[] = [
  { label: "字符串", value: "STRING" },
  { label: "整数", value: "INTEGER" },
  { label: "浮点", value: "FLOAT" },
  { label: "布尔", value: "BOOLEAN" },
  { label: "JSON", value: "JSON" },
  { label: "密钥", value: "SECRET" },
];

export const platformAuthStatusOptions: OptionItem[] = [
  { label: "未授权", value: "UNAUTHORIZED" },
  { label: "已授权", value: "AUTHORIZED" },
  { label: "已过期", value: "EXPIRED" },
  { label: "已停用", value: "DISABLED" },
];

export const taskStatusOptions: OptionItem[] = [
  { label: "待执行", value: "PENDING" },
  { label: "执行中", value: "RUNNING" },
  { label: "成功", value: "SUCCESS" },
  { label: "失败", value: "FAILED" },
  { label: "重试中", value: "RETRYING" },
  { label: "已取消", value: "CANCELLED" },
];

export const fileCategoryOptions: OptionItem[] = [
  { label: "图片", value: "IMAGE" },
  { label: "音频", value: "AUDIO" },
  { label: "视频", value: "VIDEO" },
  { label: "文档", value: "DOCUMENT" },
  { label: "其他", value: "OTHER" },
];

export const operationStatusOptions: OptionItem[] = [
  { label: "成功", value: "SUCCESS" },
  { label: "失败", value: "FAILED" },
];

export const newsSourceTypeOptions: OptionItem[] = [
  { label: "RSS", value: "RSS" },
  { label: "ATOM", value: "ATOM" },
  { label: "网页", value: "WEB" },
  { label: "手动", value: "MANUAL" },
];

export const newsStatusOptions: OptionItem[] = [
  { label: "待处理", value: "NEW" },
  { label: "已去重", value: "DEDUPED" },
  { label: "已筛选", value: "FILTERED" },
  { label: "已拒绝", value: "REJECTED" },
  { label: "处理就绪", value: "SCRIPT_READY" },
  { label: "已归档", value: "ARCHIVED" },
];

export const newsGenerateStyleOptions: OptionItem[] = [
  { label: "热点简报", value: "professional" },
  { label: "播报摘要", value: "broadcast" },
  { label: "深度整理", value: "story" },
  { label: "简洁速览", value: "concise" },
];

export const newsFetchModeOptions: OptionItem[] = [
  { label: "手动触发", value: "MANUAL" },
  { label: "定时调度", value: "SCHEDULED" },
];

export const agentRunStatusOptions: OptionItem[] = [
  { label: "待执行", value: "PENDING" },
  { label: "运行中", value: "RUNNING" },
  { label: "成功", value: "SUCCESS" },
  { label: "失败", value: "FAILED" },
  { label: "重试中", value: "RETRYING" },
  { label: "已取消", value: "CANCELLED" },
];

export const agentRunTypeOptions: OptionItem[] = [
  { label: "单条内容", value: "single_article" },
  { label: "简报", value: "digest" },
  { label: "推送计划", value: "push_plan" },
];

export const agentBizTypeOptions: OptionItem[] = [
  { label: "内容", value: "news" },
  { label: "热点", value: "hot_topic" },
  { label: "简报", value: "digest" },
];

export const hotTopicStatusOptions: OptionItem[] = [
  { label: "启用", value: "ACTIVE" },
  { label: "忽略", value: "IGNORED" },
  { label: "已归档", value: "ARCHIVED" },
];

export const hotTopicPriorityOptions: OptionItem[] = [
  { label: "高", value: "HIGH" },
  { label: "中", value: "MEDIUM" },
  { label: "低", value: "LOW" },
];

export const hotTopicTrendOptions: OptionItem[] = [
  { label: "上升", value: "RISING" },
  { label: "持续", value: "WATCH" },
  { label: "稳定", value: "STABLE" },
];

export const pushPlanStatusOptions: OptionItem[] = [
  { label: "待执行", value: "PENDING" },
  { label: "已计划", value: "SCHEDULED" },
  { label: "已执行", value: "EXECUTED" },
  { label: "失败", value: "FAILED" },
  { label: "已取消", value: "CANCELLED" },
];

export const pushPlanTypeOptions: OptionItem[] = [
  { label: "即时推送", value: "IMMEDIATE" },
  { label: "简报推送", value: "DIGEST" },
  { label: "定时推送", value: "SCHEDULED" },
];

export const agentPushChannelOptions: OptionItem[] = [
  { label: "邮件", value: "email" },
  { label: "飞书", value: "feishu" },
  { label: "企业微信", value: "wechat_work" },
];
