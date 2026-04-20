<script setup lang="ts">
import StatusTag from "@/components/StatusTag.vue";
import type { AgentRunStepItem } from "@/types/agent";

const props = defineProps<{
  steps: AgentRunStepItem[];
  activeStepId?: number | null;
}>();

const emit = defineEmits<{
  (event: "select-step", step: AgentRunStepItem): void;
}>();

const formatDuration = (value?: number | null): string => {
  if (value === null || value === undefined) {
    return "进行中";
  }
  if (value < 1000) {
    return `${value} ms`;
  }
  if (value < 60_000) {
    return `${(value / 1000).toFixed(1)} s`;
  }
  return `${(value / 60_000).toFixed(1)} min`;
};

const isStepActive = (step: AgentRunStepItem) => props.activeStepId === step.id;
</script>

<template>
  <div class="agent-flow-board">
    <button
      v-for="step in steps"
      :key="step.id"
      type="button"
      class="agent-flow-node"
      :class="{
        'is-active': isStepActive(step),
        'is-running': step.status === 'RUNNING',
        'is-success': step.status === 'SUCCESS',
        'is-failed': step.status === 'FAILED',
      }"
      @click="emit('select-step', step)"
    >
      <div class="agent-flow-node__head">
        <span class="agent-flow-node__index">{{ step.step_order }}</span>
        <StatusTag :status="step.status" />
      </div>
      <div class="agent-flow-node__name">{{ step.agent_name }}</div>
      <div class="agent-flow-node__code">{{ step.step_code }}</div>
      <div class="agent-flow-node__meta">{{ formatDuration(step.duration_ms) }}</div>
    </button>
  </div>
</template>

<style scoped lang="scss">
.agent-flow-board {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.agent-flow-node {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 132px;
  padding: 14px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #fbfcfe;
  color: var(--app-text);
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.agent-flow-node:hover {
  transform: translateY(-1px);
  border-color: rgba(31, 157, 98, 0.32);
  box-shadow: 0 10px 22px rgba(22, 32, 51, 0.06);
}

.agent-flow-node.is-active {
  border-color: rgba(31, 157, 98, 0.65);
  background: rgba(31, 157, 98, 0.05);
  box-shadow: 0 10px 24px rgba(31, 157, 98, 0.08);
}

.agent-flow-node.is-failed {
  border-color: rgba(220, 38, 38, 0.32);
}

.agent-flow-node__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.agent-flow-node__index {
  display: inline-grid;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 999px;
  background: rgba(31, 157, 98, 0.1);
  color: var(--app-primary-strong);
  font-size: 13px;
  font-weight: 700;
}

.agent-flow-node__name {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
}

.agent-flow-node__code,
.agent-flow-node__meta {
  color: var(--app-muted);
  font-size: 12px;
  line-height: 1.5;
}
</style>
