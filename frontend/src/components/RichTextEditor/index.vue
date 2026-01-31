<template>
  <div class="rich-text-editor">
    <div ref="editorRef" class="editor-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import Quill from "quill";
import "quill/dist/quill.snow.css";

interface Props {
  modelValue: string;
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "",
  placeholder: "请输入内容..."
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const editorRef = ref<HTMLElement>();
let quillInstance: Quill | null = null;
let isUpdating = false; // 防止更新时触发 watch

// 设置编辑器内容
const setContent = (content: string) => {
  if (!quillInstance) return;
  const normalizedContent = content || "";
  const currentContent = quillInstance.root.innerHTML || "";
  
  // 只有当内容真正不同时才更新
  if (currentContent !== normalizedContent) {
    isUpdating = true;
    try {
      // 使用 Quill 的 clipboard API 来设置内容，这样可以正确解析 HTML
      if (normalizedContent) {
        const delta = quillInstance.clipboard.convert({ html: normalizedContent });
        quillInstance.setContents(delta, "silent");
      } else {
        // 如果内容为空，清空编辑器
        quillInstance.setText("", "silent");
      }
    } catch (error) {
      // 如果转换失败，直接设置 HTML
      console.warn("Quill content conversion failed, using innerHTML:", error);
      quillInstance.root.innerHTML = normalizedContent;
    }
    isUpdating = false;
  }
};

// 初始化编辑器
const initEditor = async () => {
  if (!editorRef.value || quillInstance) return;

  // 等待 DOM 完全渲染
  await nextTick();

  // 配置工具栏，只保留最基础的功能
  const toolbarOptions = [
    [{ header: [1, 2, 3, false] }], // 标题
    ["bold", "italic", "underline"], // 加粗、斜体、下划线
    [{ list: "ordered" }, { list: "bullet" }], // 有序列表、无序列表
    [{ indent: "-1" }, { indent: "+1" }], // 缩进
    ["link"], // 链接
    ["clean"] // 清除格式
  ];

  quillInstance = new Quill(editorRef.value, {
    theme: "snow",
    placeholder: props.placeholder,
    modules: {
      toolbar: toolbarOptions
    }
  });

  // 监听内容变化
  quillInstance.on("text-change", () => {
    if (!isUpdating && quillInstance) {
      const content = quillInstance.root.innerHTML || "";
      emit("update:modelValue", content);
    }
  });

  // 初始化后立即设置内容（无论是否为空）
  await nextTick();
  setContent(props.modelValue || "");
};

onMounted(async () => {
  await initEditor();
});

// 监听外部值变化（用于编辑模式下数据回填）
watch(
  () => props.modelValue,
  async (newValue) => {
    if (quillInstance) {
      // 等待一个 tick 确保编辑器已准备好
      await nextTick();
      setContent(newValue);
    } else if (newValue && editorRef.value) {
      // 如果编辑器还没初始化，先初始化再设置
      await initEditor();
      if (quillInstance) {
        setContent(newValue);
      }
    }
  },
  { immediate: true }
);

// 清理
onBeforeUnmount(() => {
  if (quillInstance) {
    quillInstance = null;
  }
});
</script>

<style scoped lang="scss">
.rich-text-editor {
  :deep(.ql-container) {
    min-height: 300px;
    font-size: 14px;
  }

  :deep(.ql-editor) {
    min-height: 300px;
  }

  :deep(.ql-toolbar) {
    border-top: 1px solid var(--el-border-color);
    border-left: 1px solid var(--el-border-color);
    border-right: 1px solid var(--el-border-color);
    border-bottom: none;
    border-radius: 4px 4px 0 0;
  }

  :deep(.ql-container) {
    border-bottom: 1px solid var(--el-border-color);
    border-left: 1px solid var(--el-border-color);
    border-right: 1px solid var(--el-border-color);
    border-top: none;
    border-radius: 0 0 4px 4px;
  }
}
</style>

