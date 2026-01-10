<template>
  <div class="workspace-cockpit">
    <!-- 顶部工具栏：左侧返回按钮 -->
    <div class="cockpit-header">
      <div class="header-left">
        <el-button class="back-btn" @click="handleBack" text>
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </el-button>
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
import { ArrowLeft } from "@element-plus/icons-vue";
import IPDNAPanel from "@/components/Workspace/IPDNAPanel.vue";
import CreationReactor from "@/components/Workspace/CreationReactor.vue";
import RefineryDeck from "@/components/Workspace/RefineryDeck.vue";
import ConversationHistory from "@/components/ConversationHistory/index.vue";
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { getMPProjectApi } from "@/api/modules/miniprogram";
import {
  generateMPContentApi,
  type MPChatMessage,
  type MPChatRequest
} from "@/api/modules/miniprogram";

const route = useRoute();
const router = useRouter();
const ipCreationStore = useIPCreationStore();

const selectedAgent = computed(() => ipCreationStore.selectedAgent);
const activeProject = computed(() => ipCreationStore.activeProject);

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
    // 统一响应格式：{code, data, msg}
    const code = String(response.code);
    if (code === "200" && response.data) {
      const project = response.data;
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'workspace/index.vue:loadProject',message:'setting activeProject',data:{projectId:project.id,currentActiveId:ipCreationStore.activeProject?.id},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'H2'})}).catch(()=>{});
      // #endregion
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

// 返回上一页
const handleBack = () => {
  router.back();
};

// 选择会话
const handleConversationSelect = async (conversation: any) => {
  // 加载会话详情并恢复对话历史
  try {
    const { getMPConversationDetailApi } = await import("@/api/modules/miniprogram");
    const response = await getMPConversationDetailApi(conversation.id);
    
    // 将 response.code 转换为字符串进行比较，与其他地方保持一致
    const code = String(response.code);
    if (code === "200" && response.data) {
      const detail: any = response.data;
      // 恢复对话历史
      const history = (detail.messages || []).map((msg: any) => ({
        role: msg.role,
        content: msg.content
      }));
      ipCreationStore.conversationHistory = history;
      
      // 如果有最后一条assistant消息，设置为当前内容
      const lastAssistantMsg = history.filter((m: any) => m.role === "assistant").pop();
      if (lastAssistantMsg) {
        ipCreationStore.updateCurrentContent(lastAssistantMsg.content);
      }
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载会话详情失败");
  }
};

// 创建新会话
// 注意：这里只是打开对话框并显示欢迎语，真正的会话会在用户发送第一条消息时创建
const handleConversationCreate = () => {
  // 清空当前对话历史
  ipCreationStore.clearConversation();
  ipCreationStore.updateCurrentContent("");
  
  // 生成 AI 欢迎语
  const agentName = selectedAgent.value?.name || "AI助手";
  const welcomeMessage = `你好！我是${agentName}，很高兴为你服务。请告诉我你想创作什么内容吧~`;
  
  // 添加欢迎语到对话历史
  ipCreationStore.addMessage("assistant", welcomeMessage);
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
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--ip-os-text-primary);
  transition: all 0.2s ease;

  &:hover {
    background: var(--ip-os-bg-tertiary);
    color: var(--ip-os-accent-primary);
  }

  .el-icon {
    font-size: 16px;
  }
}

.cockpit-container {
  display: flex;
  width: 100%;
  flex: 1; // 使用 flex 占据剩余空间，自动减去 header 高度
  min-height: 0; // 防止 flex 子元素溢出
}

.cockpit-sidebar {
  width: 20%;
  min-width: 280px;
  height: 100%; // 在 flex 容器中，100% 会正确计算
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

