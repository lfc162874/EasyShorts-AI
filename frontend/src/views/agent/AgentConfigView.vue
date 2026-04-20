<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import ArtifactViewer from "@/components/ArtifactViewer.vue";
import MetricCard from "@/components/MetricCard.vue";
import PageSectionHeader from "@/components/PageSectionHeader.vue";
import { getAgentConfig, listAgentModels, saveAgentConfig } from "@/api/modules/agent";
import { agentPushChannelOptions } from "@/constants/permissions";
import type { AgentConfigItem, AgentModelItem, AgentConfigUpdateForm } from "@/types/agent";
import { resolveAgentModelOptions, resolveDefaultAgentModel } from "@/utils/agent";

const loading = ref(false);
const saving = ref(false);
const formRef = ref<FormInstance>();
const config = ref<AgentConfigItem | null>(null);
const modelOptions = ref<AgentModelItem[]>([]);

const form = reactive({
  default_model_name: "",
  supported_models: [] as string[],
  default_provider: "",
  prompt_version: "",
  push_channels: [] as string[],
});

const rules: FormRules<typeof form> = {
  default_model_name: [{ required: true, message: "请选择默认模型", trigger: "change" }],
  default_provider: [{ required: true, message: "请输入默认提供方", trigger: "blur" }],
  prompt_version: [{ required: true, message: "请输入提示词版本", trigger: "blur" }],
};

const loadData = async () => {
  loading.value = true;
  try {
    const [configResponse, modelResponse] = await Promise.all([getAgentConfig(), listAgentModels()]);
    config.value = configResponse.data;
    modelOptions.value = resolveAgentModelOptions(
      modelResponse.data,
      configResponse.data.supported_models,
    );
    form.default_model_name =
      configResponse.data.default_model_name ||
      resolveDefaultAgentModel(modelOptions.value);
    form.supported_models = [...configResponse.data.supported_models];
    form.default_provider = configResponse.data.default_provider;
    form.prompt_version = configResponse.data.prompt_version;
    form.push_channels = [...configResponse.data.push_channels];
  } finally {
    loading.value = false;
  }
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const payload: AgentConfigUpdateForm = {
    default_model_name: form.default_model_name || null,
    supported_models: form.supported_models,
    default_provider: form.default_provider || null,
    prompt_version: form.prompt_version || null,
    push_channels: form.push_channels,
  };

  saving.value = true;
  try {
    await saveAgentConfig(payload);
    ElMessage.success("Agent 配置已更新");
    await loadData();
  } finally {
    saving.value = false;
  }
};

const metrics = computed(() => [
  { label: "默认模型", value: config.value?.default_model_name || "-", hint: "运行时默认使用的模型" },
  { label: "支持模型", value: String(config.value?.supported_models.length ?? 0), hint: "当前支持的模型总数" },
  { label: "默认渠道", value: String(config.value?.push_channels.length ?? 0), hint: "默认推送渠道数量" },
  { label: "热度阈值", value: String(config.value?.hot_threshold ?? 0), hint: "热点判断的阈值" },
]);

onMounted(loadData);
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="模型配置"
      description="维护 Agent 默认模型、支持模型、默认提供方和推送渠道。热度阈值由系统参数提供，只读展示。"
    >
      <el-button @click="loadData">刷新</el-button>
      <el-button
        type="primary"
        :loading="saving"
        @click="handleSubmit"
      >
        保存配置
      </el-button>
    </PageSectionHeader>

    <div class="grid-cards">
      <MetricCard
        v-for="metric in metrics"
        :key="metric.label"
        :label="metric.label"
        :value="metric.value"
        :hint="metric.hint"
      />
    </div>

    <div class="responsive-two-col">
      <el-card
        v-loading="loading"
        shadow="never"
      >
        <template #header>Agent配置表单</template>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
        >
          <el-form-item label="默认模型" prop="default_model_name">
            <el-select
              v-model="form.default_model_name"
              filterable
              allow-create
              default-first-option
              placeholder="选择默认模型"
              style="width: 100%"
            >
              <el-option
                v-for="item in modelOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="支持模型">
            <el-select
              v-model="form.supported_models"
              filterable
              allow-create
              default-first-option
              multiple
              collapse-tags
              placeholder="可输入或选择多个模型"
              style="width: 100%"
            >
              <el-option
                v-for="item in modelOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item
            label="默认提供方"
            prop="default_provider"
          >
            <el-input
              v-model="form.default_provider"
              placeholder="例如 rule_based"
            />
          </el-form-item>
          <el-form-item
            label="提示词版本"
            prop="prompt_version"
          >
            <el-input
              v-model="form.prompt_version"
              placeholder="例如 v1"
            />
          </el-form-item>
          <el-form-item label="默认推送渠道">
            <el-select
              v-model="form.push_channels"
              filterable
              allow-create
              default-first-option
              multiple
              collapse-tags
              placeholder="可输入或选择多个渠道"
              style="width: 100%"
            >
              <el-option
                v-for="item in agentPushChannelOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header>运行参数</template>
        <el-descriptions
          v-if="config"
          :column="1"
          border
        >
          <el-descriptions-item label="默认模型">
            {{ config.default_model_name }}
          </el-descriptions-item>
          <el-descriptions-item label="默认提供方">
            {{ config.default_provider }}
          </el-descriptions-item>
          <el-descriptions-item label="提示词版本">
            {{ config.prompt_version }}
          </el-descriptions-item>
          <el-descriptions-item label="热度阈值">
            {{ config.hot_threshold }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">支持模型</el-divider>
        <div class="tag-row">
          <el-tag
            v-for="model in config?.supported_models || []"
            :key="model"
            effect="plain"
          >
            {{ model }}
          </el-tag>
        </div>

        <el-divider content-position="left">推送渠道</el-divider>
        <div class="tag-row">
          <el-tag
            v-for="channel in config?.push_channels || []"
            :key="channel"
            effect="plain"
          >
            {{ channel }}
          </el-tag>
        </div>

        <el-divider content-position="left">Prompt 模板</el-divider>
        <ArtifactViewer
          title="Prompt 配置"
          :content-json="config?.prompts"
          empty-text="暂无 Prompt 配置"
        />
      </el-card>
    </div>
  </div>
</template>
