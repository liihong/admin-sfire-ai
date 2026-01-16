<template>
  <div class="agent-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      label-position="right"
    >
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="智能体名称" prop="name">
            <el-input v-model="formData.name" placeholder="请输入智能体名称" maxlength="128" show-word-limit />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="图标" prop="icon">
            <el-input v-model="formData.icon" placeholder="请输入图标URL或图标标识" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="描述信息" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入描述信息"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="系统提示词" prop="systemPrompt">
        <div class="prompt-wrapper">
          <el-input
            v-model="formData.systemPrompt"
            type="textarea"
            :rows="10"
            placeholder="请输入系统提示词（System Prompt）"
            maxlength="5000"
            show-word-limit
          />
          <div class="template-actions">
            <el-button type="primary" link :icon="Document" @click="showTemplateDialog = true">
              选择预设模板
            </el-button>
          </div>
        </div>
      </el-form-item>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="AI模型" prop="model">
            <el-select v-model="formData.model" placeholder="请选择AI模型" filterable style="width: 100%">
              <el-option
                v-for="model in modelList"
                :key="model.id"
                :label="model.name"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-radio-group v-model="formData.status">
              <el-radio :label="1">上架</el-radio>
              <el-radio :label="0">下架</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">参数配置</el-divider>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="Temperature" prop="config.temperature">
            <div class="slider-wrapper">
              <el-slider
                v-model="formData.config.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
                :show-input-controls="false"
                style="width: 100%"
              />
              <div class="slider-tip">控制输出的随机性，值越大越随机</div>
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Max Tokens" prop="config.maxTokens">
            <div class="slider-wrapper">
              <el-slider
                v-model="formData.config.maxTokens"
                :min="1"
                :max="32000"
                :step="100"
                show-input
                :show-input-controls="false"
                style="width: 100%"
              />
              <div class="slider-tip">生成内容的最大token数</div>
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="Top P" prop="config.topP">
            <div class="slider-wrapper">
              <el-slider
                v-model="formData.config.topP"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
                :show-input-controls="false"
                style="width: 100%"
              />
              <div class="slider-tip">核采样参数，控制输出的多样性</div>
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Frequency Penalty" prop="config.frequencyPenalty">
            <div class="slider-wrapper">
              <el-slider
                v-model="formData.config.frequencyPenalty"
                :min="-2"
                :max="2"
                :step="0.1"
                show-input
                :show-input-controls="false"
                style="width: 100%"
              />
              <div class="slider-tip">频率惩罚，减少重复内容</div>
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="Presence Penalty" prop="config.presencePenalty">
        <div class="slider-wrapper">
          <el-slider
            v-model="formData.config.presencePenalty"
            :min="-2"
            :max="2"
            :step="0.1"
            show-input
            :show-input-controls="false"
            style="width: 100%"
          />
          <div class="slider-tip">存在惩罚，鼓励谈论新话题</div>
        </div>
      </el-form-item>

      <el-form-item label="排序顺序" prop="sortOrder">
        <el-input-number
          v-model="formData.sortOrder"
          :min="0"
          :max="9999"
          :step="1"
          style="width: 200px"
        />
        <span class="form-tip">数字越小越靠前</span>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
        <el-button @click="handleCancel">取消</el-button>
      </el-form-item>
    </el-form>

    <!-- 预设模板对话框 -->
    <el-dialog v-model="showTemplateDialog" title="选择预设模板" width="800px">
      <el-table :data="templateList" @row-click="handleSelectTemplate">
        <el-table-column prop="name" label="模板名称" width="150" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="content" label="模板内容" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleSelectTemplate(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { Document } from "@element-plus/icons-vue";
import { Agent } from "@/api/interface";
import { createAgent, updateAgent, getPromptTemplates, getAvailableModels } from "@/api/modules/agent";

interface Props {
  formData?: Partial<Agent.ResAgentItem>;
  isEdit?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  formData: () => ({}),
  isEdit: false,
});

