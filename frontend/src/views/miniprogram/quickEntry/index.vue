<template>
  <div class="quick-entry-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">快捷入口配置</span>
          <div class="header-actions">
            <el-button type="success" :icon="Sort" @click="openSortDialog">批量排序</el-button>
            <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增快捷入口</el-button>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select v-model="filterType" placeholder="全部类型" clearable style="width: 150px" @change="loadEntries">
          <el-option label="今天拍点啥" value="category" />
          <el-option label="快捷指令库" value="command" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 150px; margin-left: 10px" @change="loadEntries">
          <el-option label="启用" :value="1" />
          <el-option label="禁用" :value="0" />
          <el-option label="即将上线" :value="2" />
        </el-select>
        <el-input
          v-model="searchTitle"
          placeholder="搜索标题"
          clearable
          style="width: 200px; margin-left: 10px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 手机预览区域 -->
      <div class="preview-section">
        <!-- 今天拍点啥 -->
        <div class="preview-group">
          <div class="group-header">
            <h3>今天拍点啥</h3>
            <el-tag type="success" size="small">{{ categoryEntries.length }} 个</el-tag>
          </div>
          <div class="entry-grid">
            <div
              v-for="entry in categoryEntries"
              :key="entry.id"
              class="entry-card"
              :class="{ disabled: entry.status !== 1 }"
            >
              <div class="card-content">
                <div class="card-icon"  :style="{ backgroundColor: entry.bg_color || '#f5f7fa' }">
                  <i :class="entry.icon_class"></i>
                </div>
                <div class="card-info">
                  <div class="card-title-row">
                    <span class="card-title-text">{{ entry.title }}</span>
                    <el-tag v-if="entry.tag === 'new'" type="success" size="small">新</el-tag>
                    <el-tag v-else-if="entry.tag === 'hot'" type="danger" size="small">热</el-tag>
                  </div>
                  <div v-if="entry.subtitle" class="card-subtitle">{{ entry.subtitle }}</div>
                </div>
              </div>
              <div class="card-actions">
                <el-switch
                  v-model="entry.status"
                  :active-value="1"
                  :inactive-value="0"
                  :loading="statusLoading === entry.id"
                  @change="handleStatusChange(entry)"
                />
                <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', entry)">编辑</el-button>
                <el-button type="danger" link :icon="Delete" @click="deleteEntry(entry)">删除</el-button>
              </div>
            </div>
            <div v-if="categoryEntries.length === 0" class="empty-card">
              <el-empty description="暂无数据" :image-size="80" />
            </div>
          </div>
        </div>

        <!-- 快捷指令库 -->
        <div class="preview-group">
          <div class="group-header">
            <h3>快捷指令库</h3>
            <el-tag type="primary" size="small">{{ commandEntries.length }} 个</el-tag>
          </div>
          <div class="entry-grid">
            <div
              v-for="entry in commandEntries"
              :key="entry.id"
              class="entry-card"
              :class="{ disabled: entry.status !== 1 }"
            >
              <div class="card-content" >
                <div class="card-icon" :style="{ backgroundColor: entry.bg_color || '#f5f7fa' }">
                  <i :class="entry.icon_class"></i>
                </div>
                <div class="card-info">
                  <div class="card-title-row">
                    <span class="card-title-text">{{ entry.title }}</span>
                    <el-tag v-if="entry.tag === 'new'" type="success" size="small">新</el-tag>
                    <el-tag v-else-if="entry.tag === 'hot'" type="danger" size="small">热</el-tag>
                  </div>
                  <div v-if="entry.subtitle" class="card-subtitle">{{ entry.subtitle }}</div>
                </div>
              </div>
              <div class="card-actions">
                <el-switch
                  v-model="entry.status"
                  :active-value="1"
                  :inactive-value="0"
                  :loading="statusLoading === entry.id"
                  @change="handleStatusChange(entry)"
                />
                <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', entry)">编辑</el-button>
                <el-button type="danger" link :icon="Delete" @click="deleteEntry(entry)">删除</el-button>
              </div>
            </div>
            <div v-if="commandEntries.length === 0" class="empty-card">
              <el-empty description="暂无数据" :image-size="80" />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="700px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-divider content-position="left">基础信息</el-divider>
        
        <el-form-item label="入口类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择入口类型" style="width: 100%" :disabled="isEdit">
            <el-option label="今天拍点啥" value="category" />
            <el-option label="快捷指令库" value="command" />
          </el-select>
        </el-form-item>

        <el-form-item label="唯一标识" prop="unique_key">
          <el-input
            v-model="formData.unique_key"
            placeholder="请输入唯一标识（如：story, opinion, agent_001）"
            maxlength="64"
            show-word-limit
            :disabled="isEdit"
          />
          <div class="form-tip">创建后不可修改，用于系统内部识别</div>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入标题" maxlength="128" show-word-limit />
        </el-form-item>

        <el-form-item label="副标题" prop="subtitle">
          <el-input
            v-model="formData.subtitle"
            type="textarea"
            :rows="2"
            placeholder="请输入副标题（描述信息）"
            maxlength="256"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="图标类名" prop="icon_class">
          <el-input
            v-model="formData.icon_class"
            placeholder="请输入RemixIcon类名（如：ri-book-line）"
            maxlength="64"
            show-word-limit
          >
            <template #prefix>
              <i v-if="formData.icon_class" :class="formData.icon_class" style="font-size: 18px"></i>
            </template>
          </el-input>
          <div class="form-tip">
            推荐使用 RemixIcon，访问：
            <el-link href="https://remixicon.com/" target="_blank" type="primary">https://remixicon.com/</el-link>
          </div>
        </el-form-item>

        <el-form-item label="背景色" prop="bg_color">
          <el-color-picker v-model="formData.bg_color" show-alpha />
          <el-input
            v-model="formData.bg_color"
            placeholder="#F69C0E"
            maxlength="16"
            style="width: 200px; margin-left: 10px"
          />
          <div class="form-tip">十六进制颜色值，如：#F69C0E</div>
        </el-form-item>

        <el-divider content-position="left">动作配置</el-divider>

        <el-form-item label="动作类型" prop="action_type">
          <el-select v-model="formData.action_type" placeholder="请选择动作类型" style="width: 100%" @change="handleActionTypeChange">
            <el-option label="调用Agent" value="agent" />
            <el-option label="调用Skill" value="skill" />
            <el-option label="硬编码Prompt" value="prompt" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="formData.action_type === 'agent'" label="选择Agent" prop="action_value">
          <el-select
            v-model="formData.action_value"
            placeholder="请选择Agent"
            style="width: 100%"
            filterable
            :loading="agentLoading"
            @focus="loadAgents"
          >
            <el-option
              v-for="agent in agentList"
              :key="agent.id"
              :label="`${agent.name} (${agent.id})`"
              :value="String(agent.id)"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="formData.action_type === 'skill'" label="选择Skill" prop="action_value">
          <el-select
            v-model="formData.action_value"
            placeholder="请选择Skill"
            style="width: 100%"
            filterable
            :loading="skillLoading"
            @focus="loadSkills"
          >
            <el-option
              v-for="skill in skillList"
              :key="skill.id"
              :label="`${skill.name} (${skill.id})`"
              :value="String(skill.id)"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="formData.action_type === 'prompt'" label="Prompt内容" prop="action_value">
          <el-input
            v-model="formData.action_value"
            type="textarea"
            :rows="6"
            placeholder="请输入System Prompt文本"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-divider content-position="left">其他配置</el-divider>

        <el-form-item label="标签" prop="tag">
          <el-select v-model="formData.tag" placeholder="请选择标签" style="width: 100%">
            <el-option label="无标签" value="none" />
            <el-option label="新上线" value="new" />
            <el-option label="最热门" value="hot" />
          </el-select>
        </el-form-item>

        <el-form-item label="排序权重" prop="priority">
          <el-input-number v-model="formData.priority" :min="0" :max="9999" style="width: 100%" />
          <div class="form-tip">数字越小越靠前，相同数字按创建时间排序</div>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="禁用" :value="0" />
            <el-option label="启用" :value="1" />
            <el-option label="即将上线" :value="2" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>

    <!-- 排序对话框 -->
    <el-dialog v-model="showSortDialog" title="批量排序" width="600px">
      <div class="sort-tip">拖拽列表项调整顺序，数字越小越靠前</div>
      <el-table :data="sortList" row-key="id" style="margin-top: 20px">
        <el-table-column type="index" label="序号" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.type === 'category' ? 'success' : 'primary'" effect="plain">
              {{ scope.row.type === 'category' ? '今天拍点啥' : '快捷指令库' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="当前权重" width="120" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button
              v-if="scope.$index > 0"
              type="primary"
              link
              :icon="ArrowUp"
              @click="moveUp(scope.$index)"
            />
            <el-button
              v-if="scope.$index < sortList.length - 1"
              type="primary"
              link
              :icon="ArrowDown"
              @click="moveDown(scope.$index)"
            />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showSortDialog = false">取消</el-button>
        <el-button type="primary" :loading="sortLoading" @click="handleSortSubmit">保存排序</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="quickEntryManage">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Sort, ArrowUp, ArrowDown, Search } from "@element-plus/icons-vue";
import type { QuickEntryItem, QuickEntryParams, QuickEntryCreate, QuickEntryUpdate } from "@/api/modules/quickEntry";
import { useHandleData } from "@/hooks/useHandleData";
import {
  getQuickEntryList,
  getQuickEntryDetail,
  createQuickEntry,
  updateQuickEntry,
  deleteQuickEntry as deleteQuickEntryApi,
  updateQuickEntryStatus,
  updateQuickEntrySort
} from "@/api/modules/quickEntry";
import { getAgentList } from "@/api/modules/agent";
import { getSkillList } from "@/api/modules/skillAssembly";

// 数据
const entryList = ref<QuickEntryItem[]>([]);
const loading = ref(false);
const filterType = ref<string>("");
const filterStatus = ref<number | null>(null);
const searchTitle = ref("");

// 抽屉相关
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const statusLoading = ref<number | null>(null);

// 排序对话框
const showSortDialog = ref(false);
const sortLoading = ref(false);
const sortList = ref<QuickEntryItem[]>([]);

// Agent和Skill列表
const agentList = ref<Array<{ id: number; name: string }>>([]);
const skillList = ref<Array<{ id: number; name: string }>>([]);
const agentLoading = ref(false);
const skillLoading = ref(false);

// 表单数据
const formData = reactive<QuickEntryCreate & { id?: number }>({
  unique_key: "",
  type: "category",
  title: "",
  subtitle: "",
  icon_class: "",
  bg_color: "",
  action_type: "agent",
  action_value: "",
  tag: "none",
  priority: 0,
  status: 1
});

// 表单验证规则
const formRules: FormRules = {
  unique_key: [{ required: true, message: "请输入唯一标识", trigger: "blur" }],
  type: [{ required: true, message: "请选择入口类型", trigger: "change" }],
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
  icon_class: [{ required: true, message: "请输入图标类名", trigger: "blur" }],
  action_type: [{ required: true, message: "请选择动作类型", trigger: "change" }],
  action_value: [
    {
      required: true,
      message: "请填写动作值",
      trigger: "blur",
      validator: (rule, value, callback) => {
        if (!value || value.trim() === "") {
          callback(new Error("请填写动作值"));
        } else {
          callback();
        }
      }
    }
  ]
};

const formRef = ref<FormInstance>();

// 计算属性：分类后的入口列表
const categoryEntries = computed(() => {
  return entryList.value
    .filter((item) => item.type === "category")
    .filter((item) => !filterStatus.value || item.status === filterStatus.value)
    .filter((item) => !searchTitle.value || item.title.includes(searchTitle.value))
    .sort((a, b) => a.priority - b.priority);
});

const commandEntries = computed(() => {
  return entryList.value
    .filter((item) => item.type === "command")
    .filter((item) => !filterStatus.value || item.status === filterStatus.value)
    .filter((item) => !searchTitle.value || item.title.includes(searchTitle.value))
    .sort((a, b) => a.priority - b.priority);
});

// 加载数据
const loadEntries = async () => {
  loading.value = true;
  try {
    const params: QuickEntryParams = {
      pageNum: 1,
      pageSize: 1000,
      type: filterType.value || undefined,
      status: filterStatus.value || undefined,
      title: searchTitle.value || undefined
    };
    const response = await getQuickEntryList(params);
    if (response.code === 200 && response.data) {
      entryList.value = response.data.list || response.data.items || [];
    } else {
      ElMessage.error(response.msg || "加载失败");
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载失败");
  } finally {
    loading.value = false;
  }
};

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout> | null = null;
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    loadEntries();
  }, 500);
};

