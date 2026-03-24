<template>
  <div class="voice-clone">
    <el-page-header @back="goBack" title="返回" content="声音复刻" />
    <el-card class="step-card" shadow="never">
      <template #header>
        <span>步骤 1：上传训练音频</span>
      </template>
      <p class="tip">请上传 5 秒以上的清晰人声音频（wav 或 mp3），建议在安静环境下录制</p>
      <el-upload
        class="upload-area"
        drag
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        accept=".wav,.mp3,audio/wav,audio/mpeg"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          {{ uploadFile ? uploadFile.name : "点击或拖拽文件到此处" }}
        </div>
      </el-upload>
      <el-button
        type="primary"
        :loading="uploading"
        :disabled="!uploadFile"
        @click="doUpload"
      >
        上传并训练
      </el-button>
    </el-card>

    <el-card class="step-card" shadow="never">
      <template #header>
        <span>步骤 2：训练状态</span>
      </template>
      <div v-if="status.has_speaker" class="status-info">
        <p>状态：{{ statusText }}</p>
        <p v-if="status.train_version">训练次数：{{ status.train_version }}/10</p>
        <el-button
          v-if="status.status === 'training'"
          type="primary"
          link
          :loading="statusLoading"
          @click="fetchStatus"
        >
          刷新状态
        </el-button>
      </div>
      <el-empty v-else description="请先上传音频" :image-size="80" />
    </el-card>

    <el-card class="step-card" shadow="never">
      <template #header>
        <span>步骤 3：试听合成</span>
      </template>
      <el-input
        v-model="synthesizeText"
        type="textarea"
        :rows="4"
        placeholder="输入要合成的文本（需音色训练完成后）"
        maxlength="500"
        show-word-limit
      />
      <el-button
        type="primary"
        :loading="synthesizing"
        :disabled="!status.has_speaker || status.status !== 'success'"
        @click="doSynthesize"
      >
        合成试听
      </el-button>
      <audio v-if="audioUrl" :src="audioUrl" controls class="audio-player" />
    </el-card>
  </div>
</template>

<script setup lang="ts" name="VoiceClone">
import { ref, reactive, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import {
  uploadVoiceAudioApi,
  getVoiceTrainStatusApi,
  synthesizeVoiceApi,
  adminUploadVoiceAudioApi,
  adminGetVoiceTrainStatusApi,
  adminSynthesizeVoiceApi
} from "@/api/modules/tools";
import type { VoiceTrainStatus } from "@/api/modules/tools";

const route = useRoute();
const router = useRouter();

const isAdminTool = computed(() => route.path.startsWith("/tool-kit"));

const uploadFile = ref<File | null>(null);
const uploading = ref(false);
const status = reactive<VoiceTrainStatus>({
  has_speaker: false,
  speaker_id: null,
  status: "pending",
  train_version: 0
});
const statusLoading = ref(false);
const synthesizeText = ref("");
const synthesizing = ref(false);
const audioUrl = ref("");

const statusText = computed(() => {
  const map: Record<string, string> = {
    pending: "待训练",
    training: "训练中",
    success: "已完成",
    failed: "训练失败"
  };
  return map[status.status] || status.status;
});

const handleFileChange = (uf: { raw?: File } | null) => {
  uploadFile.value = uf?.raw ?? null;
};

const doUpload = async () => {
  if (!uploadFile.value) return;
  uploading.value = true;
  try {
    const res = isAdminTool.value
      ? await adminUploadVoiceAudioApi(uploadFile.value)
      : await uploadVoiceAudioApi(uploadFile.value);
    const data = res?.data;
    if (data) {
      status.has_speaker = true;
      status.speaker_id = data.speaker_id;
      status.status = data.status;
      status.train_version = data.train_version ?? 0;
      ElMessage.success("上传成功，正在训练，请稍后刷新状态");
    }
  } catch (e: unknown) {
    const err = e as { msg?: string };
    ElMessage.error(err?.msg || "上传失败");
  } finally {
    uploading.value = false;
  }
};

const fetchStatus = async () => {
  statusLoading.value = true;
  try {
    const res = isAdminTool.value
      ? await adminGetVoiceTrainStatusApi()
      : await getVoiceTrainStatusApi();
    const data = res?.data;
    if (data) {
      status.has_speaker = data.has_speaker;
      status.speaker_id = data.speaker_id;
      status.status = data.status;
      status.train_version = data.train_version ?? 0;
    }
  } catch (e: unknown) {
    const err = e as { msg?: string };
    ElMessage.error(err?.msg || "查询失败");
  } finally {
    statusLoading.value = false;
  }
};

const doSynthesize = async () => {
  if (!synthesizeText.value.trim()) {
    ElMessage.warning("请输入要合成的文本");
    return;
  }
  synthesizing.value = true;
  audioUrl.value = "";
  try {
    const res = isAdminTool.value
      ? await adminSynthesizeVoiceApi({ text: synthesizeText.value.trim() })
      : await synthesizeVoiceApi({ text: synthesizeText.value.trim() });
    const data = res?.data;
    if (data?.audio_base64) {
      audioUrl.value = `data:audio/mpeg;base64,${data.audio_base64}`;
      ElMessage.success("合成成功");
    }
  } catch (e: unknown) {
    const err = e as { msg?: string };
    ElMessage.error(err?.msg || "合成失败");
  } finally {
    synthesizing.value = false;
  }
};

const goBack = () => {
  router.push(isAdminTool.value ? "/tool-kit/list" : "/mp/tools");
};

onMounted(() => {
  fetchStatus();
});
</script>

<style scoped lang="scss">
.voice-clone {
  max-width: 640px;
  margin: 0 auto;
}

.step-card {
  margin-top: 20px;

  .tip {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-bottom: 16px;
  }

  .upload-area {
    margin-bottom: 16px;
  }

  .upload-icon {
    font-size: 48px;
    color: var(--el-color-primary);
  }

  .upload-text {
    font-size: 14px;
    color: var(--el-text-color-regular);
  }

  .status-info {
    p {
      margin: 8px 0;
    }
  }

  .audio-player {
    margin-top: 16px;
    width: 100%;
  }
}
</style>
