<template>
  <div class="agent-arsenal">
    <div class="arsenal-header">
      <h3 class="arsenal-title">智能体军械库</h3>
    </div>
    
    <div v-if="loading" class="arsenal-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
    </div>
    
    <div v-else-if="agents.length === 0" class="arsenal-empty">
      <p>暂无可用智能体</p>
    </div>
    
    <div v-else class="arsenal-list">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="arsenal-item"
        :class="{ 'is-active': selectedAgent?.id === agent.id }"
        @click="handleSelectAgent(agent)"
      >
        <div class="arsenal-item-icon">
          <span v-if="agent.icon" class="icon-emoji">{{ agent.icon }}</span>
          <el-icon v-else :size="24"><Tools /></el-icon>
        </div>
        <div class="arsenal-item-content">
          <div class="arsenal-item-name">{{ agent.name }}</div>
          <div class="arsenal-item-desc">{{ agent.description }}</div>
        </div>
        <div v-if="selectedAgent?.id === agent.id" class="arsenal-item-active">
          <el-icon><Check /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Loading, Tools, Check } from "@element-plus/icons-vue";
import { getMPAgentsApi, type MPAgentInfo } from "@/api/modules/miniprogram";
import { ElMessage } from "element-plus";

interface Props {
  selectedAgent: MPAgentInfo | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  "update:selectedAgent": [agent: MPAgentInfo | null];
  "select": [agent: MPAgentInfo];
}>();

const loading = ref(false);
const agents = ref<MPAgentInfo[]>([]);

// 获取智能体列表
const fetchAgents = async () => {
  // #region agent log
  fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'AgentArsenal.vue:fetchAgents',message:'fetch start',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run-agents',hypothesisId:'H1'})}).catch(()=>{});
  // #endregion
  loading.value = true;
  try {
    const resp = await getMPAgentsApi();
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'AgentArsenal.vue:fetchAgents',message:'fetch response',data:{code:resp.code,hasData:!!resp.data,hasAgents:!!resp.data?.agents,agentsCount:resp.data?.agents?.length ?? null},timestamp:Date.now(),sessionId:'debug-session',runId:'run-agents',hypothesisId:'H2'})}).catch(()=>{});
    // #endregion
    // 统一响应格式：{code, data: {agents: []}, msg}
    const code = String(resp.code);
    if (code === "200" && resp.data?.agents) {
      agents.value = resp.data.agents;
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'AgentArsenal.vue:fetchAgents',message:'set agents',data:{count:agents.value.length,first:agents.value[0] ?? null},timestamp:Date.now(),sessionId:'debug-session',runId:'run-agents',hypothesisId:'H3'})}).catch(()=>{});
      // #endregion
      // 如果当前还没有选中的智能体，则默认选中第一个，进入页面即可开始创作
      if (!props.selectedAgent && agents.value.length > 0) {
        handleSelectAgent(agents.value[0]);
      }
    } else {
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'AgentArsenal.vue:fetchAgents',message:'no agents in response',data:{code:resp.code,msg:resp.msg},timestamp:Date.now(),sessionId:'debug-session',runId:'run-agents',hypothesisId:'H4'})}).catch(()=>{});
      // #endregion
    }
  } catch (error: any) {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'AgentArsenal.vue:fetchAgents',message:'fetch error',data:{errorMessage:error?.msg,errorString:String(error)},timestamp:Date.now(),sessionId:'debug-session',runId:'run-agents',hypothesisId:'H5'})}).catch(()=>{});
    // #endregion
    ElMessage.error(error?.msg || "获取智能体列表失败");
  } finally {
    loading.value = false;
  }
};

// 选择智能体
const handleSelectAgent = (agent: MPAgentInfo) => {
  emit("update:selectedAgent", agent);
  emit("select", agent);
};

onMounted(() => {
  // #region agent log
  fetch('http://127.0.0.1:7243/ingest/53b38dcf-6225-4ab9-a06a-816278989907',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'AgentArsenal.vue:onMounted',message:'mounted',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run-agents',hypothesisId:'H1'})}).catch(()=>{});
  // #endregion
  fetchAgents();
});
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.agent-arsenal {
  margin-top: 24px;
}

.arsenal-header {
  margin-bottom: 16px;
  
  .arsenal-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--ip-os-text-primary);
    margin: 0;
  }
}

.arsenal-loading,
.arsenal-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: var(--ip-os-text-secondary);
  font-size: 14px;
}

.arsenal-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.arsenal-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--ip-os-bg-secondary);
  border: 1px solid var(--ip-os-border-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--ip-os-accent-primary);
    background: var(--ip-os-bg-tertiary);
    transform: translateX(4px);
  }
  
  &.is-active {
    border-color: var(--ip-os-accent-primary);
    background: rgba(255, 107, 53, 0.08);
    box-shadow: 0 2px 8px rgba(255, 107, 53, 0.15);
  }
  
  .arsenal-item-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--ip-os-bg-primary);
    border-radius: 8px;
    color: var(--ip-os-accent-primary);
    
    .icon-emoji {
      font-size: 24px;
      line-height: 1;
    }
  }
  
  .arsenal-item-content {
    flex: 1;
    min-width: 0;
    
    .arsenal-item-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--ip-os-text-primary);
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .arsenal-item-desc {
      font-size: 12px;
      color: var(--ip-os-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
  }
  
  .arsenal-item-active {
    flex-shrink: 0;
    color: var(--ip-os-accent-primary);
  }
}
</style>

