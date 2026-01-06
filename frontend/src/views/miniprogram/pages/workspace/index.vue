<template>
  <div class="workspace-cockpit">
    <div class="cockpit-container">
      <!-- 左侧栏：IP DNA + 智能体军械库 -->
      <div class="cockpit-sidebar">
        <IPDNAPanel />
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

    // 构建请求
    const request: MPChatRequest = {
      project_id: Number(activeProject.value.id),
      agent_type: currentAgent.type,
      messages: messages as MPChatMessage[],
      model_type: "deepseek",
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
      }
    );
  } catch (error: any) {
    ElMessage.error(error?.msg || "生成失败");
    ipCreationStore.setGenerating(false);
  }
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
}

.cockpit-container {
  display: flex;
  width: 100%;
  height: 100%;
}

.cockpit-sidebar {
  width: 20%;
  min-width: 280px;
  height: 100%;
  overflow-y: auto;
  @extend .ip-os-scrollbar;
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

