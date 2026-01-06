<template>
  <div class="chat-input">
    <div class="chat-messages" ref="messagesRef">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="chat-message"
        :class="msg.role"
      >
        <div class="message-content">{{ msg.content }}</div>
      </div>

      <!-- 中间栏对话区：生成中时使用打字机效果展示当前 AI 回复 -->
      <div
        v-if="isGenerating && currentContent"
        class="chat-message assistant typing"
      >
        <p class="message-content">
          {{ currentContent }}
          <span class="typing-cursor">|</span>
        </p>
      </div>
    </div>
    
    <div class="chat-input-area">
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
        <el-button
          type="primary"
          :disabled="!inputText.trim() || isGenerating"
          @click="handleSubmit"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import type { MPAgentInfo } from "@/api/modules/miniprogram";
import { useIPCreationStore } from "@/stores/modules/ipCreation";

interface Props {
  agent: MPAgentInfo;
  conversationHistory: Array<{ role: "user" | "assistant"; content: string }>;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  submit: [content: string];
  "update:conversation": [messages: Array<{ role: "user" | "assistant"; content: string }>];
}>();

const ipCreationStore = useIPCreationStore();

const inputText = ref("");
const messagesRef = ref<HTMLElement>();
const isGenerating = computed(() => ipCreationStore.isGenerating);
const currentContent = computed(() => ipCreationStore.currentContent);

const messages = computed(() => props.conversationHistory);

// 自动滚动到底部
watch(
  () => messages.value.length,
  () => {
    nextTick(() => {
      if (messagesRef.value) {
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
  background: var(--ip-os-bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--ip-os-border-primary);
  @extend .ip-os-scrollbar;
  
  .chat-message {
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .message-content {
      padding: 12px 16px;
      border-radius: 8px;
      max-width: 80%;
      word-wrap: break-word;
      line-height: 1.6;
    }
    
    &.user {
      display: flex;
      justify-content: flex-end;
      
      .message-content {
        background: var(--ip-os-accent-primary);
        color: #ffffff;
      }
    }
    
    &.assistant {
      display: flex;
      justify-content: flex-start;
      
      .message-content {
        background: var(--ip-os-bg-primary);
        color: var(--ip-os-text-primary);
        border: 1px solid var(--ip-os-border-secondary);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
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
      }
    }
  }
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

.chat-input-area {
  .ip-os-input {
    margin-bottom: 12px;
  }
  
  .chat-input-actions {
    display: flex;
    justify-content: flex-end;
  }
}
</style>