// 打开抽屉
const openDrawer = async (title: string, row?: QuickEntryItem) => {
  drawerTitle.value = title;
  isEdit.value = !!row;

  if (row) {
    // 编辑模式：获取详情（确保id是数字类型）
    try {
      const entryId = typeof row.id === 'string' ? parseInt(row.id, 10) : row.id;
      if (isNaN(entryId)) {
        ElMessage.error("无效的入口ID");
        return;
      }
      const response = await getQuickEntryDetail(entryId);
      if (response.code === 200 && response.data) {
        Object.assign(formData, {
          id: response.data.id,
          unique_key: response.data.unique_key,
          type: response.data.type,
          title: response.data.title,
          subtitle: response.data.subtitle || "",
          icon_class: response.data.icon_class,
          bg_color: response.data.bg_color || "",
          action_type: response.data.action_type,
          action_value: response.data.action_value,
          tag: response.data.tag,
          priority: response.data.priority,
          status: response.data.status
        });
      }
    } catch (error: any) {
      ElMessage.error(error?.msg || "获取详情失败");
      return;
    }
  } else {
    // 新增模式：重置表单
    Object.assign(formData, {
      id: undefined,
      unique_key: "",
      type: "category",
      title: "",
      subtitle: "",
      icon_class: "",
      bg_color: "",
      action_type: "agent",
      action_value: "",
      tag: "none",
      priority: 0,
      status: 1
    });
  }

  drawerVisible.value = true;
};

