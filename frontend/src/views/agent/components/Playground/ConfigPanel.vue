<template>
    <div class="config-panel">
      <!-- Prompt 模板选择 -->
      <div class="config-section">
        <div class="section-header">
          <span class="section-title">Prompt 模板</span>
        </div>
        <el-select
          v-model="selectedTemplate"
          placeholder="选择预设模板"
          clearable
          style="width: 100%"
          @change="handleTemplateChange"
        >
          <el-option
            v-for="template in promptTemplates"
            :key="template.name"
            :label="template.label"
            :value="template.name"
          />
        </el-select>
      </div>
  
      <!-- System Prompt 编辑器 -->
      <div class="config-section">
        <PromptEditor v-model="localConfig.systemPrompt" :min-rows="12" />
      </div>
  
      <!-- 模型参数 -->
      <div class="config-section">
        <div class="section-header">
          <span class="section-title">模型参数</span>
        </div>
        <el-form :model="localConfig" label-width="120px" label-position="right">
          <el-form-item label="模型">
            <el-select
              v-model="localConfig.model"
              placeholder="请选择模型"
              filterable
              style="width: 100%"
              @change="handleConfigChange"
            >
              <el-option
                v-for="model in modelList"
                :key="model.id"
                :label="model.name"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
  
          <el-form-item label="Temperature">
            <div class="slider-item">
              <el-slider
                v-model="localConfig.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
                :show-input-controls="false"
                @change="handleConfigChange"
              />
              <div class="slider-tip">控制输出的随机性，值越大越随机</div>
            </div>
          </el-form-item>
  
          <el-form-item label="Max Tokens">
            <el-input-number
              v-model="localConfig.maxTokens"
              :min="1"
              :max="32000"
              :step="100"
              controls-position="right"
              style="width: 100%"
              @change="handleConfigChange"
            />
            <div class="form-tip">控制生成内容的最大长度</div>
          </el-form-item>
  
          <el-form-item label="Top P">
            <div class="slider-item">
              <el-slider
                v-model="localConfig.topP"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
                :show-input-controls="false"
                @change="handleConfigChange"
              />
              <div class="slider-tip">核采样，控制输出的多样性</div>
            </div>
          </el-form-item>
  
          <el-form-item label="Frequency Penalty">
            <div class="slider-item">
              <el-slider
                v-model="localConfig.frequencyPenalty"
                :min="-2"
                :max="2"
                :step="0.1"
                show-input
                :show-input-controls="false"
                @change="handleConfigChange"
              />
              <div class="slider-tip">频率惩罚，减少重复内容</div>
            </div>
          </el-form-item>
  
          <el-form-item label="Presence Penalty">
            <div class="slider-item">
              <el-slider
                v-model="localConfig.presencePenalty"
                :min="-2"
                :max="2"
                :step="0.1"
                show-input
                :show-input-controls="false"
                @change="handleConfigChange"
              />
              <div class="slider-tip">存在惩罚，鼓励新话题</div>
            </div>
          </el-form-item>
        </el-form>
      </div>
  
      <!-- 上下文预设（Few-shot Learning） -->
      <div class="config-section">
        <div class="section-header">
          <span class="section-title">上下文预设</span>
          <el-button size="small" text :icon="Plus" @click="handleAddContext">添加示例</el-button>
        </div>
        <div class="context-list">
          <div
            v-for="(context, index) in localConfig.contextMessages"
            :key="index"
            class="context-item"
          >
            <div class="context-header">
              <el-tag :type="context.role === 'user' ? 'primary' : 'success'" size="small">
                {{ context.role === "user" ? "用户" : "助手" }}
              </el-tag>
              <el-button
                size="small"
                text
                type="danger"
                :icon="Delete"
                @click="handleRemoveContext(index)"
              />
            </div>
            <el-input
              v-model="context.content"
              type="textarea"
              :rows="3"
              placeholder="请输入示例内容..."
              @input="handleConfigChange"
            />
          </div>
          <el-empty
            v-if="localConfig.contextMessages.length === 0"
            description="暂无示例数据"
            :image-size="80"
          />
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts" name="ConfigPanel">
  import { ref, reactive, watch } from "vue";
  import { Plus, Delete } from "@element-plus/icons-vue";
  import PromptEditor from "./PromptEditor.vue";
  
  interface Props {
    agentConfig: {
      systemPrompt: string;
      model: string;
      temperature: number;
      maxTokens: number;
      topP: number;
      frequencyPenalty: number;
      presencePenalty: number;
      contextMessages: Array<{ role: "user" | "assistant"; content: string }>;
    };
    modelList: Array<{ id: string; name: string; maxTokens: number }>;
  }
  
  const props = defineProps<Props>();
  
  const emit = defineEmits<{
    "config-change": [config: Partial<Props["agentConfig"]>];
  }>();
  
  // 本地配置副本
  const localConfig = reactive<Props["agentConfig"]>({
    systemPrompt: "",
    model: "",
    temperature: 0.7,
    maxTokens: 2000,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0,
    contextMessages: []
  });
  
  // Prompt 模板
  const promptTemplates = [
    {
      name: "xiaohongshu",
      label: "小红书风格",
      prompt: "你是一个专业的小红书文案创作助手。请用活泼、亲切、富有感染力的语言，结合表情符号，创作吸引人的文案。"
    },
    {
      name: "code_assistant",
      label: "代码助手",
      prompt: "你是一个专业的编程助手。请提供清晰、准确的代码解答，包含代码示例和详细注释。"
    },
    {
      name: "customer_service",
      label: "客服机器人",
      prompt: "你是一个友好的客服助手。请用礼貌、专业、耐心的语气回复用户问题，始终以用户满意为目标。"
    },
    {
      name: "copywriter",
      label: "文案创作",
      prompt: "你是一个创意文案专家。请创作有吸引力、有说服力的文案，适合各种营销场景。"
    }
  ];
  
  const selectedTemplate = ref("");
  
  // 监听外部配置变化
  watch(
    () => props.agentConfig,
    (newConfig) => {
      Object.assign(localConfig, newConfig);
    },
    { deep: true, immediate: true }
  );
  
  // 监听本地配置变化
  watch(
    () => localConfig.systemPrompt,
    () => {
      handleConfigChange();
    }
  );
  
  // 处理配置变更
  const handleConfigChange = () => {
    emit("config-change", { ...localConfig });
  };
  
  // 处理模板选择
  const handleTemplateChange = (templateName: string) => {
    if (templateName) {
      const template = promptTemplates.find(t => t.name === templateName);
      if (template) {
        localConfig.systemPrompt = template.prompt;
        handleConfigChange();
      }
    }
  };
  
  // 添加上下文示例
  const handleAddContext = () => {
    localConfig.contextMessages.push({
      role: "user",
      content: ""
    });
    handleConfigChange();
  };
  
  // 移除上下文示例
  const handleRemoveContext = (index: number) => {
    localConfig.contextMessages.splice(index, 1);
    handleConfigChange();
  };
  </script>
  
  <style scoped lang="scss">
  .config-panel {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  
    .config-section {
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
  
        .section-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }
  
      .slider-item {
        width: 100%;
  
        .slider-tip {
          margin-top: 4px;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
  
      .form-tip {
        margin-top: 4px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
  
      .context-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
  
        .context-item {
          padding: 12px;
          border: 1px solid var(--el-border-color);
          border-radius: 4px;
          background-color: var(--el-fill-color-lighter);
  
          .context-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
          }
        }
      }
    }
  }
  </style>