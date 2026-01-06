<template>
  <div class="form-input">
    <el-form :model="formData" label-width="100px" class="creation-form">
      <el-form-item label="标题">
        <el-input
          v-model="formData.title"
          placeholder="请输入内容标题"
          class="ip-os-input"
        />
      </el-form-item>
      
      <el-form-item label="痛点描述">
        <el-input
          v-model="formData.painPoint"
          type="textarea"
          :rows="3"
          placeholder="描述目标受众的痛点..."
          class="ip-os-input"
        />
      </el-form-item>
      
      <el-form-item label="目标受众">
        <el-select
          v-model="formData.audience"
          placeholder="选择目标受众"
          class="ip-os-input"
          style="width: 100%"
        >
          <el-option label="年轻人" value="young" />
          <el-option label="职场人士" value="professional" />
          <el-option label="创业者" value="entrepreneur" />
          <el-option label="学生" value="student" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="内容类型">
        <el-radio-group v-model="formData.contentType">
          <el-radio label="article">文章</el-radio>
          <el-radio label="post">社交媒体</el-radio>
          <el-radio label="script">视频脚本</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="额外要求">
        <el-input
          v-model="formData.additional"
          type="textarea"
          :rows="2"
          placeholder="其他要求（可选）"
          class="ip-os-input"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { MPAgentInfo } from "@/api/modules/miniprogram";

interface Props {
  agent: MPAgentInfo;
  conversationHistory: Array<{ role: "user" | "assistant"; content: string }>;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  submit: [content: string];
  "update:conversation": [messages: Array<{ role: "user" | "assistant"; content: string }>];
}>();

const formData = ref({
  title: "",
  painPoint: "",
  audience: "",
  contentType: "article",
  additional: ""
});

// 监听表单变化，自动生成 prompt
watch(
  () => formData.value,
  () => {
    generatePrompt();
  },
  { deep: true }
);

const generatePrompt = () => {
  const parts: string[] = [];
  
  if (formData.value.title) {
    parts.push(`标题：${formData.value.title}`);
  }
  
  if (formData.value.painPoint) {
    parts.push(`痛点：${formData.value.painPoint}`);
  }
  
  if (formData.value.audience) {
    const audienceMap: Record<string, string> = {
      young: "年轻人",
      professional: "职场人士",
      entrepreneur: "创业者",
      student: "学生",
      other: "其他"
    };
    parts.push(`目标受众：${audienceMap[formData.value.audience] || formData.value.audience}`);
  }
  
  if (formData.value.contentType) {
    const typeMap: Record<string, string> = {
      article: "文章",
      post: "社交媒体",
      script: "视频脚本"
    };
    parts.push(`内容类型：${typeMap[formData.value.contentType] || formData.value.contentType}`);
  }
  
  if (formData.value.additional) {
    parts.push(`额外要求：${formData.value.additional}`);
  }
  
  const prompt = parts.join("\n");
  
  // 更新对话历史（仅用户输入部分）
  if (prompt) {
    emit("update:conversation", [{ role: "user", content: prompt }]);
  }
};

// 暴露提交方法
defineExpose({
  getPrompt: () => {
    const parts: string[] = [];
    if (formData.value.title) parts.push(`标题：${formData.value.title}`);
    if (formData.value.painPoint) parts.push(`痛点：${formData.value.painPoint}`);
    if (formData.value.audience) {
      const audienceMap: Record<string, string> = {
        young: "年轻人",
        professional: "职场人士",
        entrepreneur: "创业者",
        student: "学生",
        other: "其他"
      };
      parts.push(`目标受众：${audienceMap[formData.value.audience] || formData.value.audience}`);
    }
    if (formData.value.contentType) {
      const typeMap: Record<string, string> = {
        article: "文章",
        post: "社交媒体",
        script: "视频脚本"
      };
      parts.push(`内容类型：${typeMap[formData.value.contentType] || formData.value.contentType}`);
    }
    if (formData.value.additional) parts.push(`额外要求：${formData.value.additional}`);
    return parts.join("\n");
  },
  validate: () => {
    return !!(formData.value.title && formData.value.painPoint);
  }
});
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.form-input {
  height: 100%;
  overflow-y: auto;
  @extend .ip-os-scrollbar;
}

.creation-form {
  :deep(.el-form-item__label) {
    color: var(--ip-os-text-primary);
  }
  
  :deep(.el-radio) {
    color: var(--ip-os-text-primary);
  }
  
  :deep(.el-radio__input.is-checked .el-radio__inner) {
    background-color: var(--ip-os-accent-primary);
    border-color: var(--ip-os-accent-primary);
  }
}
</style>

