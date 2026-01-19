<template>
  <div class="skill-library">
    <el-card>
      <!-- 页面标题 -->
      <template #header>
        <div class="card-header">
          <span class="title">技能库管理</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">新增技能</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" class="search-form">
        <el-form-item label="技能分类">
          <el-select v-model="searchForm.category" placeholder="全部分类" clearable style="width: 200px">
            <el-option label="全部分类" value="" />
            <el-option label="Model" value="model" />
            <el-option label="Hook" value="hook" />
            <el-option label="Rule" value="rule" />
            <el-option label="Audit" value="audit" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="全部状态" :value="null" />
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="fetchSkills">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 技能列表 -->
      <el-table :data="skillList" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="技能名称" min-width="150" />
        <el-table-column prop="category" label="分类" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="meta_description" label="特征描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="content" label="内容预览" min-width="250" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="fetchSkills"
        @size-change="fetchSkills"
        class="pagination"
      />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <SkillEditor
      v-model:visible="editorVisible"
      :skill-data="currentSkill"
      @submit="handleEditorSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search, Refresh, Edit, Delete } from "@element-plus/icons-vue";
import { getSkillList, deleteSkill } from "@/api/modules/skillAssembly";
import { Skill } from "@/api/interface";
import SkillEditor from "./components/SkillEditor.vue";

// 数据定义
const loading = ref(false);
const skillList = ref<Skill.ResSkillItem[]>([]);
const editorVisible = ref(false);
const currentSkill = ref<Skill.ResSkillItem | null>(null);

const searchForm = reactive({
  category: "",
  status: null as number | null
});

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
});

// 获取技能列表
const fetchSkills = async () => {
  loading.value = true;
  try {
    const response = await getSkillList({
      page: pagination.page,
      size: pagination.size,
      category: searchForm.category || undefined,
      status: searchForm.status ?? undefined
    });
    skillList.value = response.data.list;
    pagination.total = response.data.total;
  } catch (error) {
    console.error("获取技能列表失败:", error);
    ElMessage.error("获取技能列表失败");
  } finally {
    loading.value = false;
  }
};

// 重置搜索
const resetSearch = () => {
  searchForm.category = "";
  searchForm.status = null;
  pagination.page = 1;
  fetchSkills();
};

// 显示创建弹窗
const handleCreate = () => {
  currentSkill.value = null;
  editorVisible.value = true;
};

// 编辑技能
const handleEdit = (skill: Skill.ResSkillItem) => {
  currentSkill.value = { ...skill };
  editorVisible.value = true;
};

// 删除技能
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm("确定删除该技能吗？删除后将无法恢复。", "提示", {
      type: "warning",
      confirmButtonText: "确定",
      cancelButtonText: "取消"
    });

    await deleteSkill(id);
    ElMessage.success("删除成功");
    fetchSkills();
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error("删除失败:", error);
      ElMessage.error("删除失败");
    }
  }
};

// 提交编辑
const handleEditorSubmit = async () => {
  editorVisible.value = false;
  fetchSkills();
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

// 获取分类标签文本
const getCategoryLabel = (category: string) => {
  const labelMap: Record<string, string> = {
    model: "Model",
    hook: "Hook",
    rule: "Rule",
    audit: "Audit"
  };
  return labelMap[category] || category;
};

// 初始化
onMounted(() => {
  fetchSkills();
});
</script>

<style scoped lang="scss">
.skill-library {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 18px;
      font-weight: bold;
    }
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
