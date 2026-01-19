<template>
  <div class="skill-selector">
    <div class="selector-layout">
      <!-- 左侧：可选技能 -->
      <div class="available-skills">
        <div class="section-header">
          <span>可选技能</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索技能"
            clearable
            size="small"
            style="width: 200px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <el-tabs v-model="activeCategory" class="category-tabs">
          <el-tab-pane label="全部" name="all">
            <div class="skill-list">
              <div
                v-for="skill in filteredSkills"
                :key="skill.id"
                class="skill-item"
                @click="addSkill(skill)"
              >
                <el-tag :type="getCategoryType(skill.category)" size="small">
                  {{ skill.category }}
                </el-tag>
                <span class="skill-name">{{ skill.name }}</span>
                <el-icon class="add-icon"><Plus /></el-icon>
              </div>
              <el-empty v-if="filteredSkills.length === 0" description="暂无技能" :image-size="80" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="Model" name="model">
            <div class="skill-list">
              <div
                v-for="skill in filteredSkills"
                :key="skill.id"
                class="skill-item"
                @click="addSkill(skill)"
              >
                <el-tag type="primary" size="small">Model</el-tag>
                <span class="skill-name">{{ skill.name }}</span>
                <el-icon class="add-icon"><Plus /></el-icon>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="Hook" name="hook">
            <div class="skill-list">
              <div
                v-for="skill in filteredSkills"
                :key="skill.id"
                class="skill-item"
                @click="addSkill(skill)"
              >
                <el-tag type="success" size="small">Hook</el-tag>
                <span class="skill-name">{{ skill.name }}</span>
                <el-icon class="add-icon"><Plus /></el-icon>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="Rule" name="rule">
            <div class="skill-list">
              <div
                v-for="skill in filteredSkills"
                :key="skill.id"
                class="skill-item"
                @click="addSkill(skill)"
              >
                <el-tag type="warning" size="small">Rule</el-tag>
                <span class="skill-name">{{ skill.name }}</span>
                <el-icon class="add-icon"><Plus /></el-icon>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="Audit" name="audit">
            <div class="skill-list">
              <div
                v-for="skill in filteredSkills"
                :key="skill.id"
                class="skill-item"
                @click="addSkill(skill)"
              >
                <el-tag type="danger" size="small">Audit</el-tag>
                <span class="skill-name">{{ skill.name }}</span>
                <el-icon class="add-icon"><Plus /></el-icon>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧：已选技能（支持拖拽） -->
      <div class="selected-skills">
        <div class="section-header">
          <span>已挂载技能</span>
          <el-badge :value="selectedSkills.length" type="primary" />
        </div>

        <div class="skill-list">
          <draggable
            v-model="selectedSkillsList"
            item-key="id"
            @end="handleDragEnd"
            class="draggable-list"
          >
            <template #item="{ element, index }">
              <div class="skill-item selected">
                <el-icon class="drag-handle"><Rank /></el-icon>
                <el-tag :type="getCategoryType(element.category)" size="small">
                  {{ element.category }}
                </el-tag>
                <span class="skill-name">{{ element.name }}</span>
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click.stop="configureVariables(element.id)"
                >
                  配置变量
                </el-button>
                <el-icon class="remove-icon" @click="removeSkill(index)"><Close /></el-icon>
              </div>
            </template>
          </draggable>
          <el-empty v-if="selectedSkillsList.length === 0" description="尚未选择技能" :image-size="80" />
        </div>
      </div>
    </div>

    <!-- 变量配置弹窗 -->
    <el-dialog v-model="variableDialogVisible" title="配置技能变量" width="600px">
      <el-form label-width="120px">
        <el-alert
          title="提示"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          为该技能配置变量值。Prompt中的 {{变量名}} 将被替换为实际的值。
        </el-alert>

        <el-form-item
          v-for="(value, key) in currentSkillVariables"
          :key="key"
          :label="key"
        >
          <el-input v-model="currentSkillVariables[key]" :placeholder="`请输入${key}`" />
        </el-form-item>

        <el-empty v-if="Object.keys(currentSkillVariables).length === 0" description="该技能无需配置变量" />
      </el-form>

      <template #footer>
        <el-button @click="variableDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveVariables" v-if="Object.keys(currentSkillVariables).length > 0">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Search, Plus, Close, Rank } from "@element-plus/icons-vue";
import draggable from "vuedraggable";
import { getSkillList } from "@/api/modules/skillAssembly";
import { Skill } from "@/api/interface";

interface Props {
  modelValue: number[];
  variables?: Record<number, Record<string, string>>;
}

