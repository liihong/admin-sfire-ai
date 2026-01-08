<template>
  <div class="workspace-cockpit">
    <!-- 顶部工具栏：右上角模型切换 -->
    <div class="cockpit-header">
      <div class="header-right">
        <el-dropdown @command="handleModelChange">
          <span class="model-switcher">
            <span class="model-icon">{{ currentModel.icon }}</span>
            <span class="model-name">{{ currentModel.name }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="model in availableModels"
                :key="model.type"
                :command="model.type"
                :disabled="!model.available"
              >
                <span class="dropdown-item-icon">{{ model.icon }}</span>
                <span class="dropdown-item-name">{{ model.name }}</span>
                <span class="dropdown-item-desc">{{ model.description }}</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="cockpit-container">
      <!-- 左侧栏：IP DNA + 会话历史（类似其他对话模型） -->
      <div class="cockpit-sidebar">
        <IPDNAPanel />
        <div class="sidebar-conversation">
          <ConversationHistory
            @select="handleConversationSelect"
            @create="handleConversationCreate"
          />
        </div>
      </div>
      
      <!-- 中间栏：创作反应堆 -->
      <div class="cockpit-main">
        <CreationReactor
          :selected-agent="selectedAgent"
          @generate="handleGenerate"
        />
      </div>
      
      <!-- 右侧栏：产出与精炼平台 -->
      <div class="cockpit-output">
        <RefineryDeck />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="WorkspaceCockpit">
import { computed, onMounted, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import IPDNAPanel from "@/components/Workspace/IPDNAPanel.vue";
import CreationReactor from "@/components/Workspace/CreationReactor.vue";
import RefineryDeck from "@/components/Workspace/RefineryDeck.vue";
import ConversationHistory from "@/components/ConversationHistory/index.vue";
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { getMPProjectApi } from "@/api/modules/miniprogram";
import { useMPSettingsStore } from "@/stores/modules/mpSettings";
import {
  generateMPContentApi,
  type MPChatMessage,
  type MPChatRequest
} from "@/api/modules/miniprogram";

const route = useRoute();
const router = useRouter();
const ipCreationStore = useIPCreationStore();
const mpSettingsStore = useMPSettingsStore();

const selectedAgent = computed(() => ipCreationStore.selectedAgent);
const activeProject = computed(() => ipCreationStore.activeProject);

// 当前模型与可用模型列表（与小程序端保持一致）
const currentModel = computed(() => mpSettingsStore.currentModel);
const availableModels = computed(() => mpSettingsStore.availableModels);

// 加载项目信息
const loadProject = async () => {
  const projectId = route.params.projectId;
  if (!projectId) {
    ElMessage.error("项目ID不存在");
    router.push("/mp/home");
    return;
  }

  try {
    const numericProjectId = Number(projectId);
    const response = await getMPProjectApi(numericProjectId);
    // HTTP 拦截器返回的 response 直接就是 {success: true, project: {...}}
    // 所以直接访问 response.project 或 response.data.project（如果被包装）
    const project = (response as any)?.project || (response as any)?.data?.project;
    if (project) {
      ipCreationStore.setActiveProject(project);
    } else {
      ElMessage.error("项目不存在");
      router.push("/mp/home");
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载项目失败");
    router.push("/mp/home");
  }
};

// 生成内容
const handleGenerate = async (
  prompt: string,
  messages: Array<{ role: "user" | "assistant"; content: string }>
) => {
  if (!selectedAgent.value || !activeProject.value) {
    ElMessage.warning("请先选择智能体和IP");
    return;
  }

  try {
    ipCreationStore.setGenerating(true);
    ipCreationStore.updateCurrentContent("");

    // 保存当前智能体信息，避免异步回调中引用失效
    const currentAgent = selectedAgent.value;
    if (!currentAgent) {
      ElMessage.warning("请先选择智能体");
      ipCreationStore.setGenerating(false);
      return;
    }

    // 添加用户消息到对话历史（在发送请求前）
    ipCreationStore.addMessage("user", prompt);
    
    // 构建包含新用户消息的消息列表
    const messagesWithNewUser = [...messages, { role: "user" as const, content: prompt }];

    // 构建请求
    const request: MPChatRequest = {
      conversation_id: ipCreationStore.currentConversationId || undefined,
      project_id: Number(activeProject.value.id),
      agent_type: currentAgent.type,
      messages: messagesWithNewUser as MPChatMessage[],
      // 使用当前选择的模型类型，默认与小程序保持一致
      model_type: mpSettingsStore.modelType,
      stream: true
    };

    // 调用流式生成API
    await generateMPContentApi(
      request,
      // onChunk
      (chunk: string) => {
        ipCreationStore.updateCurrentContent(ipCreationStore.currentContent + chunk);
      },
      // onError
      (error: string) => {
        ElMessage.error(error);
        ipCreationStore.setGenerating(false);
      },
      // onDone
      () => {
        // 生成完成，保存版本
        ipCreationStore.addContentVersion(
          ipCreationStore.currentContent,
          currentAgent.id,
          currentAgent.name
        );
        ipCreationStore.addMessage("assistant", ipCreationStore.currentContent);
        ipCreationStore.setGenerating(false);
      },
      // onConversationId
      (conversationId: number) => {
        // 更新当前会话ID（如果后端创建了新会话）
        if (!ipCreationStore.currentConversationId) {
          ipCreationStore.setCurrentConversationId(conversationId);
        }
      }
    );
  } catch (error: any) {
    ElMessage.error(error?.msg || "生成失败");
    ipCreationStore.setGenerating(false);
  }
};

// 切换大模型
const handleModelChange = (command: string) => {
  // 使用小程序同款模型配置，仅支持列表中已启用的模型
  mpSettingsStore.setModelType(command as any);
  ElMessage.success(`已切换到模型：${currentModel.value.name}`);
};

// 选择会话
const handleConversationSelect = async (conversation: any) => {
  // 加载会话详情并恢复对话历史
  try {
    const { getMPConversationDetailApi } = await import("@/api/modules/miniprogram");
    const response = await getMPConversationDetailApi(conversation.id);

    // 统一处理 code 类型（可能是字符串或数字）
    const code = String(response.code);
    if (code === "200" && response.data) {
      const detail: any = response.data;

      // 更新当前会话ID
      ipCreationStore.setCurrentConversationId(conversation.id);

      // 恢复对话历史
      const history = (detail.messages || []).map((msg: any) => ({
        role: msg.role,
        content: msg.content
      }));

      // 清空当前内容和生成状态
      ipCreationStore.setGenerating(false);
      ipCreationStore.updateCurrentContent("");

      // 设置对话历史（会在中间对话框中展示）
      ipCreationStore.conversationHistory = history;

      // 如果有最后一条assistant消息，同时设置为右侧当前内容
      const lastAssistantMsg = history.filter((m: any) => m.role === "assistant").pop();
      if (lastAssistantMsg) {
        ipCreationStore.updateCurrentContent(lastAssistantMsg.content);
      }

      ElMessage.success(`已切换到会话：${conversation.title}`);
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载会话详情失败");
  }
};

// 创建新会话
const handleConversationCreate = () => {
  // 清空当前对话历史
  ipCreationStore.clearConversation();
  ipCreationStore.updateCurrentContent("");
};

// 防止重复加载的标记
let isLoading = false;

// 监听路由参数变化，当参数准备好时自动加载
watch(
  () => route.params.projectId,
  (newProjectId, oldProjectId) => {
    if (newProjectId && newProjectId !== oldProjectId && !isLoading) {
      isLoading = true;
      loadProject().finally(() => {
        isLoading = false;
      });
    }
  },
  { immediate: true } // 立即执行，确保路由参数准备好时能加载
);

onMounted(async () => {
  // 使用 nextTick 确保路由参数已经准备好
  await nextTick();
  // 如果 watch 没有触发（参数还未准备好），再次尝试加载
  if (route.params.projectId && !ipCreationStore.activeProject && !isLoading) {
    isLoading = true;
    loadProject().finally(() => {
      isLoading = false;
    });
  }
});
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.workspace-cockpit {
  width: 100%;
  height: 100vh;
  background: var(--ip-os-bg-primary);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cockpit-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 12px 24px;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-switcher {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--ip-os-bg-secondary);
  border: 1px solid var(--ip-os-border-secondary);
  cursor: pointer;
  font-size: 13px;
  color: var(--ip-os-text-primary);
  transition: all 0.2s ease;

  &:hover {
    background: var(--ip-os-bg-tertiary);
    border-color: var(--ip-os-accent-primary);
  }

  .model-icon {
    font-size: 16px;
  }

  .model-name {
    font-weight: 500;
  }
}

.dropdown-item-icon {
  margin-right: 6px;
}

.dropdown-item-name {
  font-weight: 500;
  margin-right: 4px;
}

.dropdown-item-desc {
  font-size: 12px;
  color: var(--ip-os-text-secondary);
}

.cockpit-container {
  display: flex;
  width: 100%;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.cockpit-sidebar {
  width: 20%;
  min-width: 280px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  // IP DNA 面板固定高度
  :deep(.ip-dna-panel) {
    flex-shrink: 0;
  }
}

.sidebar-conversation {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  
  :deep(.conversation-history) {
    height: 100%;
    border-right: 1px solid var(--ip-os-border-primary);
  }
}

.cockpit-main {
  width: 50%;
  height: 100%;
  overflow: hidden;
  border-left: 1px solid var(--ip-os-border-primary);
  border-right: 1px solid var(--ip-os-border-primary);
}

.cockpit-output {
  width: 30%;
  min-width: 320px;
  height: 100%;
  overflow: hidden;
}

@media (max-width: 1200px) {
  .cockpit-container {
    flex-direction: column;
  }
  
  .cockpit-sidebar,
  .cockpit-main,
  .cockpit-output {
    width: 100%;
    height: auto;
    min-height: 300px;
  }
}
</style>

