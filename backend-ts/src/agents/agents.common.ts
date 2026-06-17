/**
 * Agent 通用工具函数
 * 对应 Python 端 common.py — 提供所有 Agent 的规则降级（fallback）逻辑
 */

// ===== 常量 =====

export const HOT_KEYWORDS = [
  'openai', 'anthropic', 'deepseek', 'qwen', 'modelscope', 'huggingface',
  'agent', 'llm', 'gpt', 'model', 'paper', 'research', 'open source',
  'opensource', '开源', '融资', '发布', '更新', '推理', '政策', '监管',
] as const;

export const CATEGORY_RULES: readonly [string, readonly string[]][] = [
  ['AI Agent', ['agent', 'tool use', 'tool calling', '智能体', 'workflow', 'automation']],
  ['大模型', ['llm', 'model', 'reasoning', 'benchmark', '大模型', '模型', '参数', '推理']],
  ['开源生态', ['open source', 'opensource', '开源', 'github', 'huggingface', 'modelscope']],
  ['AI产品发布', ['launch', 'release', 'update', 'ship', '发布', '更新', '上线', '功能']],
  ['学术研究', ['paper', 'arxiv', 'research', '论文', '研究', '实验']],
  ['融资动态', ['funding', 'investment', 'round', '融资', '投资', '天使轮', 'A轮', 'B轮']],
  ['政策监管', ['policy', 'regulation', 'law', '政策', '监管', '法案', '合规']],
] as const;

export const BLACKLIST_WORDS = new Set([
  'the', 'and', 'for', 'with', 'that', 'this', 'from', 'news', 'today',
  'latest', 'about', 'content', '内容', '新闻', '今天', '最新', '一个',
  '我们', '他们',
]);

// ===== 文本处理 =====

export function normalizeWhitespace(value: string | null | undefined): string {
  if (!value) return '';
  return value
    .replace(/&[^;]+;/g, ' ') // 简单 HTML entity 解码
    .replace(/\s+/g, ' ')
    .trim();
}

export function containsChinese(value: string): boolean {
  return /[\u4e00-\u9fff]/.test(value);
}

export function normalizeSignature(value: string | null | undefined): string {
  if (!value) return '';
  const text = normalizeWhitespace(value).toLowerCase();
  return text.replace(/[^\w\u4e00-\u9fff]+/g, '');
}