// 动作类型改变时清空动作值
const handleActionTypeChange = () => {
  formData.action_value = "";
};

// 加载Agent列表
const loadAgents = async () => {
  if (agentList.value.length > 0) return;
  agentLoading.value = true;
  try {
    const response = await getAgentList({ pageNum: 1, pageSize: 1000 });
    if (response.code === 200 && response.data) {
      agentList.value = (response.data.list || []).map((item: any) => ({
        id: Number(item.id),
        name: item.name || ""
      }));
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载Agent列表失败");
  } finally {
    agentLoading.value = false;
  }
};

// 加载Skill列表
const loadSkills = async () => {
  if (skillList.value.length > 0) return;
  skillLoading.value = true;
  try {
    const response = await getSkillList({ page: 1, size: 1000 });
    if (response.code === 200 && response.data) {
      skillList.value = (response.data.list || []).map((item: any) => ({
        id: item.id,
        name: item.name || ""
      }));
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载Skill列表失败");
  } finally {
    skillLoading.value = false;
  }
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        const params: QuickEntryCreate | QuickEntryUpdate = {
          unique_key: formData.unique_key,
          type: formData.type,
          title: formData.title,
          subtitle: formData.subtitle || undefined,
          icon_class: formData.icon_class,
          bg_color: formData.bg_color || undefined,
          action_type: formData.action_type,
          action_value: formData.action_value,
          tag: formData.tag,
          priority: formData.priority,
          status: formData.status
        };

        if (isEdit.value && formData.id) {
          await updateQuickEntry(formData.id, params);
          ElMessage.success("更新成功");
        } else {
          await createQuickEntry(params as QuickEntryCreate);
          ElMessage.success("创建成功");
        }

        drawerVisible.value = false;
        await loadEntries();
      } catch (error: any) {
        ElMessage.error(error?.msg || "操作失败");
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

// 删除快捷入口
const deleteEntry = async (row: QuickEntryItem) => {
  await useHandleData(deleteQuickEntryApi, row.id, `删除快捷入口 "${row.title}"`).then(() => {
    loadEntries();
  });
};

// 状态切换
const handleStatusChange = async (row: QuickEntryItem) => {
  statusLoading.value = row.id;
  try {
    await updateQuickEntryStatus(row.id, row.status);
    ElMessage.success(row.status === 1 ? "已启用" : "已禁用");
  } catch (error: any) {
    row.status = row.status === 1 ? 0 : 1; // 回滚状态
    ElMessage.error(error?.msg || "操作失败");
  } finally {
    statusLoading.value = null;
  }
};

// 打开排序对话框
const openSortDialog = async () => {
  try {
    const response = await getQuickEntryList({ pageNum: 1, pageSize: 1000 });
    if (response.code === 200 && response.data) {
      sortList.value = (response.data.list || response.data.items || []).sort(
        (a: QuickEntryItem, b: QuickEntryItem) => a.priority - b.priority
      );
      showSortDialog.value = true;
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "加载数据失败");
  }
};

// 上移
const moveUp = (index: number) => {
  if (index > 0) {
    const temp = sortList.value[index];
    sortList.value[index] = sortList.value[index - 1];
    sortList.value[index - 1] = temp;
  }
};

// 下移
const moveDown = (index: number) => {
  if (index < sortList.value.length - 1) {
    const temp = sortList.value[index];
    sortList.value[index] = sortList.value[index + 1];
    sortList.value[index + 1] = temp;
  }
};

// 提交排序
const handleSortSubmit = async () => {
  sortLoading.value = true;
  try {
    const items = sortList.value.map((item, index) => ({
      id: item.id,
      priority: index
    }));

    await updateQuickEntrySort(items);
    ElMessage.success("排序更新成功");
    showSortDialog.value = false;
    await loadEntries();
  } catch (error: any) {
    ElMessage.error(error?.msg || "排序更新失败");
  } finally {
    sortLoading.value = false;
  }
};

onMounted(() => {
  loadEntries();
});
</script>

<style scoped lang="scss">
.quick-entry-container {
  padding: 20px;
}

.config-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      font-size: 18px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color);
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.preview-group {
  .group-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.entry-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }

  &.disabled {
    opacity: 0.6;
  }

  .card-content {
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 80px;

    .card-icon {
      flex-shrink: 0;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.8);
      border-radius: 8px;

      i {
        font-size: 24px;
        color: var(--el-color-primary);
      }
    }

    .card-info {
      flex: 1;
      min-width: 0;

      .card-title-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;

        .card-title-text {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .card-subtitle {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .card-actions {
    padding: 12px 16px;
    border-top: 1px solid var(--el-border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--el-bg-color-page);
  }
}

.empty-card {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color-page);
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.5;
}

.sort-tip {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
}

:deep(.el-divider) {
  margin: 20px 0 15px 0;
}
</style>
