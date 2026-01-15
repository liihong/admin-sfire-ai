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
        <el-button
          v-if="currentContent"
          size="small"
          @click="showQRCodeDialog = true"
        >
          <el-icon><Iphone /></el-icon>
          同步到移动端
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

    <!-- 编辑器工具栏 -->
    <div v-if="currentContent" class="editor-toolbar">
      <el-button-group>
        <el-button size="small" @click="formatText('bold')" title="加粗">
          <strong>B</strong>
        </el-button>
        <el-button size="small" @click="formatText('h1')" title="标题1">
          H1
        </el-button>
        <el-button size="small" @click="formatText('h2')" title="标题2">
          H2
        </el-button>
      </el-button-group>
      <el-button-group style="margin-left: 8px;">
        <el-button size="small" @click="copyContent" title="复制">
          <el-icon><CopyDocument /></el-icon>
        </el-button>
        <el-button size="small" @click="clearContent" title="清空">
          <el-icon><Delete /></el-icon>
        </el-button>
      </el-button-group>
    </div>

    <!-- 内容显示区 -->
    <div class="deck-content" :class="{ 'has-toolbar': currentContent }">
      <div
        v-if="currentContent"
        class="content-display"
        ref="contentDisplayRef"
        @mouseup="handleTextSelection"
      >
        <textarea
          ref="editorRef"
          class="content-editor"
          v-model="editableContent"
          @input="handleEditorInput"
        ></textarea>
      </div>

      <div v-else class="content-empty">
        <el-icon :size="64"><Document /></el-icon>
        <p>生成的内容将在这里显示</p>
      </div>
    </div>

    <!-- 页脚信息栏 -->
    <div v-if="currentContent" class="deck-footer">
      <span class="footer-info">
        字符数: {{ characterCount }} | 预计时长: {{ estimatedDuration }}分钟
      </span>
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

    <!-- 二维码对话框 -->
    <el-dialog
      v-model="showQRCodeDialog"
      title="同步到移动端"
      width="400px"
      center
    >
      <div class="qrcode-container">
        <p class="qrcode-tip">使用微信扫描二维码,在移动端继续编辑</p>
        <VueQrcode
          :value="qrCodeValue"
          :options="{ width: 280, margin: 2 }"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { Plus, Delete, Document, CopyDocument, Iphone } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import VueQrcode from '@chenfengyuan/vue-qrcode';
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { useRoute } from "vue-router";

const ipCreationStore = useIPCreationStore();
const route = useRoute();

const contentDisplayRef = ref<HTMLElement>();
const editorRef = ref<HTMLTextAreaElement>();
const selectedText = ref("");
const toolbarStyle = ref({ top: "0px", left: "0px" });
const showQRCodeDialog = ref(false);
const editableContent = ref("");

const isGenerating = computed(() => ipCreationStore.isGenerating);
const currentContent = computed(() => ipCreationStore.currentContent);
const contentVersions = computed(() => ipCreationStore.contentVersions);
const currentVersionId = computed(() => ipCreationStore.currentVersionId);
const hasVersions = computed(() => ipCreationStore.hasVersions);

// 计算字符数和预计时长
const characterCount = computed(() => editableContent.value.length);
const estimatedDuration = computed(() => {
  const wordsPerMinute = 250; // 每分钟250字
  const minutes = characterCount.value / wordsPerMinute;
  return minutes.toFixed(1);
});

// 二维码内容
const qrCodeValue = computed(() => {
  const projectId = route.params.projectId;
  // 构建小程序深度链接
  return `weixin://dl/business/?t=xxx&projectId=${projectId}&scriptId=${currentVersionId.value}`;
});

// 同步编辑内容到 store
const handleEditorInput = () => {
  ipCreationStore.updateCurrentContent(editableContent.value);
};

// 监听 currentContent 变化,同步到编辑器
watch(
  () => currentContent.value,
  (newContent) => {
    if (newContent !== editableContent.value) {
      editableContent.value = newContent;
    }
  },
  { immediate: true }
);

// 格式化文本
const formatText = (type: string) => {
  const textarea = editorRef.value;
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selectedText = editableContent.value.substring(start, end);
  let replacement = "";

  switch (type) {
    case "bold":
      replacement = `**${selectedText}**`;
      break;
    case "h1":
      replacement = `# ${selectedText}`;
      break;
    case "h2":
      replacement = `## ${selectedText}`;
      break;
  }

  if (replacement) {
    editableContent.value =
      editableContent.value.substring(0, start) +
      replacement +
      editableContent.value.substring(end);
    handleEditorInput();
  }
};

// 复制内容
const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(editableContent.value);
    ElMessage.success("已复制到剪贴板");
  } catch (error) {
    ElMessage.error("复制失败");
  }
};

// 清空内容
const clearContent = () => {
  editableContent.value = "";
  handleEditorInput();
};

// 监听内容变化，右侧内容滚动到底部
watch(
  () => editableContent.value,
  () => {
    nextTick(() => {
      if (contentDisplayRef.value) {
        contentDisplayRef.value.scrollTop = contentDisplayRef.value.scrollHeight;
      }
    });
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

  .deck-actions {
    display: flex;
    gap: 8px;
  }
}

.editor-toolbar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: var(--ip-os-bg-primary);
  border: 1px solid var(--ip-os-border-primary);
  border-radius: 8px;
  margin-bottom: 12px;
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
      background: rgba(255, 107, 53, 0.08);
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
  // flex: 1;
  // overflow-y: auto;
  @extend .ip-os-scrollbar;

  &.has-toolbar {
    min-height: 0;
  }
}

.content-editor {
  width: 100%;
  min-height: 400px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--ip-os-text-primary);
  background: var(--ip-os-bg-primary);
  border: 1px solid var(--ip-os-border-primary);
  border-radius: 8px;
  resize: none;
  outline: none;
  font-family: inherit;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);

  &:focus {
    border-color: var(--ip-os-accent-primary);
  }
}

.deck-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-top: 12px;
  background: var(--ip-os-bg-primary);
  border: 1px solid var(--ip-os-border-primary);
  border-radius: 8px;
  font-size: 12px;
  color: var(--ip-os-text-secondary);
}

.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;

  .qrcode-tip {
    font-size: 14px;
    color: var(--ip-os-text-secondary);
    margin-bottom: 20px;
    text-align: center;
  }

  canvas {
    border-radius: 8px;
    padding: 16px;
    background: var(--ip-os-bg-primary);
    border: 1px solid var(--ip-os-border-primary);
  }
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
    background: var(--ip-os-bg-primary);
    border-radius: 8px;
    border: 1px solid var(--ip-os-border-primary);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
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
  background: var(--ip-os-bg-primary);
  border: 1px solid var(--ip-os-border-primary);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 100;
  backdrop-filter: blur(10px);
}
</style>

