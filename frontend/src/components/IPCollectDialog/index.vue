<template>
  <el-dialog
    :model-value="visible"
    title="AI智能填写"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
    @update:model-value="handleUpdateVisible"
  >
    <!-- 步骤指示器 -->
    <div class="step-indicator">
      <div
        v-for="(step, index) in steps"
        :key="index"
        class="step-item"
        :class="{ active: currentStep >= index, completed: currentStep > index }"
      >
        <div class="step-dot">
          <el-icon v-if="currentStep > index"><Check /></el-icon>
          <span v-else class="step-number">{{ index + 1 }}</span>
        </div>
        <span class="step-label">{{ step.label }}</span>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="dialog-messages" ref="messagesRef">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-item"
        :class="msg.role"
      >
        <div class="message-avatar">
           <img class="logo-img" src="@/assets/images/logo.svg" alt="logo" />
        </div>
        <div class="message-bubble">
          <div class="message-text">{{ msg.content }}</div>
        </div>
      </div>

      <!-- 加载中提示 -->
      <div class="message-item assistant" v-if="isLoading">
        <div class="message-avatar"></div>
        <div class="message-bubble loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI正在思考...</span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="dialog-input-area" v-if="!isComplete">
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="3"
        placeholder="请输入..."
        :disabled="isLoading"
        @keydown.enter.ctrl="handleSend"
      />
      <div class="input-actions">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="isLoading"
          :disabled="!userInput.trim()"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>

    <!-- 完成按钮 -->
    <template #footer v-if="isComplete">
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleComplete">完成采集</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { Check, User, Loading } from "@element-plus/icons-vue";
import { aiCollectIPInfoApi, type IPCollectRequest } from "@/api/modules/miniprogram";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp?: number;
}

interface Props {
  visible: boolean;
}

interface Emits {
  (e: "close"): void;
  (e: "complete", data: CollectedIPInfo): void;
}

/**
 * 收集的IP信息结构
 */
interface CollectedIPInfo {
  name?: string;
  industry?: string;
  introduction?: string;
  tone?: string;
  target_audience?: string;
  catchphrase?: string;
  keywords?: string[];
  [key: string]: any;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 步骤定义
const steps = [
  { label: "基本信息", key: "basic" },
  { label: "IP简介", key: "intro" },
  { label: "风格受众", key: "style" },
  { label: "标签关键词", key: "tags" }
];

// 状态
const currentStep = ref(0);
const messages = ref<Message[]>([]);
const userInput = ref("");
const isLoading = ref(false);
const isComplete = ref(false);
const messagesRef = ref<HTMLElement>();
const collectedInfo = ref<CollectedIPInfo>({});

// 初始化对话
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      initDialog();
    }
  }
);

function initDialog() {
  currentStep.value = 0;
  messages.value = [];
  userInput.value = "";
  isLoading.value = false;
  isComplete.value = false;
  collectedInfo.value = {};

  // 添加欢迎消息
  // addMessage("assistant", "你好！我是火源IP信息收集助手，将帮助你完善IP信息。让我们开始吧！");

  // 发送初始请求
  sendMessage("", true);
}

function addMessage(role: "user" | "assistant", content: string) {
  messages.value.push({
    role,
    content,
    timestamp: Date.now()
  });
  scrollToBottom();
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
    }
  });
}

async function sendMessage(input: string, isInit = false) {
  if (!isInit && !input.trim()) return;

  // 添加用户消息
  if (!isInit) {
    addMessage("user", input);
    userInput.value = "";
  }

  isLoading.value = true;

  try {
    const { data } = await aiCollectIPInfoApi({
      messages: messages.value.map((msg) => ({
        role: msg.role,
        content: msg.content
      })),
      step: currentStep.value,
      context: collectedInfo.value
    });

    if (data) {
      // 添加AI回复
      addMessage("assistant", data.reply);

      // 更新收集的信息
      if (data.collected_info) {
        Object.assign(collectedInfo.value, data.collected_info);
      }

      // 检查是否完成
      if (data.is_complete) {
        isComplete.value = true;
      } else if (data.next_step !== undefined) {
        currentStep.value = data.next_step;
      }
    }
  } catch (error: any) {
    console.error("采集对话失败:", error);
    // 安全处理错误消息，避免暴露敏感系统信息
    const errorMsg = getSafeErrorMessage(error);
    addMessage("assistant", `抱歉，出现了错误：${errorMsg}`);
    ElMessage.error(errorMsg);
  } finally {
    isLoading.value = false;
  }
}

function handleSend() {
  if (!userInput.value.trim() || isLoading.value) return;
  sendMessage(userInput.value);
}

function handleComplete() {
  emit("complete", collectedInfo.value);
  handleClose();
}

function handleClose() {
  emit("close");
}

function handleUpdateVisible(value: boolean) {
  if (!value) {
    emit("close");
  }
}

/**
 * 安全处理错误消息，避免暴露敏感系统信息
 */
function getSafeErrorMessage(error: any): string {
  const msg = error?.msg || error?.message || "";

  // 根据错误类型返回安全的错误消息
  if (msg.includes("余额不足")) {
    return "余额不足，请充值后重试";
  }
  if (msg.includes("认证") || msg.includes("登录") || msg.includes("token")) {
    return "登录已过期，请重新登录";
  }
  if (msg.includes("网络") || msg.includes("连接")) {
    return "网络连接异常，请检查网络后重试";
  }
  if (msg.includes("超时")) {
    return "请求超时，请稍后重试";
  }

  // 默认返回通用错误消息
  return "服务暂时不可用，请稍后重试";
}
</script>

<style scoped lang="scss">
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 20px 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;

  .step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex: 1;

    .step-dot {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;

      .step-number {
        font-size: 14px;
        color: #9ca3af;
        font-weight: 600;
      }

      .el-icon {
        font-size: 16px;
        color: #fff;
      }
    }

    .step-label {
      font-size: 12px;
      color: #9ca3af;
    }

    &.active {
      .step-dot {
        background: #3b82f6;

        .step-number {
          color: #fff;
        }
      }

      .step-label {
        color: #3b82f6;
        font-weight: 500;
      }
    }

    &.completed {
      .step-dot {
        background: #22c55e;
      }

      .step-label {
        color: #22c55e;
      }
    }
  }
}

.dialog-messages {
  max-height: 400px;
  min-height: 300px;
  overflow-y: auto;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;

  &.user {
    flex-direction: row-reverse;

    .message-bubble {
      background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
      color: #fff;
    }
  }

  &.assistant {
    .message-bubble {
      background: #fff;
      color: #333;
      border: 1px solid #e5e7eb;
    }
  }

  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    .el-icon {
      font-size: 18px;
      color: #6b7280;
    }
  }

  .message-bubble {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 12px;
    word-wrap: break-word;

    .message-text {
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
    }

    &.loading {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;

      .el-icon {
        font-size: 16px;
      }

      span {
        font-size: 14px;
        color: #6b7280;
      }
    }
  }
}

.dialog-input-area {
  .input-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 12px;
  }
}
</style>

