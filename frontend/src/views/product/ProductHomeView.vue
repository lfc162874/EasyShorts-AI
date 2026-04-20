<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Cpu, DataLine, Setting, Document, VideoCamera } from "@element-plus/icons-vue";

import { useAuthStore } from "@/stores/auth";

type FeatureItem = {
  title: string;
  description: string;
  to: string;
  permission?: string | string[];
  icon: unknown;
  accent: string;
};

const router = useRouter();
const authStore = useAuthStore();

const features = computed<FeatureItem[]>(() => [
  {
    title: "智能处理中心",
    description: "从内容采集到 Agent 运行、热点聚合与推送计划，一站式完成。",
    to: "/news/list",
    permission: ["news:list", "agent:run:list", "agent:hot-topic:list", "agent:push-plan:list"],
    icon: Cpu,
    accent: "rgba(91, 95, 240, 0.22)",
  },
  {
    title: "内容中心",
    description: "内容列表、详情、手动触发智能处理与链路跟踪。",
    to: "/news/list",
    permission: "news:list",
    icon: Document,
    accent: "rgba(56, 189, 248, 0.18)",
  },
  {
    title: "运行中心",
    description: "查看每次 Agent 运行状态、日志与产出结果。",
    to: "/agent/runs",
    permission: "agent:run:list",
    icon: DataLine,
    accent: "rgba(16, 185, 129, 0.18)",
  },
  {
    title: "热点池",
    description: "聚合热点、筛选与进一步处理，沉淀可推送选题。",
    to: "/agent/hot-topics",
    permission: "agent:hot-topic:list",
    icon: VideoCamera,
    accent: "rgba(236, 72, 153, 0.16)",
  },
  {
    title: "后台管理",
    description: "用户、角色、菜单、系统配置与任务/日志等管理能力。",
    to: "/admin/dashboard",
    permission: ["dashboard:view", "system:user:list", "system:role:list", "system:menu:list"],
    icon: Setting,
    accent: "rgba(148, 163, 184, 0.18)",
  },
]);

const isAllowed = (permission?: string | string[]) => {
  if (!permission) {
    return true;
  }
  if (authStore.isSuperAdmin) {
    return true;
  }
  const required = Array.isArray(permission) ? permission : [permission];
  return required.some((item) => authStore.permissions.includes(item));
};
</script>

