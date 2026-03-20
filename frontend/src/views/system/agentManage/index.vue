<template>
  <div class="agent-manage-container">
    <!-- 顶部操作栏 -->
    <div class="header-actions card">
      <div class="left">
        <el-input
          v-model="searchName"
          placeholder="搜索智能体名称..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @input="handleSearch"
        />
        <el-select v-model="searchStatus" placeholder="全部状态" clearable @change="handleSearch">
          <el-option label="已上架" :value="1" />
          <el-option label="已下架" :value="0" />
        </el-select>
      </div>
      <div class="right">
        <el-button type="primary" :icon="Plus" @click="openEditor()">
          新建智能体
        </el-button>
      </div>
    </div>

    <!-- 智能体卡片列表 -->
    <div class="agent-grid" v-loading="loading">
      <TransitionGroup name="card-list">
        <el-card
          v-for="agent in filteredAgents"
          :key="agent.id"
          class="agent-card"
          :class="{ 'is-offline': agent.status === 0 }"
          shadow="hover"
        >
          <!-- 卡片头部 -->
          <div class="card-header">
            <div class="agent-icon">
              <span class="icon-emoji">{{ agent.icon || '🤖' }}</span>
            </div>
            <div class="agent-info">
              <h3 class="agent-name">{{ agent.name }}</h3>
              <p class="agent-model">{{ agent.modelName ?? agent.model }}</p>
            </div>
            <el-switch
              v-model="agent.status"
              :active-value="1"
              :inactive-value="0"
              :loading="statusLoading === agent.id"
              @change="handleStatusChange(agent)"
            />
          </div>

          <!-- 卡片内容 -->
          <div class="card-body">
            <p class="agent-description">{{ agent.description || '暂无描述' }}</p>
            <div class="agent-stats">
              <div class="stat-item">
                <el-icon><ChatDotRound /></el-icon>
                <span>{{ formatNumber(agent.usageCount || 0) }} 次调用</span>
              </div>
              <div class="stat-item">
                <el-icon><Sort /></el-icon>
                <span>排序: {{ agent.sortOrder }}</span>
              </div>
            </div>
          </div>

          <!-- 卡片底部 -->
          <div class="card-footer">
            <el-button type="primary" link :icon="Edit" @click="openEditor(agent)">
              编辑配置
            </el-button>
            <el-button type="info" link :icon="CopyDocument" @click="duplicateAgent(agent)">
              复制
            </el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(agent)">
              删除
            </el-button>
          </div>
        </el-card>
      </TransitionGroup>

      <!-- 空状态 -->
      <el-empty v-if="!loading && filteredAgents.length === 0" description="暂无智能体配置">
        <el-button type="primary" @click="openEditor()">创建第一个智能体</el-button>
      </el-empty>
    </div>

    <!-- 全屏编辑对话框 -->
    <el-dialog
      v-model="editorVisible"
      :title="isEdit ? '编辑智能体' : '新建智能体'"
      fullscreen
      :close-on-click-modal="false"
      class="agent-editor-dialog"
    >
      <div class="editor-container">
        <!-- 左侧基础信息 -->
        <div class="editor-left">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-position="top"
            class="agent-form"
          >
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><InfoFilled /></el-icon>
                基础信息
              </h4>
              
              <el-form-item label="智能体图标" prop="icon">
                <div class="icon-picker">
                  <el-popover placement="bottom" :width="280" trigger="click">
                    <template #reference>
                      <div class="current-icon">
                        <span class="icon-display">{{ formData.icon || '🤖' }}</span>
                        <span class="icon-hint">点击选择</span>
                      </div>
                    </template>
                    <div class="emoji-grid">
                      <span
                        v-for="emoji in emojiList"
                        :key="emoji"
                        class="emoji-item"
                        :class="{ active: formData.icon === emoji }"
                        @click="formData.icon = emoji"
                      >
                        {{ emoji }}
                      </span>
                    </div>
                  </el-popover>
                </div>
              </el-form-item>

              <el-form-item label="智能体名称" prop="name">
                <el-input v-model="formData.name" placeholder="输入智能体名称" maxlength="20" show-word-limit />
              </el-form-item>

              <el-form-item label="简介描述" prop="description">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  placeholder="简要描述智能体的功能和用途"
                  :rows="3"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="使用模型" prop="model">
                <el-select v-model="formData.model" placeholder="选择AI模型" style="width: 100%">
                  <el-option
                    v-for="model in modelList"
                    :key="model.id"
                    :label="model.name"
                    :value="model.id"
                  >
                    <div class="model-option">
                      <span>{{ model.name }}</span>
                      <span class="model-provider">{{ getProviderName(model.provider) }}</span>
                      <span class="model-tokens">{{ model.maxTokens }} tokens</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="显示排序" prop="sortOrder">
                <el-input-number
                  v-model="formData.sortOrder"
                  :min="0"
                  :max="9999"
                  controls-position="right"
                  style="width: 100%"
                />
                <div class="form-tip">数值越小，在小程序端显示越靠前</div>
              </el-form-item>

              <el-form-item label="上架状态">
                <el-switch
                  v-model="formData.status"
                  :active-value="1"
                  :inactive-value="0"
                  active-text="已上架"
                  inactive-text="已下架"
                />
              </el-form-item>
            </div>
          </el-form>
        </div>

        <!-- 中间 System Prompt -->
        <div class="editor-center">
          <div class="form-section">
            <h4 class="section-title">
              <el-icon><Document /></el-icon>
              System Prompt
              <el-dropdown trigger="click" @command="applyTemplate">
                <el-button type="primary" link class="template-btn">
                  <el-icon><MagicStick /></el-icon>
                  预设模板
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="template in promptTemplates"
                      :key="template.id"
                      :command="template"
                    >
                      <div class="template-item">
                        <span class="template-name">{{ template.name }}</span>
                        <span class="template-category">{{ template.category }}</span>
                      </div>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </h4>
            
            <el-input
              v-model="formData.systemPrompt"
              type="textarea"
              placeholder="输入系统提示词，定义智能体的角色、能力和行为规范...