/** 从文本中提取关键词 */
export function extractKeywords(text: string, maxCount = 8): string[] {
  const rawTerms = text.match(/[A-Za-z][A-Za-z0-9+._-]{2,}|[\u4e00-\u9fff]{2,6}/g) || [];
  const keywords: string[] = [];
  for (const term of rawTerms) {
    const normalized = term.trim().replace(/[,.:;!?()\[\]{}<>"'`]/g, '');
    if (!normalized) continue;
    const lower = normalized.toLowerCase();
    if (BLACKLIST_WORDS.has(lower) || keywords.includes(normalized)) continue;
    keywords.push(normalized);
    if (keywords.length >= maxCount) break;
  }
  return keywords;
}

/** 按句子分割文本 */
export function splitSentences(text: string): string[] {
  return text
    .split(/[。！？!?\.]\s*/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/** 生成简短摘要 */
export function summarizeText(text: string, limit = 220): string {
  if (!text) return '';
  const sentences = splitSentences(text);
  const selected = sentences.length > 0 ? sentences.slice(0, 2) : [text.slice(0, 180)];
  let summary = selected.join('；');
  if (!containsChinese(summary)) summary = summary.trim();
  return normalizeWhitespace(summary).slice(0, limit);
}

// ===== 推理函数 =====

/** 根据标题和内容推断分类 */
export function inferCategory(
  title: string,
  content: string,
  fallback?: string,
): string {
  const text = `${title} ${content}`.toLowerCase();
  for (const [category, keywords] of CATEGORY_RULES) {
    if (keywords.some((kw) => text.includes(kw))) {
      return category;
    }
  }
  return fallback || '行业动态';
}

/** 根据热度分推断优先级 */
export function inferPriority(score: number): 'HIGH' | 'MEDIUM' | 'LOW' {
  if (score >= 80) return 'HIGH';
  if (score >= 60) return 'MEDIUM';
  return 'LOW';
}

/** 根据热度分和内容推断趋势 */
export function inferTrend(score: number, title: string, content: string): 'RISING' | 'WATCH' | 'STABLE' {
  const text = `${title} ${content}`.toLowerCase();
  if (
    score >= 80 ||
    ['breaking', '紧急', '首发', '发布'].some((kw) => text.includes(kw))
  ) {
    return 'RISING';
  }
  if (score >= 60) return 'WATCH';
  return 'STABLE';
}

/** 合并去重渠道列表 */
export function mergeChannels(...groups: Array<string[] | null | undefined>): string[] {
  const merged: string[] = [];
  const seen = new Set<string>();
  for (const group of groups) {
    for (const channel of group || []) {
      const normalized = normalizeWhitespace(channel).toLowerCase();
      if (!normalized || seen.has(normalized)) continue;
      seen.add(normalized);
      merged.push(normalized);
    }
  }
  return merged;
}

/** 根据优先级推荐推送渠道 */
export function recommendChannels(priority: string): string[] {
  switch (priority) {
    case 'HIGH':
      return ['webhook', 'email', 'feishu', 'wechat_work'];
    case 'MEDIUM':
      return ['webhook', 'email', 'feishu'];
    default:
      return ['webhook', 'email'];
  }
}

/** 计算主题唯一标识 */
export function computeTopicKey(title: string, category: string | null): string {
  const payload = [normalizeSignature(title), normalizeSignature(category || '')].join('|');
  // 简单 hash 实现
  let hash = 0;
  for (let i = 0; i < payload.length; i++) {
    const char = payload.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(16).padStart(8, '0') + Math.abs(hash ^ 0xdeadbeef).toString(16).padStart(8, '0');
}

/** 构建要点列表 */
export function buildHighlights(text: string, keywords: string[]): string[] {
  const sentences = splitSentences(text);
  const highlights: string[] = [];
  for (const sentence of sentences.slice(0, 3)) {
    if (!highlights.includes(sentence)) {
      highlights.push(sentence.slice(0, 160));
    }
  }
  if (keywords.length > 0) {
    highlights.push(`核心关键词：${keywords.slice(0, 3).join('、')}`);
  }
  return highlights.slice(0, 4);
}

/** 构建背景说明 */
export function buildBackground(category: string, title: string, keywords: string[]): string {
  switch (category) {
    case 'AI Agent':
      return `这条 ${category} 动态围绕 ${title} 展开，和智能体编排、工具调用以及自动化流程相关。`;
    case '大模型':
      return `这条 ${category} 动态涉及 ${title}，通常会影响模型能力、推理成本和产品迭代节奏。`;
    case '开源生态':
      return `这条 ${category} 动态涉及 ${title}，对社区传播、生态协作和二次开发都比较敏感。`;
    default:
      if (keywords.length > 0) {
        return `这条 ${category} 动态围绕 ${title} 展开，关键词包括 ${keywords.slice(0, 3).join('、')}。`;
      }
      return `这条 ${category} 动态围绕 ${title} 展开。`;
  }
}

/** 构建影响分析 */
export function buildImpact(category: string, score: number, keywords: string[]): string {
  const focus = keywords.length > 0 ? keywords.slice(0, 3).join('、') : 'AI 生态';
  if (score >= 80) {
    return `这类高热度内容会直接影响 ${focus} 方向的关注度和后续传播节奏。`;
  }
  if (category === 'AI Agent' || category === '大模型') {
    return `该内容可能影响 ${focus} 的产品落地、方法迭代与讨论热度。`;
  }
  return `该内容会为 ${focus} 提供补充信息，适合纳入持续观察。`;
}

/** 构建技术分析 */
export function buildTechnicalAnalysis(category: string, keywords: string[]): string {
  switch (category) {
    case 'AI Agent':
      return '重点关注编排方式、工具调用、上下文管理和任务拆分是否有变化。';
    case '大模型':
      return '重点关注模型规模、推理能力、上下文长度和成本变化。';
    case '开源生态':
      return '重点关注开源协议、仓库活跃度、复现门槛和社区参与度。';
    default:
      if (keywords.length > 0) {
        return `从技术角度看，需关注 ${keywords.slice(0, 3).join('、')} 的变化。`;
      }
      return '从技术角度看，可继续追踪相关实现细节和落地方式。';
  }
}

/** 构建应用场景 */
export function buildApplicationScenarios(category: string, keywords: string[]): string[] {
  const scenarios = [
    `用于跟进 ${category} 的最新行业动态。`,
    '用于生成简报、日报或周报摘要。',
  ];
  if (keywords.length > 0) {
    scenarios.push(`用于围绕 ${keywords.slice(0, 2).join('、')} 建立持续监控。`);
  }
  return scenarios.slice(0, 3);
}

/** 获取模型显示名称 */
export function buildModelLabel(modelName: string): string {
  const labels: Record<string, string> = {
    'qwen3.5-plus': '通义千问 3.5 Plus',
    'qwen-max': '通义千问 Max',
    'deepseek-v3': 'DeepSeek V3',
    'deepseek-r1': 'DeepSeek R1',
  };
  return labels[modelName] || modelName;
}