interface Emits {
  (e: "update:modelValue", value: number[]): void;
  (e: "update:variables", value: Record<number, Record<string, string>>): void;
  (e: "change", skills: any[]): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const allSkills = ref<Skill.ResSkillItem[]>([]);
const searchKeyword = ref("");
const activeCategory = ref("all");
const variableDialogVisible = ref(false);
const currentSkillId = ref<number | null>(null);
const currentSkillVariables = ref<Record<string, string>>({});

const selectedSkillsList = ref<any[]>([]);

// 加载技能列表
const loadSkills = async () => {
  try {
    const response = await getSkillList({ page: 1, size: 100, status: 1 });
    allSkills.value = response.data.list;
  } catch (error) {
    console.error("加载技能列表失败:", error);
    ElMessage.error("加载技能列表失败");
  }
};

// 过滤技能
const filteredSkills = computed(() => {
  let skills = allSkills.value;

  // 分类过滤
  if (activeCategory.value !== "all") {
    skills = skills.filter(s => s.category === activeCategory.value);
  }

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    skills = skills.filter(s =>
      s.name.toLowerCase().includes(keyword) ||
      (s.meta_description && s.meta_description.toLowerCase().includes(keyword))
    );
  }

  // 排除已选
  const selectedIds = props.modelValue || [];
  return skills.filter(s => !selectedIds.includes(s.id));
});

// 添加技能
const addSkill = (skill: Skill.ResSkillItem) => {
  const newIds = [...(props.modelValue || []), skill.id];
  emit("update:modelValue", newIds);

  selectedSkillsList.value = allSkills.value.filter(s => newIds.includes(s.id));
  emit("change", selectedSkillsList.value);
};

// 移除技能
const removeSkill = (index: number) => {
  const newIds = props.modelValue.filter((_, i) => i !== index);
  emit("update:modelValue", newIds);

  selectedSkillsList.value = allSkills.value.filter(s => newIds.includes(s.id));
  emit("change", selectedSkillsList.value);
};

// 拖拽结束
const handleDragEnd = () => {
  const newIds = selectedSkillsList.value.map(s => s.id);
  emit("update:modelValue", newIds);
  emit("change", selectedSkillsList.value);
};

// 配置变量
const configureVariables = (skillId: number) => {
  currentSkillId.value = skillId;

  // 从父组件获取已有的变量配置
  const existingVars = props.variables?.[skillId] || {};
  currentSkillVariables.value = { ...existingVars };

  // 解析技能内容，提取变量（简单的正则匹配）
  const skill = allSkills.value.find(s => s.id === skillId);
  if (skill) {
    const varPattern = /\{\{([^}]+)\}\}/g;
    const matches = skill.content.match(varPattern);
    if (matches) {
      const varNames = matches.map(m => m.replace(/\{\{|\}\}/g, '').trim());
      varNames.forEach(varName => {
        if (!(varName in currentSkillVariables.value)) {
          currentSkillVariables.value[varName] = "";
        }
      });
    }
  }

  variableDialogVisible.value = true;
};

// 保存变量
const saveVariables = () => {
  if (currentSkillId.value === null) return;

  const newVariables = {
    ...(props.variables || {}),
    [currentSkillId.value!]: { ...currentSkillVariables.value }
  };

  emit("update:variables", newVariables);
  variableDialogVisible.value = false;
  ElMessage.success("变量保存成功");
};

// 获取分类标签类型
const getCategoryType = (category: string) => {
  const typeMap: Record<string, any> = {
    model: "primary",
    hook: "success",
    rule: "warning",
    audit: "danger"
  };
  return typeMap[category] || "";
};

// 监听外部变化
watch(
  () => props.modelValue,
  (newIds) => {
    if (newIds && newIds.length > 0) {
      selectedSkillsList.value = allSkills.value
        .filter(s => newIds.includes(s.id))
        .sort((a, b) => newIds.indexOf(a.id) - newIds.indexOf(b.id));
    } else {
      selectedSkillsList.value = [];
    }
  },
  { immediate: true }
);

// 初始化
onMounted(() => {
  loadSkills();
});
</script>

<style scoped lang="scss">
.skill-selector {
  .selector-layout {
    display: flex;
    gap: 20px;
    height: 500px;
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    padding: 16px;
  }

  .available-skills,
  .selected-skills {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-weight: bold;
  }

  .skill-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;

    .skill-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      margin-bottom: 8px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      .skill-name {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .add-icon {
        color: var(--el-color-primary);
      }

      .remove-icon {
        color: var(--el-color-danger);
        cursor: pointer;

        &:hover {
          color: var(--el-color-danger-dark-2);
        }
      }

      &.selected {
        background-color: var(--el-fill-color);
        cursor: move;

        &:hover {
          background-color: var(--el-fill-color-dark);
        }
      }

      .drag-handle {
        cursor: move;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .category-tabs {
    display: flex;
    flex-direction: column;
    height: 100%;

    :deep(.el-tabs__content) {
      flex: 1;
      overflow-y: auto;
    }
  }

  .draggable-list {
    min-height: 100px;
  }
}
</style>
