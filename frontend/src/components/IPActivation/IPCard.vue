<template>
  <div
    class="ip-card"
    :class="{ 'is-active': project.isActive }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @click="handleClick"
  >
    <div class="ip-card-background">
      <!-- 背景视频或渐变 -->
      <div class="ip-card-bg-gradient"></div>
    </div>
    
    <div class="ip-card-content">
      <div class="ip-card-header">
        <h3 class="ip-card-name">{{ project.name }}</h3>
        <el-tag v-if="project.isActive" type="success" size="small" class="ip-card-active-tag">
          当前IP
        </el-tag>
      </div>
      
      <div class="ip-card-info">
        <div class="ip-card-item">
          <el-icon><Briefcase /></el-icon>
          <span>{{ project.industry }}</span>
        </div>
        <div class="ip-card-item">
          <el-icon><ChatDotRound /></el-icon>
          <span>{{ project.tone }}</span>
        </div>
        <div v-if="project.ipPersona" class="ip-card-item">
          <el-icon><User /></el-icon>
          <span class="ip-card-persona">{{ project.ipPersona }}</span>
        </div>
      </div>
      
      <div class="ip-card-footer">
        <div class="ip-card-time">{{ formatTime(project.updatedAt) }}</div>
        <div class="ip-card-action">
          <span class="ip-card-action-text">激活</span>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
    
    <div class="ip-card-glow"></div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Briefcase, ChatDotRound, User, ArrowRight } from "@element-plus/icons-vue";
import type { MPProject } from "@/api/modules/miniprogram";
import { cardHoverAnimation, cardLeaveAnimation } from "@/utils/animations/cardHover";
import dayjs from "dayjs";

interface Props {
  project: MPProject;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  click: [project: MPProject];
}>();

const cardRef = ref<HTMLElement>();

const handleMouseEnter = (e: MouseEvent) => {
  const card = e.currentTarget as HTMLElement;
  cardHoverAnimation(card);
};

const handleMouseLeave = (e: MouseEvent) => {
  const card = e.currentTarget as HTMLElement;
  cardLeaveAnimation(card);
};

const handleClick = () => {
  emit("click", props.project);
};

const formatTime = (time: string) => {
  return dayjs(time).format("MM-DD HH:mm");
};
</script>

<style scoped lang="scss">
.ip-card {
  position: relative;
  width: 100%;
  height: 400px;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--ip-os-bg-secondary);
  border: 2px solid var(--ip-os-border-primary);
  
  &.is-active {
    border-color: var(--ip-os-accent-primary);
    box-shadow: 0 0 20px var(--ip-os-accent-glow);
  }
  
  .ip-card-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    
    .ip-card-bg-gradient {
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, 
        rgba(255, 107, 53, 0.1) 0%, 
        rgba(26, 31, 58, 0.8) 50%,
        rgba(10, 14, 39, 0.9) 100%
      );
      transition: all 0.3s ease;
    }
  }
  
  &:hover {
    .ip-card-bg-gradient {
      background: linear-gradient(135deg, 
        rgba(255, 107, 53, 0.2) 0%, 
        rgba(26, 31, 58, 0.7) 50%,
        rgba(10, 14, 39, 0.8) 100%
      );
    }
  }
  
  .ip-card-content {
    position: relative;
    z-index: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 24px;
    color: var(--ip-os-text-primary);
  }
  
  .ip-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    
    .ip-card-name {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      color: var(--ip-os-text-primary);
      text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    }
    
    .ip-card-active-tag {
      background: var(--ip-os-accent-primary);
      border: none;
      color: var(--ip-os-text-primary);
    }
  }
  
  .ip-card-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .ip-card-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: var(--ip-os-text-secondary);
      
      .el-icon {
        color: var(--ip-os-accent-primary);
      }
      
      .ip-card-persona {
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
    }
  }
  
  .ip-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 16px;
    border-top: 1px solid var(--ip-os-border-secondary);
    
    .ip-card-time {
      font-size: 12px;
      color: var(--ip-os-text-tertiary);
    }
    
    .ip-card-action {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--ip-os-accent-primary);
      font-weight: 600;
      transition: all 0.3s ease;
      
      .ip-card-action-text {
        font-size: 14px;
      }
      
      .el-icon {
        transition: transform 0.3s ease;
      }
    }
  }
  
  &:hover {
    .ip-card-action {
      .el-icon {
        transform: translateX(4px);
      }
    }
  }
  
  .ip-card-glow {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: inherit;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
}
</style>