示例：
你是一位专业的客服助手，请用友善专业的语气回答用户问题。
- 保持回答简洁明了
- 遇到无法回答的问题，礼貌地引导用户联系人工客服"
              :rows="10"
              class="prompt-textarea"
              resize="none"
            />
            <div class="prompt-stats">
              <span>字数: {{ formData.systemPrompt?.length || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧参数配置 -->
        <div class="editor-right">
          <div class="form-section">
            <h4 class="section-title">
              <el-icon><Setting /></el-icon>
              模型参数配置
            </h4>

            <div class="param-item">
              <div class="param-header">
                <span class="param-label">Temperature (创造性)</span>
                <span class="param-value">{{ formData.config.temperature }}</span>
              </div>
              <el-slider
                v-model="formData.config.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :marks="temperatureMarks"
              />
              <p class="param-desc">较低值使输出更确定，较高值使输出更随机多样</p>
            </div>

            <div class="param-item">
              <div class="param-header">
                <span class="param-label">Max Tokens (最大长度)</span>
                <span class="param-value">{{ formData.config.maxTokens }}</span>
              </div>
              <el-slider
                v-model="formData.config.maxTokens"
                :min="100"
                :max="4096"
                :step="100"
              />
              <p class="param-desc">控制单次回复的最大长度</p>
            </div>

            <div class="param-item">
              <div class="param-header">
                <span class="param-label">Top P (核采样)</span>
                <span class="param-value">{{ formData.config.topP }}</span>
              </div>
              <el-slider
                v-model="formData.config.topP"
                :min="0"
                :max="1"
                :step="0.05"
              />
              <p class="param-desc">控制输出的多样性，与 Temperature 配合使用</p>
            </div>

            <div class="param-item">
              <div class="param-header">
                <span class="param-label">Frequency Penalty (频率惩罚)</span>
                <span class="param-value">{{ formData.config.frequencyPenalty }}</span>
              </div>
              <el-slider
                v-model="formData.config.frequencyPenalty"
                :min="0"
                :max="2"
                :step="0.1"
              />
              <p class="param-desc">降低重复词汇的出现频率</p>
            </div>

            <div class="param-item">
              <div class="param-header">
                <span class="param-label">Presence Penalty (存在惩罚)</span>
                <span class="param-value">{{ formData.config.presencePenalty }}</span>
              </div>
              <el-slider
                v-model="formData.config.presencePenalty"
                :min="0"
                :max="2"
                :step="0.1"
              />
              <p class="param-desc">鼓励模型谈论新话题</p>
            </div>

            <el-button type="info" plain class="reset-params-btn" @click="resetParams">
              <el-icon><RefreshLeft /></el-icon>
              恢复默认参数
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editorVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '创建智能体' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="agentManage">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import {
  Search,
  Plus,
  Edit,
  Delete,
  CopyDocument,
  ChatDotRound,
  Sort,
  InfoFilled,
  Document,
  Setting,
  MagicStick,
  RefreshLeft
} from "@element-plus/icons-vue";
import { Agent } from "@/api/interface";
import {
  getAgentList,
  createAgent,
  updateAgent,
  deleteAgent,
  changeAgentStatus,
  getPromptTemplates,
  getAvailableModels
} from "@/api/modules/agent";
import { useHandleData } from "@/hooks/useHandleData";

// ==================== 数据定义 ====================
const loading = ref(false);
const agentList = ref<Agent.ResAgentItem[]>([]);
const searchName = ref("");
const searchStatus = ref<Agent.StatusType | "">("");
const statusLoading = ref<string>("");

// 过滤后的智能体列表
const filteredAgents = computed(() => {
  return agentList.value.filter(agent => {
    const matchName = !searchName.value || agent.name.includes(searchName.value);
    const matchStatus = searchStatus.value === "" || agent.status === searchStatus.value;
    return matchName && matchStatus;
  });
});

// 编辑器相关
const editorVisible = ref(false);
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const modelList = ref<Array<{ id: string; name: string; model_id: string; provider: string; maxTokens: number }>>([]);
const promptTemplates = ref<Agent.PromptTemplate[]>([]);

// 默认配置参数
const defaultConfig: Agent.AgentConfig = {
  temperature: 0.7,
  maxTokens: 2048,
  topP: 0.9,
  frequencyPenalty: 0,
  presencePenalty: 0
};

// 表单数据
const formData = reactive<Agent.ReqAgentForm>({
  name: "",
  icon: "🤖",
  description: "",
  systemPrompt: "",
  model: "",
  config: { ...defaultConfig },
  sortOrder: 0,
  status: 1
});

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: "请输入智能体名称", trigger: "blur" },
    { min: 2, max: 20, message: "名称长度为 2-20 个字符", trigger: "blur" }
  ],
  model: [{ required: true, message: "请选择使用模型", trigger: "change" }],
  systemPrompt: [{ required: true, message: "请输入 System Prompt", trigger: "blur" }]
};