const emit = defineEmits<{
  submit: [];
  cancel: [];
}>();

const formRef = ref<FormInstance>();
const submitting = ref(false);
const showTemplateDialog = ref(false);
const templateList = ref<Agent.PromptTemplate[]>([]);
const modelList = ref<Array<{ id: string; name: string; maxTokens: number }>>([]);

// 表单数据
const formData = reactive<Agent.ReqAgentForm>({
  name: "",
  icon: "",
  description: "",
  systemPrompt: "",
  model: "",
  config: {
    temperature: 0.7,
    maxTokens: 2000,
    topP: 1.0,
    frequencyPenalty: 0.0,
    presencePenalty: 0.0,
  },
  sortOrder: 0,
  status: 1,
});

// 表单验证规则
const rules: FormRules = {
  name: [{ required: true, message: "请输入智能体名称", trigger: "blur" }],
  icon: [{ required: true, message: "请输入图标", trigger: "blur" }],
  systemPrompt: [{ required: true, message: "请输入系统提示词", trigger: "blur" }],
  model: [{ required: true, message: "请选择AI模型", trigger: "change" }],
};

// 初始化表单数据
const initFormData = () => {
  if (props.formData && Object.keys(props.formData).length > 0) {
    Object.assign(formData, {
      id: props.formData.id,
      name: props.formData.name || "",
      icon: props.formData.icon || "",
      description: props.formData.description || "",
      systemPrompt: props.formData.systemPrompt || "",
      model: props.formData.model || "",
      config: {
        temperature: props.formData.config?.temperature ?? 0.7,
        maxTokens: props.formData.config?.maxTokens ?? 2000,
        topP: props.formData.config?.topP ?? 1.0,
        frequencyPenalty: props.formData.config?.frequencyPenalty ?? 0.0,
        presencePenalty: props.formData.config?.presencePenalty ?? 0.0,
      },
      sortOrder: props.formData.sortOrder ?? 0,
      status: props.formData.status ?? 1,
    });
  }
};

// 获取预设模板列表
const fetchTemplates = async () => {
  try {
    const response = await getPromptTemplates();
    if (response.data) {
      templateList.value = response.data;
    }
  } catch (error) {
    console.error("获取模板列表失败:", error);
  }
};

// 获取可用模型列表
const fetchModels = async () => {
  try {
    const response = await getAvailableModels();
    if (response.data) {
      modelList.value = response.data;
      // 如果没有选择模型，默认选择第一个
      if (!formData.model && modelList.value.length > 0) {
        formData.model = modelList.value[0].id;
      }
    }
  } catch (error) {
    console.error("获取模型列表失败:", error);
  }
};

// 选择模板
const handleSelectTemplate = (template: Agent.PromptTemplate) => {
  formData.systemPrompt = template.content;
  showTemplateDialog.value = false;
  ElMessage.success(`已应用模板：${template.name}`);
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();
  submitting.value = true;

  try {
    if (props.isEdit && formData.id) {
      await updateAgent(formData as Agent.ReqAgentForm);
      ElMessage.success("更新成功");
    } else {
      await createAgent(formData);
      ElMessage.success("创建成功");
    }
    emit("submit");
  } catch (error) {
    console.error("提交失败:", error);
  } finally {
    submitting.value = false;
  }
};

// 取消
const handleCancel = () => {
  emit("cancel");
};

// 监听props变化
watch(
  () => props.formData,
  () => {
    initFormData();
  },
  { immediate: true, deep: true }
);

// 初始化
onMounted(() => {
  initFormData();
  fetchTemplates();
  fetchModels();
});
</script>

<style scoped lang="scss">
.agent-form {
  padding: 20px;

  .prompt-wrapper {
    position: relative;
    width:100%;
    .template-actions {
      margin-top: 8px;
      text-align: right;
    }
  }

  .slider-wrapper {
    .slider-tip {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-top: 8px;
    }
  }

  .form-tip {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-left: 12px;
  }
}
</style>






















