<template>
    <div class="agent-playground">
      <!-- 头部工具栏 -->
      <div class="playground-header">
        <div class="header-left">
          <el-button :icon="ArrowLeft" @click="handleBack">返回</el-button>
          <div class="agent-info">
            <el-icon class="agent-icon">
              <component :is="getIconComponent(agentInfo.icon)" />
            </el-icon>
            <span class="agent-name">{{ agentInfo.name }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-button type="primary" :icon="Document" @click="handleSaveConfig">保存配置</el-button>
        </div>
      </div>
  
      <!-- 左右分屏布局 -->
      <div class="playground-content">
        <!-- 左侧配置面板 -->
        <div class="config-panel" :style="{ width: leftPanelWidth + 'px' }">
          <div class="panel-header">
            <span class="panel-title">配置面板</span>
            <el-button text :icon="Close" @click="collapseLeftPanel" />
          </div>
          <div v-if="!leftPanelCollapsed" class="panel-body">
            <ConfigPanel
              ref="configPanelRef"
              :agent-config="agentConfig"
              :model-list="modelList"
              @config-change="handleConfigChange"
            />
          </div>
        </div>
  
        <!-- 分割线 -->
        <div
          v-if="!leftPanelCollapsed"
          class="resize-handle"
          @mousedown="startResize"
        ></div>
  
        <!-- 右侧聊天面板 -->
        <div class="chat-panel" :style="{ width: `calc(100% - ${leftPanelCollapsed ? 0 : leftPanelWidth + 10}px)` }">
          <ChatPanel
            ref="chatPanelRef"
            :agent-config="agentConfig"
            :system-prompt="agentConfig.systemPrompt"
            @save-config="handleSaveConfig"
          />
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts" name="AgentPlayground">
  import { ref, reactive, onMounted, onUnmounted } from "vue";
  import { useRoute, useRouter } from "vue-router";
  import { ElMessage, ElMessageBox } from "element-plus";
  import { ArrowLeft, Document, Close, ChatDotRound } from "@element-plus/icons-vue";
  import ConfigPanel from "./ConfigPanel.vue";
  import ChatPanel from "./ChatPanel.vue";
  import { getAgentDetail, updateAgent, getAvailableModels } from "@/api/modules/agent";
  import type { Agent } from "@/api/interface";
  
  interface AgentInfo {
    id: string;
    name: string;
    icon: string;
  }
  
  const route = useRoute();
  const router = useRouter();
  
  // 智能体基本信息
  const agentInfo = ref<AgentInfo>({
    id: "",
    name: "",
    icon: ""
  });
  
  // 保存原始agent数据（用于保存配置时）
  const originalAgentData = ref<Partial<Agent.ResAgentItem>>({});
  
  // 智能体配置
  const agentConfig = reactive<{
    systemPrompt: string;
    model: string;
    temperature: number;
    maxTokens: number;
    topP: number;
    frequencyPenalty: number;
    presencePenalty: number;
    contextMessages: Array<{ role: "user" | "assistant"; content: string }>;
  }>({
    systemPrompt: "",
    model: "",
    temperature: 0.7,
    maxTokens: 2000,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0,
    contextMessages: []
  });
  
  // 模型列表
  const modelList = ref<Array<{ id: string; name: string; maxTokens: number }>>([]);
  
  // 左侧面板宽度
  const leftPanelWidth = ref(800);
  const leftPanelCollapsed = ref(false);
  
  // 组件引用
  const configPanelRef = ref<InstanceType<typeof ConfigPanel>>();
  const chatPanelRef = ref<InstanceType<typeof ChatPanel>>();
  
  // 获取图标组件
  const getIconComponent = (iconName: string) => {
    if (!iconName) return ChatDotRound;
    const iconMap: Record<string, any> = {
      viral_copy_default: Document,       // 文案类（已更换为 Document 图标）
      script_default: ChatDotRound,
      marketing_default: ChatDotRound,
      ChatDotRound
    };
    return iconMap[iconName] || ChatDotRound;
  };
  
  // 加载智能体详情
  const loadAgentDetail = async () => {
    const agentId = route.params.id as string;
    if (!agentId) {
      ElMessage.error("智能体ID不存在");
      router.back();
      return;
    }
  
    try {
      const res = await getAgentDetail(agentId);
      const agent = res.data;
  
      // 保存原始数据
      originalAgentData.value = { ...agent };
  
      agentInfo.value = {
        id: agent.id,
        name: agent.name,
        icon: agent.icon
      };
  
      agentConfig.systemPrompt = agent.systemPrompt;
      agentConfig.model = agent.model;
      agentConfig.temperature = agent.config.temperature;
      agentConfig.maxTokens = agent.config.maxTokens;
      agentConfig.topP = agent.config.topP ?? 1.0;
      agentConfig.frequencyPenalty = agent.config.frequencyPenalty ?? 0.0;
      agentConfig.presencePenalty = agent.config.presencePenalty ?? 0.0;
    } catch (error: unknown) {
      const err = error as { message?: string };
      ElMessage.error(err.message || "加载智能体详情失败");
      router.back();
    }
  };
  
  // 加载模型列表
  const loadModelList = async () => {
    try {
      const res = await getAvailableModels();
      modelList.value = res.data || [];
    } catch (error: unknown) {
      console.error("加载模型列表失败:", error);
    }
  };
  
  // 处理配置变更
  const handleConfigChange = (config: Partial<typeof agentConfig>) => {
    Object.assign(agentConfig, config);
  };
  
  // 保存配置
  const handleSaveConfig = async () => {
    try {
      await ElMessageBox.confirm("确定要保存当前配置吗？", "提示", {
        type: "warning"
      });
  
      const updateData: Agent.ReqAgentForm = {
        id: agentInfo.value.id,
        name: agentInfo.value.name,
        icon: agentInfo.value.icon,
        description: originalAgentData.value.description || "",
        systemPrompt: agentConfig.systemPrompt,
        model: agentConfig.model,
        config: {
          temperature: agentConfig.temperature,
          maxTokens: agentConfig.maxTokens,
          topP: agentConfig.topP,
          frequencyPenalty: agentConfig.frequencyPenalty,
          presencePenalty: agentConfig.presencePenalty
        },
        sortOrder: originalAgentData.value.sortOrder || 0,
        status: originalAgentData.value.status ?? 1
      };
  
      await updateAgent(updateData);
      ElMessage.success("配置保存成功");
    } catch (error: unknown) {
      if (error !== "cancel") {
        const err = error as { message?: string };
        ElMessage.error(err.message || "保存配置失败");
      }
    }
  };
  
  // 返回
  const handleBack = () => {
    router.back();
  };
  
  // 折叠左侧面板
  const collapseLeftPanel = () => {
    leftPanelCollapsed.value = !leftPanelCollapsed.value;
  };
  
  // 调整面板宽度
  let isResizing = false;
  const startResize = (e: MouseEvent) => {
    isResizing = true;
    document.addEventListener("mousemove", handleResize);
    document.addEventListener("mouseup", stopResize);
    e.preventDefault();
  };
  
  const handleResize = (e: MouseEvent) => {
    if (!isResizing) return;
    const newWidth = e.clientX;
    if (newWidth >= 300 && newWidth <= 800) {
      leftPanelWidth.value = newWidth;
    }
  };
  
  const stopResize = () => {
    isResizing = false;
    document.removeEventListener("mousemove", handleResize);
    document.removeEventListener("mouseup", stopResize);
  };
  
  onMounted(() => {
    loadAgentDetail();
    loadModelList();
  });
  
  onUnmounted(() => {
    document.removeEventListener("mousemove", handleResize);
    document.removeEventListener("mouseup", stopResize);
  });
  </script>
  
  <style scoped lang="scss">
  .agent-playground {
    height: calc(100vh - 150px);
    display: flex;
    flex-direction: column;
    background-color: var(--el-bg-color-page);
  
    .playground-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      background-color: var(--el-bg-color);
      border-bottom: 1px solid var(--el-border-color-lighter);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
      .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
  
        .agent-info {
          display: flex;
          align-items: center;
          gap: 12px;
  
          .agent-icon {
            font-size: 24px;
            color: var(--el-color-primary);
          }
  
          .agent-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }
        }
      }
    }
  
    .playground-content {
      flex: 1;
      display: flex;
      overflow: hidden;
      position: relative;
  
      .config-panel {
        height: 100%;
        background-color: var(--el-bg-color);
        border-right: 1px solid var(--el-border-color-lighter);
        display: flex;
        flex-direction: column;
        transition: width 0.3s ease;
  
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid var(--el-border-color-lighter);
          background-color: var(--el-fill-color-light);
  
          .panel-title {
            font-weight: 600;
            color: var(--el-text-color-primary);
          }
        }
  
        .panel-body {
          flex: 1;
          overflow-y: auto;
        }
      }
  
      .resize-handle {
        width: 4px;
        height: 100%;
        background-color: var(--el-border-color);
        cursor: col-resize;
        position: relative;
        transition: background-color 0.2s;
  
        &:hover {
          background-color: var(--el-color-primary);
        }
  
        &::after {
          content: "";
          position: absolute;
          left: -2px;
          top: 0;
          width: 8px;
          height: 100%;
        }
      }
  
      .chat-panel {
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: width 0.3s ease;
      }
    }
  }
  </style>