// Temperature 标记
const temperatureMarks = {
  0: "精确",
  1: "平衡",
  2: "创意"
};

// 表情列表
const emojiList = [
  "🤖", "💬", "🎯", "📚", "✍️", "🎨", "🔍", "💡",
  "🚀", "⚡", "🌟", "🎮", "📊", "🛠️", "🎭", "🧠",
  "💻", "📱", "🌐", "🔒", "📝", "🎓", "💼", "🏆"
];

// ==================== 方法定义 ====================

// 获取智能体列表
const fetchAgentList = async () => {
  loading.value = true;
  try {
    const { data } = await getAgentList();
    agentList.value = data?.list || [];
  } finally {
    loading.value = false;
  }
};

// 搜索处理
const handleSearch = () => {
  // 搜索由 computed 自动处理
};

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + "w";
  if (num >= 1000) return (num / 1000).toFixed(1) + "k";
  return num.toString();
};

// 打开编辑器
const openEditor = async (agent?: Agent.ResAgentItem) => {
  isEdit.value = !!agent;
  
  if (agent) {
    // 编辑模式
    Object.assign(formData, {
      id: agent.id,
      name: agent.name,
      icon: agent.icon,
      description: agent.description,
      systemPrompt: agent.systemPrompt,
      model: agent.model,
      config: { ...agent.config },
      sortOrder: agent.sortOrder,
      status: agent.status
    });
  } else {
    // 新建模式
    Object.assign(formData, {
      id: undefined,
      name: "",
      icon: "🤖",
      description: "",
      systemPrompt: "",
      model: modelList.value[0]?.id || "",
      config: { ...defaultConfig },
      sortOrder: agentList.value.length,
      status: 1
    });
  }
  
  editorVisible.value = true;
  formRef.value?.clearValidate();
};

