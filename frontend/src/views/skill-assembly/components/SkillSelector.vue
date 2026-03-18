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

        <el-tabs v-model="activeCategory" class="category-tabs" @tab-change="handleCategoryChange">
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
              <el-empty v-if="filteredSkills.length === 0 && !loading" description="暂无技能" :image-size="80" />
            </div>
            <div v-if="pagination.total > pagination.size" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="pagination.page"
                :page-size="pagination.size"
                :total="pagination.total"
                layout="prev, pager, next"
                small
                @current-change="handlePageChange"
              />
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
              <el-empty v-if="filteredSkills.length === 0 && !loading" description="暂无技能" :image-size="80" />
            </div>
            <div v-if="pagination.total > pagination.size" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="pagination.page"
                :page-size="pagination.size"
                :total="pagination.total"
                layout="prev, pager, next"
                small
                @current-change="handlePageChange"
              />
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
              <el-empty v-if="filteredSkills.length === 0 && !loading" description="暂无技能" :image-size="80" />
            </div>
            <div v-if="pagination.total > pagination.size" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="pagination.page"
                :page-size="pagination.size"
                :total="pagination.total"
                layout="prev, pager, next"
                small
                @current-change="handlePageChange"
              />
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
              <el-empty v-if="filteredSkills.length === 0 && !loading" description="暂无技能" :image-size="80" />
            </div>
            <div v-if="pagination.total > pagination.size" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="pagination.page"
                :page-size="pagination.size"
                :total="pagination.total"
                layout="prev, pager, next"
                small
                @current-change="handlePageChange"
              />
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
              <el-empty v-if="filteredSkills.length === 0 && !loading" description="暂无技能" :image-size="80" />
            </div>
            <div v-if="pagination.total > pagination.size" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="pagination.page"
                :page-size="pagination.size"
                :total="pagination.total"
                layout="prev, pager, next"
                small
                @current-change="handlePageChange"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧：已选技能（支持拖拽） -->
      <div class="selected-skills">
        <div class="section-header">
          <span>已挂载技能</span>
          <el-badge :value="selectedSkillsList.length" type="primary" />
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
import { ref, reactive, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Search, Plus, Close, Rank } from "@element-plus/icons-vue";
import draggable from "vuedraggable";
import { getSkillList, getSkillDetail } from "@/api/modules/skillAssembly";
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
const skillCache = ref<Map<number, Skill.ResSkillItem>>(new Map()); // 缓存已加载技能，用于回填已选项
const searchKeyword = ref("");
const activeCategory = ref("all");
const loading = ref(false);
const variableDialogVisible = ref(false);
const currentSkillId = ref<number | null>(null);
const currentSkillVariables = ref<Record<string, string>>({});

const selectedSkillsList = ref<any[]>([]);

const pagination = reactive({
  page: 1,
  size: 100,
  total: 0
});

// 同步已选技能列表（用于编辑时回填，从 skillCache + allSkills 获取）
const syncSelectedSkills = () => {
  const ids = props.modelValue || [];
  if (ids.length === 0) {
    selectedSkillsList.value = [];
    return;
  }
  const cache = skillCache.value;
  const current = allSkills.value || [];
  selectedSkillsList.value = ids
    .map(id => cache.get(id) ?? current.find(s => s.id === id))
    .filter(Boolean)
    .sort((a, b) => ids.indexOf(a!.id) - ids.indexOf(b!.id));
};

// 加载技能列表（分页，size=100）
const loadSkills = async () => {
  loading.value = true;
  try {
    const params: { page: number; size: number; status: number; category?: string } = {
      page: pagination.page,
      size: pagination.size,
      status: 1
    };
    if (activeCategory.value !== "all") {
      params.category = activeCategory.value;
    }
    const response = await getSkillList(params);
    const list = response.data.list || [];
    allSkills.value = list;
    pagination.total = response.data.total ?? 0;
    // 写入缓存
    list.forEach((s: Skill.ResSkillItem) => skillCache.value.set(s.id, s));
    syncSelectedSkills();
    // 编辑时：已选技能可能不在当前页，需单独拉取
    fetchMissingSelectedSkills();
  } catch (error) {
    console.error("加载技能列表失败:", error);
    ElMessage.error("加载技能列表失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  loadSkills();
};

const handleCategoryChange = () => {
  pagination.page = 1;
  loadSkills();
};

// 编辑时拉取不在当前页的已选技能
const fetchMissingSelectedSkills = async () => {
  const ids = props.modelValue || [];
  const missing = ids.filter(id => !skillCache.value.has(id));
  if (missing.length === 0) return;
  for (const id of missing) {
    try {
      const res = await getSkillDetail(id);
      if (res.data) skillCache.value.set(id, res.data);
    } catch {
      // 技能可能已删除，忽略
    }
  }
  syncSelectedSkills();
};

// 过滤技能（分类由后端分页处理，此处仅做搜索过滤和排除已选）
const filteredSkills = computed(() => {
  let skills = allSkills.value || [];

  // 搜索过滤（当前页内）
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
  skillCache.value.set(skill.id, skill);
  const newIds = [...(props.modelValue || []), skill.id];
  emit("update:modelValue", newIds);

  selectedSkillsList.value = newIds
    .map(id => skillCache.value.get(id) ?? allSkills.value?.find(s => s.id === id))
    .filter(Boolean)
    .sort((a, b) => newIds.indexOf(a!.id) - newIds.indexOf(b!.id));
  emit("change", selectedSkillsList.value);
};

// 移除技能
const removeSkill = (index: number) => {
  const currentIds = props.modelValue || [];
  const newIds = currentIds.filter((_, i) => i !== index);
  emit("update:modelValue", newIds);

  selectedSkillsList.value = newIds
    .map(id => skillCache.value.get(id) ?? allSkills.value?.find(s => s.id === id))
    .filter(Boolean)
    .sort((a, b) => newIds.indexOf(a!.id) - newIds.indexOf(b!.id));
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

  // 解析技能内容，提取变量（从缓存或当前页查找）
  const skill = skillCache.value.get(skillId) ?? allSkills.value.find(s => s.id === skillId);
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

// 监听 modelValue 变化（编辑时父组件传入 skillIds/skill_ids 后触发回填）
watch(
  () => props.modelValue,
  () => syncSelectedSkills(),
  { immediate: true }
);

// 监听 allSkills 变化（技能列表加载完成后补充回填，解决异步加载时序问题）
watch(
  () => allSkills.value,
  () => syncSelectedSkills()
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
    min-width: 500px;
    min-height: 0; /* flex 子项需设置，否则 overflow 无法正确滚动 */
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
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
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
    flex: 1;
    min-height: 0;
    overflow: hidden;

    :deep(.el-tabs__header) {
      flex-shrink: 0;
    }

    :deep(.el-tabs__content) {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
    }

    :deep(.el-tab-pane) {
      height: 100%;
    }
  }

  .draggable-list {
    min-height: 100px;
  }

  .pagination-wrapper {
    flex-shrink: 0;
    padding: 8px 0;
    display: flex;
    justify-content: center;
  }
}
</style>
