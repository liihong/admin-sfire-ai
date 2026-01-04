<template>
    <div class="prompt-editor">
      <div class="editor-header">
        <span class="editor-title">System Prompt</span>
        <div class="editor-actions">
          <el-button size="small" text :icon="DocumentCopy" @click="handleCopy">复制</el-button>
          <el-button size="small" text :icon="Delete" @click="handleClear">清空</el-button>
        </div>
      </div>
      <div class="editor-wrapper">
        <!-- 行号 -->
        <div class="line-numbers" ref="lineNumbersRef">
          <span
            v-for="lineNum in lineCount"
            :key="lineNum"
            class="line-number"
          >{{ lineNum }}</span>
        </div>
        <!-- 编辑器 -->
        <el-input
          ref="inputRef"
          v-model="modelValue"
          type="textarea"
          :rows="minRows"
          :maxlength="5000"
          placeholder="请输入系统提示词（System Prompt）..."
          class="editor-textarea"
          @input="handleInput"
          @scroll="handleScroll"
        />
      </div>
      <div class="editor-footer">
        <span class="char-count">{{ modelValue.length }} / 5000</span>
      </div>
    </div>
  </template>
  
  <script setup lang="ts" name="PromptEditor">
  import { ref, watch, computed, nextTick } from "vue";
  import { ElMessage, ElInput } from "element-plus";
  import { DocumentCopy, Delete } from "@element-plus/icons-vue";
  
  interface Props {
    modelValue: string;
    minRows?: number;
  }
  
  const props = withDefaults(defineProps<Props>(), {
    modelValue: "",
    minRows: 12
  });
  
  const emit = defineEmits<{
    "update:modelValue": [value: string];
  }>();
  
  const inputRef = ref<InstanceType<typeof ElInput>>();
  const lineNumbersRef = ref<HTMLElement>();
  
  const modelValue = computed({
    get: () => props.modelValue,
    set: (value) => emit("update:modelValue", value)
  });
  
  // 计算行数
  const lineCount = computed(() => {
    const lines = modelValue.value.split("\n").length;
    return Math.max(lines, props.minRows);
  });
  
  // 处理输入
  const handleInput = () => {
    updateLineNumbers();
  };
  
  // 更新行号
  const updateLineNumbers = () => {
    nextTick(() => {
      if (lineNumbersRef.value && inputRef.value) {
        const textarea = inputRef.value.$el.querySelector("textarea");
        if (textarea) {
          lineNumbersRef.value.scrollTop = textarea.scrollTop;
        }
      }
    });
  };
  
  // 处理滚动同步
  const handleScroll = () => {
    updateLineNumbers();
  };
  
  // 复制内容
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(modelValue.value);
      ElMessage.success("已复制到剪贴板");
    } catch (error) {
      ElMessage.error("复制失败");
    }
  };
  
  // 清空内容
  const handleClear = () => {
    modelValue.value = "";
  };
  
  watch(() => props.modelValue, () => {
    updateLineNumbers();
  }, { immediate: true });
  </script>
  
  <style scoped lang="scss">
  .prompt-editor {
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    background-color: var(--el-bg-color);
    overflow: hidden;
  
    .editor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background-color: var(--el-fill-color-light);
      border-bottom: 1px solid var(--el-border-color-lighter);
  
      .editor-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
  
    .editor-wrapper {
      position: relative;
      display: flex;
  
      .line-numbers {
        flex-shrink: 0;
        width: 50px;
        padding: 10px 8px;
        background-color: var(--el-fill-color-lighter);
        border-right: 1px solid var(--el-border-color-lighter);
        font-family: "Courier New", monospace;
        font-size: 14px;
        line-height: 1.5;
        text-align: right;
        color: var(--el-text-color-secondary);
        user-select: none;
        overflow: hidden;
  
        .line-number {
          display: block;
          height: 22.5px;
        }
      }
  
      .editor-textarea {
        flex: 1;
  
        :deep(.el-textarea__inner) {
          height: 100%;
          font-family: "Courier New", monospace;
          font-size: 14px;
          line-height: 1.5;
          padding: 10px 12px;
          border: none;
          resize: none;
          background-color: transparent;
          color: var(--el-text-color-primary);
  
          &::placeholder {
            color: var(--el-text-color-placeholder);
          }
        }
      }
    }
  
    .editor-footer {
      padding: 6px 12px;
      background-color: var(--el-fill-color-light);
      border-top: 1px solid var(--el-border-color-lighter);
      text-align: right;
  
      .char-count {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  </style>