<template>
  <!-- 触发按钮 -->
  <div class="agent-selector-trigger" @click="openDialog">
    <div class="selected-agent" v-if="selectedAgent">
      <AgentIcon :icon="selectedAgent.icon" :size="24" />
      <span class="agent-name">{{ selectedAgent.name }}</span>
    </div>
    <div class="no-agent" v-else>
      <el-icon><Tools /></el-icon>
      <span>选择智能体</span>
    </div>
    <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
  </div>

  <!-- Dialog 对话框 -->
  <el-dialog
    v-model="visible"
    title="智能体军械库"
    width="480px"
    :close-on-click-modal="false"
    class="agent-selector-dialog"
  >
    <!-- 加载状态 -->
    <div v-if="loading" class="dialog-loading">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="agents.length === 0" class="dialog-empty">
      <el-icon :size="48"><Tools /></el-icon>
      <p>暂无可用智能体</p>
    </div>

    <!-- 智能体列表 -->
    <div v-else class="dialog-list">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="dialog-item"
        :class="{ 'is-active': tempSelectedAgent?.id === agent.id }"
        @click="handleSelect(agent)"
      >
        <div class="item-icon">
          <AgentIcon :icon="agent.icon" :size="30" />
        </div>
        <div class="item-content">
          <div class="item-name">{{ agent.name }}</div>
          <div class="item-desc">{{ agent.description }}</div>
        </div>
        <div v-if="tempSelectedAgent?.id === agent.id" class="item-check">
          <el-icon><Check /></el-icon>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="confirmSelection" :disabled="!tempSelectedAgent">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Loading, Tools, Check, ArrowDown } from "@element-plus/icons-vue";
import { getMPAgentsApi, type MPAgentInfo } from "@/api/modules/miniprogram";
import { ElMessage } from "element-plus";
import AgentIcon from "@/components/AgentIcon/index.vue";

interface Props {
  selectedAgent: MPAgentInfo | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  "update:selectedAgent": [agent: MPAgentInfo | null];
  select: [agent: MPAgentInfo];
}>();

const visible = ref(false);
const loading = ref(false);
const agents = ref<MPAgentInfo[]>([]);
const tempSelectedAgent = ref<MPAgentInfo | null>(null);

// 打开对话框
const openDialog = () => {
  tempSelectedAgent.value = props.selectedAgent;
  visible.value = true;
};

// 关闭对话框
const closeDialog = () => {
  visible.value = false;
  tempSelectedAgent.value = null;
};

// 获取智能体列表
const fetchAgents = async () => {
  loading.value = true;
  try {
    const resp = await getMPAgentsApi();
    // 统一响应格式：{code, data: {agents: []}, msg}
    const code = String(resp.code);
    if (code === "200" && resp.data?.agents) {
      agents.value = resp.data.agents;
      // 如果当前还没有选中的智能体，默认选中第一个
      if (!props.selectedAgent && agents.value.length > 0) {
        emit("update:selectedAgent", agents.value[0]);
        emit("select", agents.value[0]);
      }
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "获取智能体列表失败");
  } finally {
    loading.value = false;
  }
};

// 选择智能体（仅临时选中，不立即触发）
const handleSelect = (agent: MPAgentInfo) => {
  tempSelectedAgent.value = agent;
};

// 确认选择
const confirmSelection = () => {
  if (tempSelectedAgent.value) {
    emit("update:selectedAgent", tempSelectedAgent.value);
    emit("select", tempSelectedAgent.value);
  }
  closeDialog();
};

onMounted(() => {
  fetchAgents();
});
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.agent-selector-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  background: var(--ip-os-bg-tertiary);
  border: 1px solid var(--ip-os-border-secondary);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--ip-os-bg-secondary);
    border-color: var(--ip-os-accent-primary);
  }

  .selected-agent {
    display: flex;
    align-items: center;
    gap: 6px;

    .agent-name {
      font-size: 14px;
      font-weight: 500;
      color: var(--ip-os-text-primary);
      max-width: 120px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .no-agent {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    color: var(--ip-os-text-secondary);
  }

  .dropdown-arrow {
    color: var(--ip-os-text-secondary);
    transition: transform 0.2s;
  }
}

.dialog-loading,
.dialog-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 0;
  color: var(--ip-os-text-secondary);
  font-size: 14px;
  gap: 12px;
}

.dialog-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow-y: auto;
  @extend .ip-os-scrollbar;
}

.dialog-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--ip-os-bg-secondary);
  border: 1px solid var(--ip-os-border-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--ip-os-accent-primary);
    background: var(--ip-os-bg-tertiary);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  &.is-active {
    border-color: var(--ip-os-accent-primary);
    background: rgba(255, 107, 53, 0.08);
  }

  .item-icon {
    flex-shrink: 0;
    padding: 10px;
  }

  .item-content {
    flex: 1;
    min-width: 0;

    .item-name {
      font-size: 15px;
      font-weight: 600;
      color: var(--ip-os-text-primary);
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .item-desc {
      font-size: 13px;
      color: var(--ip-os-text-secondary);
      line-height: 1.4;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      line-clamp: 2;
      -webkit-box-orient: vertical;
    }
  }

  .item-check {
    flex-shrink: 0;
    color: var(--ip-os-accent-primary);
    font-size: 18px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

<style lang="scss">
// 全局样式覆盖对话框
.agent-selector-dialog {
  .el-dialog__header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--ip-os-border-secondary);

    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
      color: var(--ip-os-text-primary);
    }
  }

  .el-dialog__body {
    padding: 24px;
  }

  .el-dialog__footer {
    padding: 16px 24px;
    border-top: 1px solid var(--ip-os-border-secondary);
  }
}
</style>

