<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import type { UploadProps } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";

import PageSectionHeader from "@/components/PageSectionHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { uploadFile } from "@/api/modules/system";
import { fileCategoryOptions } from "@/constants/permissions";
import type { FileAssetItem } from "@/types/system";

const loading = ref(false);
const uploadedFiles = ref<FileAssetItem[]>([]);

const accept = ".jpg,.jpeg,.png,.webp,.mp3,.wav,.aac,.mp4,.mov,.mkv,.txt,.pdf,.doc,.docx";
const maxSizeMb = 200;

const recentUploads = computed(() => uploadedFiles.value.slice(0, 8));

const beforeUpload: UploadProps["beforeUpload"] = (file) => {
  const sizeMb = file.size / 1024 / 1024;
  if (sizeMb > maxSizeMb) {
    ElMessage.error(`单文件不能超过 ${maxSizeMb}MB`);
    return false;
  }
  return true;
};

const handleUpload: UploadProps["httpRequest"] = async (options) => {
  loading.value = true;
  try {
    const response = await uploadFile(options.file as File);
    uploadedFiles.value = [response.data, ...uploadedFiles.value];
    options.onSuccess?.(response.data as any);
    ElMessage.success("上传成功");
  } catch (error) {
    options.onError?.(error as any);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  uploadedFiles.value = [];
});
</script>

<template>
  <div class="page-shell">
    <PageSectionHeader
      title="文件中心"
      description="后端当前只开放上传接口，所以这里聚焦于真实上传、返回结果和预览。"
    />

    <div class="responsive-two-col">
      <el-card shadow="never">
        <template #header>统一上传入口</template>
        <el-upload
          drag
          :accept="accept"
          :show-file-list="false"
          :before-upload="beforeUpload"
          :http-request="handleUpload"
        >
          <el-icon style="font-size: 36px; color: #1f9d62"><UploadFilled /></el-icon>
          <div style="margin-top: 12px; font-size: 16px; color: #172030">
            拖拽文件到这里，或点击上传
          </div>
          <div class="muted-text" style="margin-top: 8px">
            支持图片、音频、视频和文档，单文件上限 200MB
          </div>
        </el-upload>
      </el-card>

      <el-card shadow="never">
        <template #header>上传规范</template>
        <el-descriptions
          :column="1"
          border
        >
          <el-descriptions-item label="支持类别">
            图片 / 音频 / 视频 / 文档 / 其他
          </el-descriptions-item>
          <el-descriptions-item label="存储后端">
            本地存储，后续可无缝切到 OSS
          </el-descriptions-item>
          <el-descriptions-item label="预览方式">
            返回 `url` 直接用于预览或下载
          </el-descriptions-item>
          <el-descriptions-item label="返回字段">
            original_name、storage_name、category、content_type、storage_path、url
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header>最近上传</template>
      <el-table :data="recentUploads">
        <el-table-column
          prop="original_name"
          label="文件名"
          min-width="220"
        />
        <el-table-column
          prop="storage_name"
          label="存储名"
          min-width="220"
        />
        <el-table-column
          label="类别"
          width="120"
        >
          <template #default="{ row }">
            <StatusTag :status="row.category" />
          </template>
        </el-table-column>
        <el-table-column
          prop="content_type"
          label="内容类型"
          min-width="160"
        />
        <el-table-column
          prop="size"
          label="大小(字节)"
          width="130"
        />
        <el-table-column
          prop="storage_backend"
          label="存储后端"
          width="140"
        />
        <el-table-column
          prop="storage_path"
          label="存储路径"
          min-width="220"
        />
        <el-table-column
          label="预览"
          width="120"
        >
          <template #default="{ row }">
            <el-link
              :href="row.url"
              target="_blank"
              type="primary"
            >
              打开
            </el-link>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="上传时间"
          min-width="180"
        />
      </el-table>

      <div
        v-if="recentUploads.length === 0"
        class="empty-helper"
      >
        还没有上传过文件，先传一张图或一个视频试试。
      </div>
    </el-card>
  </div>
</template>
