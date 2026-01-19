<template>
  <div class="agent-builder">
    <el-card>
      <!-- 页面标题 -->
      <template #header>
        <div class="card-header">
          <span class="title">{{ isEdit ? '编辑Agent' : '创建Agent' }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="140px"
        label-position="right"
      >
        <!-- 基础配置 -->
        <el-divider content-position="left">基础配置</el-divider>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="Agent名称" prop="name">
              <el-input
                v-model="formData.name"
                placeholder="请输入Agent名称"
                maxlength="128"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="运行模式" prop="agent_mode">
              <el-radio-group v-model="formData.agent_mode">
                <el-radio :label="0">普通模式</el-radio>
                <el-radio :label="1">技能组装模式</el-radio>
              </el-radio-group>
              <div class="form-tip">
                {{ formData.agent_mode === 0 ? '直接编辑系统提示词' : '通过技能组装生成提示词' }}
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="图标" prop="icon">
          <el-input
            v-model="formData.icon"
            placeholder="请输入图标URL或图标标识"
            maxlength="256"
          />
        </el-form-item>

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

        <!-- 技能组装模式专属 -->
        <template v-if="formData.agent_mode === 1">
          <el-divider content-position="left">技能组装配置</el-divider>

          <!-- 技能选择器 -->
          <el-form-item label="选择技能">
            <SkillSelector
              v-model="formData.skill_ids"
              v-model:variables="formData.skill_variables"
              @change="handleSkillChange"
            />
          </el-form-item>

          <!-- 路由配置 -->
          <el-form-item label="启用智能路由">
            <el-switch v-model="isRoutingEnabled" />
            <span class="form-tip" style="margin-left: 12px">
              启用后，AI将根据用户输入自动选择最合适的技能
            </span>
          </el-form-item>

          <el-form-item v-if="isRoutingEnabled" label="路由特征">
            <el-input
              v-model="formData.routing_description"
              type="textarea"
              :rows="2"
              placeholder="描述本Agent的擅长场景，用于智能路由匹配"
              maxlength="500"
              show-word-limit
            />
            <div class="form-tip">例如：擅长处理餐饮招商、品牌推广等业务</div>
          </el-form-item>

          <!-- 预览Prompt -->
          <el-form-item>
            <el-button type="primary" :icon="View" @click="handlePreview" :loading="previewing">
              预览完整Prompt
            </el-button>
            <el-button :icon="DocumentCopy" @click="handleCopyPrompt" v-if="previewData.full_prompt">
              复制Prompt
            </el-button>
          </el-form-item>

          <!-- Prompt预览区 -->
          <el-form-item v-if="previewData.full_prompt">
            <PromptPreview
              :prompt="previewData.full_prompt"
              :token-count="previewData.token_count"
              :skills-used="previewData.skills_used"
            />
          </el-form-item>
        </template>

        <!-- 普通模式专属 -->
        <template v-else>
          <el-divider content-position="left">系统提示词</el-divider>
          <el-form-item label="系统提示词" prop="system_prompt">
            <el-input
              v-model="formData.system_prompt"
              type="textarea"
              :rows="10"
              placeholder="请输入系统提示词"
              maxlength="5000"
              show-word-limit
            />
          </el-form-item>
        </template>

        <!-- 参数配置 -->
        <el-divider content-position="left">参数配置</el-divider>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="AI模型" prop="model">
              <el-select v-model="formData.model" placeholder="请选择模型" style="width: 100%">
                <el-option label="GPT-4" value="gpt-4" />
                <el-option label="GPT-3.5-Turbo" value="gpt-3.5-turbo" />
                <el-option label="Claude-3-Opus" value="claude-3-opus" />
                <el-option label="Claude-3-Sonnet" value="claude-3-sonnet" />
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

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="Temperature">
              <div class="slider-wrapper">
                <el-slider
                  v-model="formData.config.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  show-input
                  :show-input-controls="false"
                />
                <div class="slider-tip">控制输出的随机性，值越大越随机</div>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Max Tokens">
              <div class="slider-wrapper">
                <el-slider
                  v-model="formData.config.maxTokens"
                  :min="1"
                  :max="32000"
                  :step="100"
                  show-input
                  :show-input-controls="false"
                />
                <div class="slider-tip">生成内容的最大token数</div>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="排序顺序">
          <el-input-number
            v-model="formData.sort_order"
            :min="0"
            :max="9999"
            :step="1"
            style="width: 200px"
          />
          <span class="form-tip">数字越小越靠前</span>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { View, DocumentCopy } from "@element-plus/icons-vue";
import { useRoute, useRouter } from "vue-router";
import { createAgentV2, updateAgentV2, previewPrompt, getAgentDetailV2 } from "@/api/modules/skillAssembly";
import { AgentV2 } from "@/api/interface";
import SkillSelector from "./components/SkillSelector.vue";
import PromptPreview from "./components/PromptPreview.vue";

const route = useRoute();
const router = useRouter();

const formRef = ref<FormInstance>();
const submitting = ref(false);
const previewing = ref(false);
const isEdit = computed(() => !!route.params.id);
const isRoutingEnabled = ref(false);

const formData = reactive<AgentV2.ReqAgentCreate>({
  name: "",
  icon: "",
  description: "",
  agent_mode: 0,
  system_prompt: "",
  model: "gpt-4",
  config: {
    temperature: 0.7,
    maxTokens: 2000,
    topP: 1.0,
    frequencyPenalty: 0.0,
    presencePenalty: 0.0
  },
  sort_order: 0,
  status: 1,
  skill_ids: [],
  skill_variables: {},
  routing_description: "",
  is_routing_enabled: 0
});

const previewData = reactive({
  full_prompt: "",
  token_count: 0,
  skills_used: [] as any[]
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入Agent名称", trigger: "blur" }],
  icon: [{ required: true, message: "请输入图标", trigger: "blur" }],
  model: [{ required: true, message: "请选择模型", trigger: "change" }]
};

// 加载Agent详情
const loadAgentDetail = async () => {
  const id = Number(route.params.id);
  try {
    const response = await getAgentDetailV2(id);
    const agent = response.data;

    Object.assign(formData, {
      name: agent.name,
      icon: agent.icon,
      description: agent.description,
      agent_mode: agent.agent_mode,
      system_prompt: agent.system_prompt,
      model: agent.model,
      config: agent.config || {
        temperature: 0.7,
        maxTokens: 2000
      },
      sort_order: agent.sort_order,
      status: agent.status,
      skill_ids: agent.skill_ids || [],
      skill_variables: agent.skill_variables || {},
      routing_description: agent.routing_description || "",
      is_routing_enabled: agent.is_routing_enabled
    });

    isRoutingEnabled.value = agent.is_routing_enabled === 1;
  } catch (error) {
    console.error("加载Agent详情失败:", error);
    ElMessage.error("加载失败");
  }
};

// 技能变化时
const handleSkillChange = (skills: any[]) => {
  console.log("技能变化:", skills);
};

// 预览Prompt
const handlePreview = async () => {
  if (!formData.skill_ids || formData.skill_ids.length === 0) {
    ElMessage.warning("请先选择技能");
    return;
  }

  previewing.value = true;
  try {
    const response = await previewPrompt(0, {
      skill_ids: formData.skill_ids,
      skill_variables: formData.skill_variables
    });
    previewData.full_prompt = response.data.full_prompt;
    previewData.token_count = response.data.token_count;
    previewData.skills_used = response.data.skills_used;
  } catch (error) {
    console.error("预览失败:", error);
    ElMessage.error("预览失败");
  } finally {
    previewing.value = false;
  }
};

// 复制Prompt
const handleCopyPrompt = () => {
  navigator.clipboard.writeText(previewData.full_prompt).then(() => {
    ElMessage.success("已复制到剪贴板");
  }).catch(() => {
    ElMessage.error("复制失败");
  });
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();
  submitting.value = true;

  try {
    // 更新is_routing_enabled
    formData.is_routing_enabled = isRoutingEnabled.value ? 1 : 0;

    if (isEdit.value) {
      const id = Number(route.params.id);
      await updateAgentV2(id, formData);
      ElMessage.success("更新成功");
    } else {
      await createAgentV2(formData);
      ElMessage.success("创建成功");
    }
    router.back();
  } catch (error) {
    console.error("提交失败:", error);
    ElMessage.error("操作失败");
  } finally {
    submitting.value = false;
  }
};

// 取消
const handleCancel = () => {
  router.back();
};

// 初始化
onMounted(() => {
  if (isEdit.value) {
    loadAgentDetail();
  }
});
</script>

<style scoped lang="scss">
.agent-builder {
  padding: 20px;

  .card-header {
    .title {
      font-size: 18px;
      font-weight: bold;
    }
  }

  .form-tip {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-left: 12px;
  }

  .slider-wrapper {
    width: 100%;

    .slider-tip {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-top: 8px;
    }
  }
}
</style>
