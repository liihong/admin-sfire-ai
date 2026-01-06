<template>
  <div class="refinery-deck">
    <div class="deck-header">
      <h3 class="deck-title">产出与精炼平台</h3>
      <div class="deck-actions">
        <el-button
          v-if="hasVersions"
          type="primary"
          size="small"
          :icon="Plus"
          @click="handleNewVersion"
        >
          新版本
        </el-button>
      </div>
    </div>
    
    <!-- 版本标签页 -->
    <div v-if="hasVersions" class="deck-versions">
      <div
        v-for="version in contentVersions"
        :key="version.id"
        class="version-tab"
        :class="{ 'is-active': currentVersionId === version.id }"
        @click="handleSwitchVersion(version.id)"
      >
        <span class="version-name">{{ version.agentName }}</span>
        <el-button
          type="danger"
          size="small"
          text
          :icon="Delete"
          @click.stop="handleDeleteVersion(version.id)"
        />
      </div>
    </div>
    
    <!-- 内容显示区 -->
    <div class="deck-content">
      <div
        v-if="isGenerating"
        class="content-generating"
      >
        <div class="generating-text" ref="generatingTextRef">
          {{ currentContent }}
          <span class="typing-cursor">|</span>
        </div>
        <div class="generating-particles"></div>
      </div>
      
      <div
        v-else-if="currentContent"
        class="content-display"
        ref="contentDisplayRef"
        @mouseup="handleTextSelection"
      >
        <div class="content-text">{{ currentContent }}</div>
      </div>
      
      <div v-else class="content-empty">
        <el-icon :size="64"><Document /></el-icon>
        <p>生成的内容将在这里显示</p>
      </div>
    </div>
    
    <!-- 浮动工具栏 -->
    <div
      v-if="selectedText"
      class="floating-toolbar"
      :style="toolbarStyle"
    >
      <el-button size="small" @click="handleRefine">润色</el-button>
      <el-button size="small" @click="handleExpand">扩写</el-button>
      <el-button size="small" @click="handleShrink">缩写</el-button>
      <el-button size="small" @click="handleToScript">转为视频脚本</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { Plus, Delete, Document } from "@element-plus/icons-vue";
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { gsap } from "gsap";

const ipCreationStore = useIPCreationStore();

const generatingTextRef = ref<HTMLElement>();
const contentDisplayRef = ref<HTMLElement>();
const selectedText = ref("");
const toolbarStyle = ref({ top: "0px", left: "0px" });

const isGenerating = computed(() => ipCreationStore.isGenerating);
const currentContent = computed(() => ipCreationStore.currentContent);
const contentVersions = computed(() => ipCreationStore.contentVersions);
const currentVersionId = computed(() => ipCreationStore.currentVersionId);
const hasVersions = computed(() => ipCreationStore.hasVersions);

// 监听内容变化，添加打字机效果
watch(
  () => currentContent.value,
  () => {
    if (isGenerating.value && generatingTextRef.value) {
      // 滚动到底部
      nextTick(() => {
        if (generatingTextRef.value) {
          generatingTextRef.value.scrollTop = generatingTextRef.value.scrollHeight;
        }
      });
    }
  }
);

// 文本选择处理
const handleTextSelection = () => {
  const selection = window.getSelection();
  if (selection && selection.toString().trim()) {
    selectedText.value = selection.toString().trim();
    updateToolbarPosition(selection);
  } else {
    selectedText.value = "";
  }
};

// 更新工具栏位置
const updateToolbarPosition = (selection: Selection) => {
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  const contentRect = contentDisplayRef.value?.getBoundingClientRect();
  
  if (contentRect) {
    toolbarStyle.value = {
      top: `${rect.top - contentRect.top - 40}px`,
      left: `${rect.left - contentRect.left}px`
    };
  }
};

// 切换版本
const handleSwitchVersion = (versionId: string) => {
  ipCreationStore.setCurrentVersion(versionId);
};

// 删除版本
const handleDeleteVersion = (versionId: string) => {
  ipCreationStore.deleteVersion(versionId);
};

// 创建新版本
const handleNewVersion = () => {
  // 触发父组件生成新版本
  // 这里需要从父组件传入方法
};

// 工具栏操作
const handleRefine = () => {
  // TODO: 实现润色功能
  console.log("润色:", selectedText.value);
  selectedText.value = "";
};

const handleExpand = () => {
  // TODO: 实现扩写功能
  console.log("扩写:", selectedText.value);
  selectedText.value = "";
};

const handleShrink = () => {
  // TODO: 实现缩写功能
  console.log("缩写:", selectedText.value);
  selectedText.value = "";
};

const handleToScript = () => {
  // TODO: 实现转为视频脚本功能
  console.log("转为视频脚本:", selectedText.value);
  selectedText.value = "";
};
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.refinery-deck {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: var(--ip-os-bg-secondary);
  border-left: 1px solid var(--ip-os-border-primary);
  position: relative;
}

.deck-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .deck-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--ip-os-text-primary);
    margin: 0;
  }
}

.deck-versions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  
  .version-tab {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--ip-os-bg-tertiary);
    border: 1px solid var(--ip-os-border-secondary);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 12px;
    color: var(--ip-os-text-secondary);
    
    &:hover {
      border-color: var(--ip-os-accent-primary);
    }
    
    &.is-active {
      border-color: var(--ip-os-accent-primary);
      background: rgba(255, 107, 53, 0.1);
      color: var(--ip-os-accent-primary);
    }
    
    .version-name {
      max-width: 100px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.deck-content {
  flex: 1;
  overflow-y: auto;
  @extend .ip-os-scrollbar;
}

.content-generating {
  position: relative;
  min-height: 200px;
  
  .generating-text {
    font-size: 14px;
    line-height: 1.8;
    color: var(--ip-os-text-primary);
    white-space: pre-wrap;
    word-wrap: break-word;
    
    .typing-cursor {
      display: inline-block;
      animation: blink 1s infinite;
      color: var(--ip-os-accent-primary);
    }
  }
  
  .generating-particles {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    // 粒子效果可以通过 CSS 或 Canvas 实现
  }
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

.content-display {
  font-size: 14px;
  line-height: 1.8;
  color: var(--ip-os-text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
  user-select: text;
  
  .content-text {
    padding: 16px;
    background: var(--ip-os-bg-tertiary);
    border-radius: 8px;
  }
}

.content-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
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

.floating-toolbar {
  position: absolute;
  display: flex;
  gap: 8px;
  padding: 8px;
  background: var(--ip-os-bg-tertiary);
  border: 1px solid var(--ip-os-border-primary);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
  backdrop-filter: blur(10px);
}
</style>