<template>
  <div class="home-shell">
    <div class="hero">
      <div class="hero__main">
        <div class="hero__badge">智能处理平台</div>
        <h1 class="hero__title">
          <span class="hero__title-gradient">EasyShorts AI</span>
        </h1>
        <p class="hero__subtitle">
          将内容采集、Agent 智能处理、热点聚合与推送计划串成一条可观测的生产线。
        </p>
        <div class="hero__chips">
          <div class="hero-chip">内容中心</div>
          <div class="hero-chip">运行中心</div>
          <div class="hero-chip">热点池</div>
          <div class="hero-chip">推送计划</div>
        </div>
        <div class="hero__actions">
          <el-button
            type="primary"
            size="large"
            :disabled="!isAllowed(['news:list','agent:run:list','agent:hot-topic:list','agent:push-plan:list'])"
            @click="router.push('/news/list')"
          >
            进入智能处理
          </el-button>
          <el-button
            size="large"
            :disabled="!isAllowed(['dashboard:view','system:user:list','system:role:list','system:menu:list'])"
            @click="router.push('/admin/dashboard')"
          >
            进入后台管理
          </el-button>
        </div>

        <div class="hero__trust">
          <div class="trust-item">
            <div class="trust-item__label">当前账号</div>
            <div class="trust-item__value">
              {{ authStore.user?.nickname ?? authStore.user?.username ?? "-" }}
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-item__label">权限模式</div>
            <div class="trust-item__value">
              {{ authStore.isSuperAdmin ? "超级管理员" : "按角色权限控制" }}
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-item__label">进入方式</div>
            <div class="trust-item__value">无需学习成本</div>
          </div>
        </div>
      </div>

      <div class="hero__visual">
        <div class="visual-card">
          <div class="visual-card__glow" />

          <div class="visual-card__top">
            <div class="visual-pill">实时可观测</div>
            <div class="visual-metric">
              <div class="visual-metric__label">最新运行</div>
              <div class="visual-metric__value">Agent Run</div>
            </div>
          </div>

          <div class="visual-flow">
            <div class="flow-node">
              <div class="flow-node__dot flow-node__dot--content" />
              <div class="flow-node__text">
                <div class="flow-node__title">内容</div>
                <div class="flow-node__desc">采集 / 过滤</div>
              </div>
            </div>
            <div class="flow-line" />
            <div class="flow-node">
              <div class="flow-node__dot flow-node__dot--agent" />
              <div class="flow-node__text">
                <div class="flow-node__title">Agent</div>
                <div class="flow-node__desc">抽取 / 生成</div>
              </div>
            </div>
            <div class="flow-line" />
            <div class="flow-node">
              <div class="flow-node__dot flow-node__dot--hot" />
              <div class="flow-node__text">
                <div class="flow-node__title">热点</div>
                <div class="flow-node__desc">聚合 / 排序</div>
              </div>
            </div>
            <div class="flow-line" />
            <div class="flow-node">
              <div class="flow-node__dot flow-node__dot--push" />
              <div class="flow-node__text">
                <div class="flow-node__title">推送</div>
                <div class="flow-node__desc">计划 / 分发</div>
              </div>
            </div>
          </div>

          <div class="visual-stats">
            <div class="stat-chip">
              <div class="stat-chip__label">可追踪</div>
              <div class="stat-chip__value">运行链路</div>
            </div>
            <div class="stat-chip">
              <div class="stat-chip__label">可复用</div>
              <div class="stat-chip__value">模型配置</div>
            </div>
            <div class="stat-chip">
              <div class="stat-chip__label">可协作</div>
              <div class="stat-chip__value">权限与菜单</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="section-head">
      <div>
        <div class="section-title">核心能力</div>
        <div class="section-subtitle">以产品化方式封装智能处理链路，入口清晰，过程可观测。</div>
      </div>
    </div>

    <div class="feature-grid">
      <el-card
        v-for="item in features"
        :key="item.title"
        shadow="never"
        class="feature-card"
        :class="{ 'is-disabled': !isAllowed(item.permission) }"
        @click="isAllowed(item.permission) && router.push(item.to)"
      >
        <div class="feature-card__inner">
          <div class="feature-card__head">
            <div
              class="feature-card__icon"
              :style="{ background: item.accent }"
            >
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="feature-card__title">{{ item.title }}</div>
          </div>
          <div class="feature-card__desc">{{ item.description }}</div>
          <div class="feature-card__cta">
            <span>打开</span>
            <span class="feature-card__arrow">→</span>
          </div>
        </div>
      </el-card>
    </div>

    <div class="section-head section-head--spaced">
      <div>
        <div class="section-title">工作流</div>
        <div class="section-subtitle">从内容到推送，按步骤沉淀资产，随时回溯每一次运行。</div>
      </div>
    </div>

    <div class="workflow-grid">
      <div class="workflow-card">
        <div class="workflow-card__step">01</div>
        <div class="workflow-card__title">收集内容</div>
        <div class="workflow-card__desc">维护来源，查看采集记录，形成可复用的内容入口。</div>
      </div>
      <div class="workflow-card">
        <div class="workflow-card__step">02</div>
        <div class="workflow-card__title">触发智能处理</div>
        <div class="workflow-card__desc">在内容中心一键触发 Agent 处理，参数与结果都有迹可循。</div>
      </div>
      <div class="workflow-card">
        <div class="workflow-card__step">03</div>
        <div class="workflow-card__title">沉淀热点</div>
        <div class="workflow-card__desc">聚合热点池，筛选可推送选题，持续迭代策略。</div>
      </div>
      <div class="workflow-card">
        <div class="workflow-card__step">04</div>
        <div class="workflow-card__title">编排推送</div>
        <div class="workflow-card__desc">制定推送计划，自动化分发，让内容产出更稳定。</div>
      </div>
    </div>

    <div class="cta-band">
      <div class="cta-band__copy">
        <div class="cta-band__title">准备好开始了吗？</div>
        <div class="cta-band__subtitle">进入智能处理中心，从第一条内容开始跑通链路。</div>
      </div>
      <div class="cta-band__actions">
        <el-button
          type="primary"
          size="large"
          :disabled="!isAllowed(['news:list','agent:run:list','agent:hot-topic:list','agent:push-plan:list'])"
          @click="router.push('/news/list')"
        >
          立即开始
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.home-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 18px;
  padding: 26px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 26px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.62) 0%, rgba(2, 6, 23, 0.52) 55%, rgba(15, 23, 42, 0.52) 100%);
  box-shadow:
    0 26px 80px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  inset: -1px;
  background:
    radial-gradient(circle at 18% 24%, rgba(91, 95, 240, 0.32) 0%, transparent 55%),
    radial-gradient(circle at 86% 42%, rgba(56, 189, 248, 0.18) 0%, transparent 55%),
    radial-gradient(circle at 40% 120%, rgba(16, 185, 129, 0.14) 0%, transparent 58%);
  opacity: 0.9;
  pointer-events: none;
}

.hero__main {
  min-width: 0;
  position: relative;
  z-index: 1;
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(15, 23, 42, 0.5);
  color: rgba(226, 232, 240, 0.84);
  font-size: 12px;
  font-weight: 600;
}

.hero__title {
  margin: 10px 0 0;
  font-size: 42px;
  font-weight: 850;
  letter-spacing: -0.03em;
  line-height: 1.05;
  color: rgba(255, 255, 255, 0.96);
}

.hero__title-gradient {
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.98) 0%, rgba(202, 203, 253, 0.92) 35%, rgba(91, 95, 240, 0.95) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero__subtitle {
  margin: 14px 0 0;
  max-width: 680px;
  color: rgba(226, 232, 240, 0.78);
  font-size: 15px;
  line-height: 1.75;
}

.hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(2, 6, 23, 0.35);
  color: rgba(226, 232, 240, 0.86);
  font-size: 12px;
  font-weight: 600;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.hero__trust {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.trust-item {
  padding: 12px 12px 10px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.34);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(14px);
}

.trust-item__label {
  color: rgba(226, 232, 240, 0.7);
  font-size: 12px;
}

.trust-item__value {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.94);
  font-size: 13px;
  font-weight: 750;
}

.hero__visual {
  position: relative;
  z-index: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-card {
  width: 100%;
  max-width: 460px;
  position: relative;
  padding: 20px 18px 18px;
  border-radius: 26px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(2, 6, 23, 0.36);
  box-shadow:
    0 26px 80px rgba(0, 0, 0, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.visual-card__glow {
  position: absolute;
  inset: -1px;
  background:
    radial-gradient(circle at 20% 20%, rgba(91, 95, 240, 0.36) 0%, transparent 55%),
    radial-gradient(circle at 80% 34%, rgba(56, 189, 248, 0.2) 0%, transparent 58%),
    radial-gradient(circle at 60% 86%, rgba(16, 185, 129, 0.14) 0%, transparent 62%);
  opacity: 0.9;
  pointer-events: none;
}

.visual-card__top {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.visual-pill {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.5);
  color: rgba(226, 232, 240, 0.86);
  font-size: 12px;
  font-weight: 700;
}

.visual-metric {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.visual-metric__label {
  color: rgba(226, 232, 240, 0.66);
  font-size: 12px;
}

.visual-metric__value {
  color: rgba(255, 255, 255, 0.94);
  font-size: 14px;
  font-weight: 800;
}

.visual-flow {
  position: relative;
  margin-top: 16px;
  padding: 14px 12px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 22px;
  background: rgba(15, 23, 42, 0.32);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.flow-node {
  display: flex;
  align-items: center;
  gap: 10px;
}

.flow-node__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.08);
}

.flow-node__dot--content {
  background: rgba(56, 189, 248, 0.9);
}

.flow-node__dot--agent {
  background: rgba(91, 95, 240, 0.95);
}

.flow-node__dot--hot {
  background: rgba(236, 72, 153, 0.92);
}

.flow-node__dot--push {
  background: rgba(16, 185, 129, 0.92);
}

.flow-node__text {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.flow-node__title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.01em;
}

.flow-node__desc {
  color: rgba(226, 232, 240, 0.68);
  font-size: 12px;
}

.flow-line {
  height: 1px;
  background: rgba(148, 163, 184, 0.16);
  margin-left: 20px;
}

.visual-stats {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.stat-chip {
  padding: 10px 10px 9px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.26);
}

.stat-chip__label {
  color: rgba(226, 232, 240, 0.66);
  font-size: 11px;
}

.stat-chip__value {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
  font-weight: 800;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  padding: 2px 4px 0;
}

.section-title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 16px;
  font-weight: 800;
}

.section-subtitle {
  margin-top: 6px;
  color: rgba(226, 232, 240, 0.68);
  font-size: 13px;
  line-height: 1.6;
}

.section-head--spaced {
  margin-top: 6px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.feature-card {
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(2, 6, 23, 0.3);
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease;
  cursor: pointer;
  overflow: hidden;
}

:deep(.feature-card .el-card__body) {
  padding: 18px;
}

.feature-card:hover {
  transform: translateY(-2px);
  border-color: rgba(91, 95, 240, 0.32);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.34);
}

.feature-card.is-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.feature-card.is-disabled:hover {
  transform: none;
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: none;
}

.feature-card__inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 126px;
}

.feature-card__head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-card__icon {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.feature-card__title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 16px;
  font-weight: 850;
}

.feature-card__desc {
  color: rgba(226, 232, 240, 0.7);
  font-size: 13px;
  line-height: 1.7;
}

.feature-card__cta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(226, 232, 240, 0.76);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-top: auto;
}

.feature-card__arrow {
  display: inline-flex;
  transform: translateY(-1px);
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.workflow-card {
  padding: 18px 18px 16px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(2, 6, 23, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.workflow-card__step {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.42);
  color: rgba(226, 232, 240, 0.82);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.workflow-card__title {
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  font-weight: 850;
}

.workflow-card__desc {
  margin-top: 10px;
  color: rgba(226, 232, 240, 0.68);
  font-size: 13px;
  line-height: 1.7;
}

.cta-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 20px;
  border-radius: 26px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(135deg, rgba(91, 95, 240, 0.22) 0%, rgba(2, 6, 23, 0.36) 60%, rgba(56, 189, 248, 0.16) 100%);
  box-shadow:
    0 30px 90px rgba(0, 0, 0, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
}

.cta-band__title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 18px;
  font-weight: 900;
}

.cta-band__subtitle {
  margin-top: 6px;
  color: rgba(226, 232, 240, 0.72);
  font-size: 13px;
}

.cta-band__actions {
  flex-shrink: 0;
}

@media (max-width: 1280px) {
  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workflow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .hero__title {
    font-size: 34px;
  }

  .hero__trust {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .cta-band {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 720px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }

  .workflow-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .hero__trust {
    grid-template-columns: 1fr;
  }
}
</style>
