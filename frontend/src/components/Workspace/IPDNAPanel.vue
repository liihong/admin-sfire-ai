<template>
  <div class="ip-dna-panel">
    <!-- IP 图腾 -->
    <div class="dna-totem">
      <el-avatar :size="80" :src="projectAvatar" class="dna-avatar">
        <el-icon :size="40"><UserFilled /></el-icon>
      </el-avatar>
      <h3 class="dna-name">{{ project?.name || "未选择 IP" }}</h3>
      <p class="dna-position">{{ projectPosition }}</p>
    </div>
    
    <!-- 动态能量条 -->
    <PowerGauge :power="computePower" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { UserFilled } from "@element-plus/icons-vue";
import PowerGauge from "./PowerGauge.vue";
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";

const ipCreationStore = useIPCreationStore();
const mpUserStore = useMPUserStore();

const project = computed(() => ipCreationStore.activeProject);
const computePower = computed(() => mpUserStore.computePower);

const projectAvatar = computed(() => {
  // 可以从项目信息中获取头像，这里暂时返回空
  return "";
});

const projectPosition = computed(() => {
  if (!project.value) return "请选择 IP";
  const parts = [];
  if (project.value.industry) parts.push(project.value.industry);
  if (project.value.tone) parts.push(project.value.tone);
  return parts.join(" · ") || "IP 定位";
});
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.ip-dna-panel {
  // 移除 height: 100%，让面板只占据所需的空间
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: var(--ip-os-bg-secondary);
  border-right: 1px solid var(--ip-os-border-primary);
  flex-shrink: 0; // 不被压缩
}

.dna-totem {
  text-align: center;
  margin-bottom: 24px;
  
  .dna-avatar {
    margin-bottom: 16px;
    border: 2px solid var(--ip-os-accent-primary);
    box-shadow: 0 2px 12px rgba(255, 107, 53, 0.2);
  }
  
  .dna-name {
    font-size: 20px;
    font-weight: 700;
    color: var(--ip-os-text-primary);
    margin: 0 0 8px;
  }
  
  .dna-position {
    font-size: 14px;
    color: var(--ip-os-text-secondary);
    margin: 0;
  }
}
</style>

