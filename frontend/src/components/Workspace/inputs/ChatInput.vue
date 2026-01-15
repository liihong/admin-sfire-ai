<template>
  <div class="chat-input">
    <div class="chat-messages" ref="messagesRef">
      <div v-for="(msg, index) in messages" :key="index" class="chat-message" :class="msg.role">
        <!-- AI 头像 -->
        <div v-if="msg.role === 'assistant'" class="message-avatar">
          <!-- <img :src="agentAvatar" :alt="agentName" /> -->
          <img class="logo-img" src="@/assets/images/logo.svg" alt="logo" />
        </div>
        <div v-else class="message-avatar">
          <img class="user-avatar" :src="userAvatar" />
        </div>

        <div class="message-wrapper">
          <div class="message-content">{{ msg.content }}</div>
          <!-- Use this Text button for AI messages -->
          <el-button
            v-if="msg.role === 'assistant'"
            type="primary"
            size="small"
            text
            class="use-text-btn"
            @click="handleUseText(msg.content)"
          >
            <el-icon><ArrowRight /></el-icon>
            <span>使用该文案</span>
          </el-button>
        </div>
      </div>

      <!-- AI 思考中的 loading 状态 -->
      <div v-if="isGenerating && !currentContent" class="chat-message assistant thinking">
        <div class="message-avatar">
          <!-- <img :src="agentAvatar" :alt="agentName" /> -->
          <img class="logo-img" src="@/assets/images/logo.svg" alt="logo" />
        </div>

        <div class="message-content thinking-content">
          <div class="thinking-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
          <span class="thinking-text">{{ agentName }}正在思考...</span>
        </div>
      </div>

      <!-- 中间栏对话区：生成中时使用打字机效果展示当前 AI 回复 -->
      <div v-if="isGenerating && currentContent" class="chat-message assistant typing">
        <div class="message-avatar">
          <!-- <img :src="agentAvatar" :alt="agentName" /> -->
          <img class="logo-img" src="@/assets/images/logo.svg" alt="logo" />
        </div>

        <p class="message-content">
          {{ currentContent }}
          <span class="typing-cursor">|</span>
        </p>
      </div>
    </div>

    <div class="chat-input-area">
      <!-- Quick Actions Row -->
      <!-- <div class="quick-actions">
        <el-button
          size="small"
          text
          @click="handleQuickAction('Make it shorter')"
        >
          <el-icon><Minus /></el-icon>
          Make it shorter
        </el-button>
        <el-button
          size="small"
          text
          @click="handleQuickAction('More emotional')"
        >
          <el-icon><Star /></el-icon>
          More emotional
        </el-button>
        <el-button
          size="small"
          text
          @click="handleQuickAction('Add emojis')"
        >
          <el-icon><ChatDotRound /></el-icon>
          Add emojis
        </el-button>
        <el-button
          size="small"
          text
          @click="handleQuickAction('Generate Storyboard')"
        >
          <el-icon><Notebook /></el-icon>
          Generate Storyboard
        </el-button>
      </div> -->
      <div class="ai-input">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="4"
          placeholder="输入您的创作需求..."
          class="ip-os-input"
          @keydown.enter.exact.prevent="handleSubmit"
          @keydown.enter.shift.exact="handleShiftEnter"
        />
        <div class="chat-input-actions">
          <el-button class="input-btn" type="primary" :disabled="!inputText.trim() || isGenerating" @click="handleSubmit">
            发送
          </el-button>
        </div>
      </div>
      <div class="ai-tip">提示：回答由 AI 生成，内容仅供参考，请仔细甄别。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { ArrowRight } from "@element-plus/icons-vue";
import type { MPAgentInfo } from "@/api/modules/miniprogram";
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";

interface Props {
  agent: MPAgentInfo;
  conversationHistory: Array<{ role: "user" | "assistant"; content: string }>;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  submit: [content: string];
  "update:conversation": [messages: Array<{ role: "user" | "assistant"; content: string }>];
  "use-text": [content: string];
}>();

const ipCreationStore = useIPCreationStore();
const mpUserStore = useMPUserStore();

const inputText = ref("");
const messagesRef = ref<HTMLElement>();
const isGenerating = computed(() => ipCreationStore.isGenerating);
const currentContent = computed(() => ipCreationStore.currentContent);

const messages = computed(() => props.conversationHistory);

const userAvatar = computed(() => mpUserStore.userDetail.avatar);

// AI 头像和名称
const agentAvatar = computed(() => {
  // 使用默认头像
  return "@/assets/images/sfire-logo.png";
});

const agentName = computed(() => {
  return props.agent.name || "AI助手";
});

