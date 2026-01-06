<template>
  <div class="creation-reactor">
    <div class="reactor-header">
      <h3 class="reactor-title">{{ selectedAgent?.name || "选择智能体开始创作" }}</h3>
      <p v-if="selectedAgent" class="reactor-subtitle">{{ selectedAgent.description }}</p>
    </div>
    
    <div class="reactor-canvas">
      <!-- 动态输入界面 -->
      <component
        :is="currentInputComponent"
        v-if="selectedAgent"
        ref="inputComponentRef"
        :agent="selectedAgent"
        :conversation-history="conversationHistory"
        @submit="handleSubmit"
        @update:conversation="handleConversationUpdate"
      />
      
      <div v-else class="reactor-empty">
        <el-icon :size="64"><Tools /></el-icon>
        <p>请从左侧选择智能体</p>
      </div>
    </div>
    
    <!-- 点火按钮 -->
    <div class="reactor-footer" v-if="selectedAgent">
      <button
        class="ip-os-button-primary reactor-ignite-btn"
        :disabled="isGenerating || !canSubmit"
        @click="handleIgnite"
      >
        <span v-if="!isGenerating">生成 / 点火</span>
        <span v-else>生成中...</span>
        <el-icon v-if="!isGenerating"><Promotion /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { Tools, Promotion } from "@element-plus/icons-vue";
import ChatInput from "./inputs/ChatInput.vue";
import FormInput from "./inputs/FormInput.vue";
import type { MPAgentInfo } from "@/api/modules/miniprogram";
import { useIPCreationStore } from "@/stores/modules/ipCreation";

interface Props {
  selectedAgent: MPAgentInfo | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  generate: [prompt: string, messages: Array<{ role: "user" | "assistant"; content: string }>];
}>();

const ipCreationStore = useIPCreationStore();

const conversationHistory = computed(() => ipCreationStore.conversationHistory);
const isGenerating = computed(() => ipCreationStore.isGenerating);
const canSubmit = ref(true);

// 根据智能体类型选择输入组件
const currentInputComponent = computed(() => {
  if (!props.selectedAgent) return null;
  
  // 这里可以根据智能体的 type 或 description 来判断使用哪种输入方式
  // 暂时默认使用聊天输入，后续可以根据实际需求扩展
  const agentType = props.selectedAgent.type?.toLowerCase() || "";
  
  // 如果智能体类型包含 "form" 或 "structured"，使用表单输入
  if (agentType.includes("form") || agentType.includes("structured")) {
    return FormInput;
  }
  
  // 默认使用聊天输入
  return ChatInput;
});

const inputComponentRef = ref<InstanceType<typeof ChatInput> | InstanceType<typeof FormInput>>();

const handleSubmit = (content: string) => {
  if (!content.trim() || isGenerating.value) return;
  
  // 添加用户消息到对话历史
  ipCreationStore.addMessage("user", content);
  
  emit("generate", content, [...conversationHistory.value, { role: "user", content }]);
};

const handleConversationUpdate = (messages: Array<{ role: "user" | "assistant"; content: string }>) => {
  // 更新对话历史
  ipCreationStore.conversationHistory = messages;
};

const handleIgnite = async () => {
  if (isGenerating.value) return;
  
  // 如果是表单输入，获取表单数据
  if (inputComponentRef.value && "getPrompt" in inputComponentRef.value) {
    const formInput = inputComponentRef.value as InstanceType<typeof FormInput>;
    if (formInput.validate && !formInput.validate()) {
      ElMessage.warning("请填写必填项");
      return;
    }
    const prompt = formInput.getPrompt();
    if (prompt) {
      handleSubmit(prompt);
    }
  } else {
    // 聊天输入，聚焦输入框
    const inputElement = document.querySelector(".reactor-canvas textarea");
    if (inputElement) {
      (inputElement as HTMLElement).focus();
    }
  }
};
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.creation-reactor {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: var(--ip-os-bg-secondary);
}

.reactor-header {
  margin-bottom: 24px;
  
  .reactor-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--ip-os-text-primary);
    margin: 0 0 8px;
  }
  
  .reactor-subtitle {
    font-size: 14px;
    color: var(--ip-os-text-secondary);
    margin: 0;
  }
}

.reactor-canvas {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.reactor-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--ip-os-text-secondary);
  
  .el-icon {
    margin-bottom: 16px;
    color: var(--ip-os-accent-primary);
  }
  
  p {
    font-size: 16px;
    margin: 0;
  }
}

.reactor-footer {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.reactor-ignite-btn {
  min-width: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  padding: 14px 32px;
}
</style>

