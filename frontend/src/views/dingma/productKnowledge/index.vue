<template>
  <div class="product-knowledge-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">产品配方配置</span>
          <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增产品</el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select
          v-model="filters.category_code"
          placeholder="全部品类"
          clearable
          style="width: 160px"
          @change="loadList"
        >
          <el-option
            v-for="cat in categories"
            :key="cat.category_code"
            :label="`${cat.category_name}（${cat.count}）`"
            :value="cat.category_code"
          />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="全部状态"
          clearable
          style="width: 120px; margin-left: 10px"
          @change="loadList"
        >
          <el-option label="启用" :value="1" />
          <el-option label="禁用" :value="0" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          placeholder="搜索产品名/编码"
          clearable
          style="width: 220px; margin-left: 10px"
          @keyup.enter="loadList"
          @clear="loadList"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" :icon="Search" style="margin-left: 10px" @click="loadList">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" style="width: 100%; margin-top: 16px">
        <el-table-column prop="product_name" label="产品名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_code" label="产品编码" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag type="info" effect="plain">{{ row.product_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="品类" width="100" />
        <el-table-column prop="aliases" label="别名" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ (row.aliases || []).join("、") || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="source_version" label="课件版本" width="100" />
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              :loading="statusLoading === row.id"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page.pageNum"
        v-model:page-size="page.pageSize"
        :total="page.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        background
        style="margin-top: 16px; justify-content: flex-end"
        @size-change="loadList"
        @current-change="loadList"
      />
    </el-card>

    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="720px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="110px">
        <el-divider content-position="left">基础信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品编码" prop="product_code">
              <el-input
                v-model="formData.product_code"
                placeholder="如 mixian_paocai_chaoxian"
                :disabled="isEdit"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品名称" prop="product_name">
              <el-input v-model="formData.product_name" placeholder="如 泡菜朝鲜面" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="品类编码" prop="category_code">
              <el-input v-model="formData.category_code" placeholder="如 mixian" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品类名称" prop="category_name">
              <el-input v-model="formData.category_name" placeholder="如 米线" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="别名">
          <el-select
            v-model="formData.aliases"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入别名后回车，如 朝鲜面"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课件版本">
              <el-input v-model="formData.source_version" placeholder="如 2026-01" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="formData.sort_order" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">文案事实（智能体注入）</el-divider>
        <el-form-item label="文案事实">
          <el-input
            v-model="formData.copywriting_facts"
            type="textarea"
            :rows="6"
            placeholder="含：...&#10;不含：...&#10;可写：...&#10;不可写：..."
          />
        </el-form-item>

        <el-divider content-position="left">配方全量（售后预留）</el-divider>
        <el-form-item label="出货配比">
          <el-input
            v-model="formData.pack_formula"
            type="textarea"
            :rows="4"
            placeholder="含克重/包数的出货配比"
          />
        </el-form-item>
        <el-form-item label="制作详情 JSON">
          <el-input
            v-model="recipeDetailText"
            type="textarea"
            :rows="8"
            placeholder='{"ingredients":[{"name":"包菜","amount":"1500g"}],"steps":["..."],"notes":["..."]}'
          />
          <div class="form-tip">JSON 格式，含 ingredients / steps / notes 等字段</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts" name="dingmaProductKnowledge">
import { onMounted, reactive, ref } from "vue";
import { CirclePlus, Delete, EditPen, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import {
  createProductKnowledgeApi,
  deleteProductKnowledgeApi,
  getProductKnowledgeCategoriesApi,
  getProductKnowledgeListApi,
  updateProductKnowledgeApi,
  updateProductKnowledgeStatusApi,
  type ProductKnowledgeCategory,
  type ProductKnowledgeCreate,
  type ProductKnowledgeItem
} from "@/api/modules/dingmaProductKnowledge";

const loading = ref(false);
const submitting = ref(false);
const statusLoading = ref<number | null>(null);
const tableData = ref<ProductKnowledgeItem[]>([]);
const categories = ref<ProductKnowledgeCategory[]>([]);

const page = reactive({ pageNum: 1, pageSize: 20, total: 0 });
const filters = reactive({
  category_code: "" as string | undefined,
  status: undefined as number | undefined,
  keyword: ""
});

const drawerVisible = ref(false);
const drawerTitle = ref("新增产品");
const isEdit = ref(false);
const editingId = ref<number | null>(null);
const formRef = ref<FormInstance>();
const recipeDetailText = ref("");

const defaultForm = (): ProductKnowledgeCreate => ({
  category_code: "",
  category_name: "",
  product_code: "",
  product_name: "",
  aliases: [],
  pack_formula: "",
  copywriting_facts: "",
  source_version: "2026-01",
  status: 1,
  sort_order: 0
});

const formData = ref<ProductKnowledgeCreate>(defaultForm());

const formRules: FormRules = {
  product_code: [{ required: true, message: "请输入产品编码", trigger: "blur" }],
  product_name: [{ required: true, message: "请输入产品名称", trigger: "blur" }],
  category_code: [{ required: true, message: "请输入品类编码", trigger: "blur" }],
  category_name: [{ required: true, message: "请输入品类名称", trigger: "blur" }]
};

const loadCategories = async () => {
  const { data } = await getProductKnowledgeCategoriesApi();
  categories.value = data || [];
};

const loadList = async () => {
  loading.value = true;
  try {
    const { data } = await getProductKnowledgeListApi({
      pageNum: page.pageNum,
      pageSize: page.pageSize,
      category_code: filters.category_code || undefined,
      status: filters.status,
      keyword: filters.keyword || undefined
    });
    tableData.value = data?.list || [];
    page.total = data?.total || 0;
  } finally {
    loading.value = false;
  }
};

const openDrawer = (mode: "新增" | "编辑", row?: ProductKnowledgeItem) => {
  drawerTitle.value = mode === "新增" ? "新增产品" : "编辑产品";
  isEdit.value = mode === "编辑";
  editingId.value = row?.id ?? null;

  if (row) {
    formData.value = {
      category_code: row.category_code,
      category_name: row.category_name,
      product_code: row.product_code,
      product_name: row.product_name,
      aliases: row.aliases || [],
      pack_formula: row.pack_formula || "",
      copywriting_facts: row.copywriting_facts || "",
      source_version: row.source_version || "",
      status: row.status,
      sort_order: row.sort_order
    };
    recipeDetailText.value = row.recipe_detail ? JSON.stringify(row.recipe_detail, null, 2) : "";
  } else {
    formData.value = defaultForm();
    recipeDetailText.value = "";
  }
  drawerVisible.value = true;
};

const parseRecipeDetail = () => {
  const text = recipeDetailText.value.trim();
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    ElMessage.error("制作详情 JSON 格式不正确");
    throw new Error("invalid json");
  }
};

const handleSubmit = async () => {
  await formRef.value?.validate();
  let recipe_detail;
  try {
    recipe_detail = parseRecipeDetail();
  } catch {
    return;
  }

  submitting.value = true;
  try {
    const payload = { ...formData.value, recipe_detail };
    if (isEdit.value && editingId.value) {
      const { product_code: _pc, ...updateData } = payload;
      await updateProductKnowledgeApi(editingId.value, updateData);
      ElMessage.success("更新成功");
    } else {
      await createProductKnowledgeApi(payload);
      ElMessage.success("创建成功");
    }
    drawerVisible.value = false;
    await loadList();
    await loadCategories();
  } finally {
    submitting.value = false;
  }
};

const handleStatusChange = async (row: ProductKnowledgeItem) => {
  statusLoading.value = row.id;
  try {
    await updateProductKnowledgeStatusApi(row.id, row.status);
    ElMessage.success("状态已更新");
  } catch {
    row.status = row.status === 1 ? 0 : 1;
  } finally {
    statusLoading.value = null;
  }
};

const handleDelete = async (row: ProductKnowledgeItem) => {
  await ElMessageBox.confirm(`确定删除「${row.product_name}」吗？`, "提示", { type: "warning" });
  await deleteProductKnowledgeApi(row.id);
  ElMessage.success("删除成功");
  await loadList();
  await loadCategories();
};

onMounted(async () => {
  await Promise.all([loadCategories(), loadList()]);
});
</script>

<style scoped lang="scss">
.product-knowledge-page {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    .title {
      font-size: 16px;
      font-weight: 600;
    }
  }
  .filter-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
  }
  .form-tip {
    margin-top: 4px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}
</style>
