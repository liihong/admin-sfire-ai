<template>
  <div class="douyin-caption">
    <el-page-header @back="goBack" title="返回" content="抖音文案提取" />
    <el-card class="step-card" shadow="never">
      <template #header>
        <span>粘贴抖音视频链接</span>
      </template>
      <p class="tip">
        支持分享短链或浏览器打开的视频页链接。解析与语音识别由 TikHub、火山引擎在云端完成，本服务器不保存视频或音频文件。
      </p>
      <el-input
        v-model="shareUrl"
        type="textarea"
        :rows="3"
        placeholder="例如：https://v.douyin.com/xxxxx/"
        clearable
      />
      <el-button
        type="primary"
        class="extract-btn"
        :loading="loading"
        :disabled="!shareUrl.trim()"
        @click="doExtract"
      >
        提取口播文案
      </el-button>
    </el-card>

    <el-card v-if="resultText !== null" class="step-card" shadow="never">
      <template #header>
        <span>识别结果</span>
      </template>
      <p v-if="videoTitle" class="meta">标题：{{ videoTitle }}</p>
      <el-input v-model="resultText" type="textarea" :rows="12" readonly />
      <el-button class="copy-btn" @click="copyText">复制全文</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts" name="DouyinCaption">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  extractDouyinCaptionApi,
  adminExtractDouyinCaptionApi
} from "@/api/modules/tools";

const route = useRoute();
const router = useRouter();
const isAdminTool = () => route.path.startsWith("/tool-kit");

const shareUrl = ref("");
const loading = ref(false);
const resultText = ref<string | null>(null);
const videoTitle = ref<string | null>(null);

const doExtract = async () => {
  const url = shareUrl.value.trim();
  if (!url) {
    ElMessage.warning("请先粘贴抖音链接");
    return;
  }
  loading.value = true;
  resultText.value = null;
  videoTitle.value = null;
  try {
    const res = isAdminTool()
      ? await adminExtractDouyinCaptionApi({ url })
      : await extractDouyinCaptionApi({ url });
    const data = res?.data as { text?: string; title?: string } | undefined;
    if (data?.text != null) {
      resultText.value = data.text;
      videoTitle.value = data.title ?? null;
      ElMessage.success("提取成功");
    }
  } catch (e: unknown) {
    const err = e as { msg?: string };
    ElMessage.error(err?.msg || "提取失败");
  } finally {
    loading.value = false;
  }
};

const copyText = async () => {
  if (!resultText.value) return;
  try {
    await navigator.clipboard.writeText(resultText.value);
    ElMessage.success("已复制");
  } catch {
    ElMessage.warning("复制失败，请手动选择文本复制");
  }
};

const goBack = () => {
  router.push(isAdminTool() ? "/tool-kit/list" : "/mp/tools");
};
</script>

<style scoped lang="scss">
.douyin-caption {
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

  .extract-btn {
    margin-top: 16px;
  }

  .meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
  }

  .copy-btn {
    margin-top: 12px;
  }
}
</style>