// 应用预设模板
const applyTemplate = (template: Agent.PromptTemplate) => {
  ElMessageBox.confirm(
    "应用模板将覆盖当前的 System Prompt，是否继续？",
    "提示",
    { type: "warning" }
  ).then(() => {
    formData.systemPrompt = template.content;
    ElMessage.success(`已应用模板：${template.name}`);
  }).catch(() => {});
};

// 重置参数
const resetParams = () => {
  formData.config = { ...defaultConfig };
  ElMessage.success("参数已重置为默认值");
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate();
  submitLoading.value = true;
  
  try {
    if (isEdit.value) {
      await updateAgent(formData);
      ElMessage.success("保存成功");
    } else {
      await createAgent(formData);
      ElMessage.success("创建成功");
    }
    editorVisible.value = false;
    fetchAgentList();
  } finally {
    submitLoading.value = false;
  }
};

// 状态变更
const handleStatusChange = async (agent: Agent.ResAgentItem) => {
  const action = agent.status === 1 ? "上架" : "下架";
  
  try {
    statusLoading.value = agent.id;
    await changeAgentStatus(agent.id, agent.status);
    ElMessage.success(`${action}成功`);
  } catch {
    // 恢复原状态
    agent.status = agent.status === 1 ? 0 : 1;
  } finally {
    statusLoading.value = "";
  }
};

// 复制智能体
const duplicateAgent = (agent: Agent.ResAgentItem) => {
  Object.assign(formData, {
    id: undefined,
    name: agent.name + " (副本)",
    icon: agent.icon,
    description: agent.description,
    systemPrompt: agent.systemPrompt,
    model: agent.model,
    config: { ...agent.config },
    sortOrder: agentList.value.length,
    status: 0 // 默认下架
  });
  isEdit.value = false;
  editorVisible.value = true;
};

// 删除智能体
const handleDelete = async (agent: Agent.ResAgentItem) => {
  await useHandleData(deleteAgent, agent.id, `删除智能体【${agent.name}】`);
  fetchAgentList();
};

// 获取提供商名称
const getProviderName = (provider: string): string => {
  const nameMap: Record<string, string> = {
    openai: "OpenAI",
    anthropic: "Anthropic",
    deepseek: "DeepSeek"
  };
  return nameMap[provider] || provider;
};

// 获取模型列表和模板
const fetchInitData = async () => {
  try {
    const [modelsRes, templatesRes] = await Promise.all([
      getAvailableModels(),
      getPromptTemplates()
    ]);
    // 从数据库获取模型列表，兼容后端返回格式（可能缺少 model_id 和 provider）
    const models = modelsRes.data || [];
    modelList.value = models.map((model: any) => ({
      id: model.id,
      name: model.name,
      model_id: model.model_id || model.id,
      provider: model.provider || 'openai',
      maxTokens: model.maxTokens || model.max_tokens || 4096
    }));
    promptTemplates.value = templatesRes.data || [
      { id: "1", name: "客服助手", category: "客服", content: "你是一位专业的客服助手，请用友善专业的语气回答用户问题。\n\n职责：\n- 解答用户关于产品和服务的疑问\n- 处理用户投诉和反馈\n- 引导用户完成操作\n\n注意事项：\n- 保持耐心和礼貌\n- 回答要简洁明了\n- 遇到无法回答的问题，引导联系人工客服" },
      { id: "2", name: "文案写手", category: "创作", content: "你是一位专业的文案写手，擅长创作各类营销文案和内容。\n\n能力：\n- 产品描述和卖点提炼\n- 社交媒体文案\n- 广告标语和口号\n- 品牌故事撰写\n\n风格要求：\n- 语言生动有感染力\n- 突出产品价值和用户利益\n- 适应不同平台的内容风格" },
      { id: "3", name: "代码助手", category: "开发", content: "你是一位经验丰富的编程助手，精通多种编程语言和技术栈。\n\n能力范围：\n- 代码编写和优化\n- Bug 排查和修复\n- 技术方案设计\n- 代码审查建议\n\n回答要求：\n- 代码示例要完整可运行\n- 解释要清晰易懂\n- 遵循最佳实践和设计模式" },
      { id: "4", name: "数据分析师", category: "分析", content: "你是一位专业的数据分析师，擅长从数据中发现洞察和价值。\n\n专业领域：\n- 数据清洗和处理\n- 统计分析和建模\n- 数据可视化\n- 业务指标分析\n\n输出要求：\n- 分析结论要有数据支撑\n- 建议要具体可执行\n- 图表展示要清晰直观" }
    ];
  } catch (error) {
    console.error("Failed to fetch init data:", error);
  }
};

