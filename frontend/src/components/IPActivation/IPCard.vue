<template>
  <div
    class="ip-card"
    :class="{ 'is-active': project.isActive }"
    :style="{ '--gradient': getGradient() }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @click="handleClick"
  >
    <!-- 卡片顶部渐变区域 -->
    <div class="card-header">
      <!-- 左上角装饰线 -->
      <div class="header-line"></div>
      <!-- 激活状态角标 -->
      <div v-if="project.isActive" class="active-corner">
        <el-icon><Check /></el-icon>
      </div>
      <!-- 项目首字母 -->
      <div class="project-initial">{{ project.name.charAt(0) }}</div>
      <!-- 项目名称 -->
      <h2 class="project-name">{{ project.name }}</h2>
    </div>

    <!-- 卡片内容区域 -->
    <div class="card-body">
      <!-- 项目信息 -->
      <div class="info-text">
        <p><strong>行业赛道</strong> {{ project.industry }}</p>
        <p><strong>语气风格</strong> {{ project.tone }}</p>
        <p v-if="project.ipPersona" class="persona-text"><strong>IP人设</strong> {{ project.ipPersona }}</p>
      </div>

      <!-- 底部操作区 -->
      <div class="card-footer">
        <span class="update-time">
          <el-icon><Clock /></el-icon>
          {{ formatTime(project.updatedAt) }}
        </span>
        <div class="action-hint">
          <span>点击激活</span>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Check, Clock, ArrowRight } from "@element-plus/icons-vue";
import type { MPProject } from "@/api/modules/miniprogram";
import { cardHoverAnimation, cardLeaveAnimation } from "@/utils/animations/cardHover";
import dayjs from "dayjs";

// 渐变色配置
const gradients = [
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
  "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
];

interface Props {
  project: MPProject;
  index?: number;
}

const props = withDefaults(defineProps<Props>(), {
  index: 0
});

const emit = defineEmits<{
  click: [project: MPProject];
}>();

const cardRef = ref<HTMLElement>();

// 根据项目名称生成稳定的渐变色
const getGradient = () => {
  const charCode = props.project.name.charCodeAt(0) || 0;
  return gradients[charCode % gradients.length];
};

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
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);

    .action-hint .el-icon {
      transform: translateX(4px);
    }
  }

  // 激活状态边框
  &.is-active {
    box-shadow: 0 2px 12px rgba(59, 130, 246, 0.3), 0 0 0 2px #3b82f6;
  }

  // 卡片顶部渐变区域
  .card-header {
    background: var(--gradient);
    padding: 24px 20px 28px;
    position: relative;
    min-height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    flex-shrink: 0;

    // 左上角装饰线
    .header-line {
      position: absolute;
      top: 16px;
      left: 16px;
      width: 28px;
      height: 3px;
      background: rgba(255, 255, 255, 0.6);
      border-radius: 2px;
    }

    // 激活角标
    .active-corner {
      position: absolute;
      top: 14px;
      right: 14px;
      width: 26px;
      height: 26px;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;

      .el-icon {
        font-size: 13px;
        color: #10b981;
      }
    }

    // 项目首字母
    .project-initial {
      font-size: 64px;
      font-weight: 300;
      color: rgba(0, 0, 0, 0.2);
      line-height: 1;
      position: absolute;
      right: 20px;
      bottom: 16px;
      font-family: "Georgia", serif;
    }

    // 项目名称
    .project-name {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      color: #1f2937;
      line-height: 1.3;
      position: relative;
      z-index: 1;
      max-width: 65%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  // 卡片内容区域
  .card-body {
    background: #fff;
    padding: 20px;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    // 信息文本
    .info-text {
      margin: 0;

      p {
        margin: 0 0 6px 0;
        font-size: 13px;
        color: #4b5563;
        line-height: 1.5;

        strong {
          color: #6b7280;
          font-weight: 500;
          margin-right: 6px;
        }

        &:last-child {
          margin-bottom: 0;
        }
      }

      .persona-text {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
    }

    // 底部操作区
    .card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 14px;
      border-top: 1px solid #f3f4f6;
      margin-top: 16px;

      .update-time {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #9ca3af;

        .el-icon {
          font-size: 12px;
        }
      }

      .action-hint {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        font-weight: 600;
        color: #3b82f6;

        .el-icon {
          font-size: 14px;
          transition: transform 0.2s ease;
        }
      }
    }
  }
}
</style>