// Handle "Use this Text" button click
const handleUseText = (content: string) => {
  emit("use-text", content);
};

// Handle Quick Actions
const handleQuickAction = (action: string) => {
  inputText.value = action;
  // Optionally auto-submit after a short delay
  // setTimeout(() => {
  //   handleSubmit();
  // }, 300);
};

// 自动滚动到底部
watch(
  () => messages.value.length,
  () => {
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
      }
    });
  },
  { immediate: true }
);

// 监听当前生成内容的变化，自动滚动
watch(
  () => currentContent.value,
  () => {
    nextTick(() => {
      if (messagesRef.value && isGenerating.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
      }
    });
  }
);

const handleSubmit = () => {
  if (!inputText.value.trim() || isGenerating.value) return;

  const content = inputText.value.trim();
  inputText.value = "";

  emit("submit", content);
};

const handleShiftEnter = () => {
  // Shift+Enter 换行，不做任何处理
};
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.chat-input {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  margin-bottom: 16px;
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid var(--ip-os-border-primary);
  @extend .ip-os-scrollbar;

  .chat-message {
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
    gap: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    .message-avatar {
      flex-shrink: 0;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      overflow: hidden;
      background: var(--ip-os-bg-primary);
      border: 2px solid var(--ip-os-accent-primary);
      box-shadow: 0 2px 8px var(--ip-os-accent-glow);

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .message-content {
      padding: 12px 16px;
      border-radius: 12px;
      max-width: 70%;
      line-height: 1.6;
      font-size: 14px;
      white-space: pre-wrap;
      word-wrap: break-word;
      background: lightgray;
    }

    &.user {
      flex-direction: row-reverse;

      .message-content {
        margin-left: auto;
        background: var(--ip-os-accent-primary);
        color: #ffffff;
        border-radius: 12px 12px 4px 12px;
        box-shadow: 0 2px 8px rgba(255, 107, 53, 0.2);
      }
    }

    &.assistant {
      .message-content {
        background: #f5f5f5;
        color: var(--ip-os-text-primary);
        border: 1px solid var(--ip-os-border-secondary);
        border-radius: 12px 12px 12px 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      }
      .user-avatar{

      }
    }

    &.thinking {
      .message-content {
        background: var(--ip-os-bg-primary);
        border: 1px solid var(--ip-os-border-secondary);
        border-radius: 12px 12px 12px 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      }

      .thinking-content {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
      }

      .thinking-dots {
        display: flex;
        gap: 4px;

        .dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--ip-os-accent-primary);
          animation: thinking-pulse 1.4s infinite ease-in-out;

          &:nth-child(1) {
            animation-delay: 0s;
          }

          &:nth-child(2) {
            animation-delay: 0.2s;
          }

          &:nth-child(3) {
            animation-delay: 0.4s;
          }
        }
      }

      .thinking-text {
        font-size: 13px;
        color: var(--ip-os-text-secondary);
      }
    }

    &.typing {
      .message-content {
        position: relative;
      }

      .typing-cursor {
        display: inline-block;
        margin-left: 2px;
        animation: blink 1s infinite;
        color: var(--ip-os-accent-primary);
        font-weight: bold;
      }
    }
  }
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}

@keyframes thinking-pulse {
  0%,
  60%,
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
  30% {
    transform: scale(1.3);
    opacity: 1;
  }
}

.chat-input-area {
  margin-bottom: 30px;
  .ai-input {
    display: flex;
  }
  .ai-tip {
    color: darkgray;
    text-align: center;
    font-size: 12px;
  }
  .quick-actions {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;

    .el-button {
      font-size: 12px;
      padding: 4px 8px;
      color: var(--ip-os-text-secondary);
      transition: all 0.2s ease;

      &:hover {
        color: var(--ip-os-accent-primary);
        background: rgba(255, 107, 53, 0.08);
      }

      .el-icon {
        font-size: 14px;
      }
    }
  }

  .ip-os-input {
    margin-bottom: 12px;
  }

  .chat-input-actions {
    display: flex;
    margin-left: 10px;
    justify-content: flex-end;
    .input-btn{
      height: 90%;
    }
  }
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 70%;

  .use-text-btn {
    align-self: flex-start;
    font-size: 12px;
    padding: 4px 8px;
    color: var(--ip-os-accent-primary);
    background: rgba(255, 107, 53, 0.08);
    border-radius: 6px;
    transition: all 0.2s ease;
    margin-top: 4px;

    &:hover {
      background: rgba(255, 107, 53, 0.15);
      transform: translateX(2px);
    }

    .el-icon {
      font-size: 14px;
      margin-right: 4px;
    }

    span {
      font-size: 12px;
    }
  }
}
</style>