// ==================== 生命周期 ====================
onMounted(() => {
  fetchAgentList();
  fetchInitData();
});
</script>

<style scoped lang="scss">
.agent-manage-container {
  padding: 20px;
  min-height: 100%;
  background: var(--el-bg-color-page);
}

// 顶部操作栏
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);

  .left {
    display: flex;
    gap: 12px;
  }

  .search-input {
    width: 280px;
  }
}

// 卡片网格布局
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

// 智能体卡片
.agent-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 2px solid transparent;

  &:hover {
    border-color: var(--el-color-primary-light-5);
    transform: translateY(-4px);
  }

  &.is-offline {
    opacity: 0.7;

    .agent-icon {
      filter: grayscale(100%);
    }
  }

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.agent-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ff7700 0%, #ffb366 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .icon-emoji {
    font-size: 28px;
  }
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-model {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.card-body {
  margin-bottom: 16px;
}

.agent-description {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.agent-stats {
  display: flex;
  gap: 20px;

  .stat-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: var(--el-text-color-secondary);

    .el-icon {
      color: var(--el-color-primary);
    }
  }
}

.card-footer {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

// 列表动画
.card-list-enter-active,
.card-list-leave-active {
  transition: all 0.3s ease;
}

.card-list-enter-from,
.card-list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

// ==================== 编辑器对话框 ====================
.agent-editor-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
    height: calc(100vh - 120px);
    overflow: hidden;
  }
}

.editor-container {
  display: flex;
  height: 100%;
  background: var(--el-bg-color-page);
}

.editor-left,
.editor-center,
.editor-right {
  padding: 24px;
  overflow-y: auto;
}

.editor-left {
  width: 320px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
}

.editor-center {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-right {
  width: 360px;
  background: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-lighter);
}

.form-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);

  .el-icon {
    color: var(--el-color-primary);
  }

  .template-btn {
    margin-left: auto;
  }
}

// 图标选择器
.icon-picker {
  width: 100%;
}

.current-icon {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }
}

.icon-display {
  font-size: 32px;
}

.icon-hint {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}

.emoji-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 20px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: var(--el-color-primary-light-8);
  }

  &.active {
    background: var(--el-color-primary);
  }
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.model-provider {
  font-size: 12px;
  color: var(--el-color-primary);
  padding: 2px 6px;
  background: var(--el-color-primary-light-9);
  border-radius: 2px;
}

.model-tokens {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

// System Prompt 区域
.prompt-textarea {
  :deep(.el-textarea__inner) {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 14px;
    line-height: 1.6;
    padding: 16px;
    background: var(--el-bg-color);
    border-radius: 8px;
    min-height: 400px !important;
  }
}

.prompt-stats {
  margin-top: 8px;
  text-align: right;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

// 模板下拉
.template-item {
  display: flex;
  justify-content: space-between;
  width: 200px;
}

.template-name {
  font-weight: 500;
}

.template-category {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

// 参数配置
.param-item {
  margin-bottom: 28px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.param-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.param-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-color-primary);
  font-family: "DIN", sans-serif;
}

.param-desc {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  line-height: 1.4;
}

.reset-params-btn {
  width: 100%;
  margin-top: 16px;
}

// 对话框底部
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

// 响应式
@media (max-width: 1400px) {
  .editor-left {
    width: 280px;
  }
  .editor-right {
    width: 300px;
  }
}

@media (max-width: 1200px) {
  .editor-container {
    flex-direction: column;
  }
  
  .editor-left,
  .editor-center,
  .editor-right {
    width: 100%;
    border: none;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
}
</style>
