<template>
  <div class="product-knowledge-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">产品知识库 v2</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="成品 SKU" name="sku">
          <div class="toolbar">
            <el-select v-model="skuFilters.category_code" placeholder="全部品类" clearable style="width: 160px" @change="loadSkuList">
              <el-option v-for="cat in skuCategories" :key="cat.category_code" :label="`${cat.category_name}（${cat.count}）`" :value="cat.category_code" />
            </el-select>
            <el-input v-model="skuFilters.keyword" placeholder="搜索 SKU" clearable style="width: 220px; margin-left: 10px" @keyup.enter="loadSkuList" />
            <el-button type="primary" style="margin-left: 10px" @click="loadSkuList">查询</el-button>
            <el-button type="primary" :icon="CirclePlus" style="margin-left: auto" @click="openSkuDrawer('新增')">新增 SKU</el-button>
          </div>
          <el-table v-loading="skuLoading" :data="skuTable" style="margin-top: 12px">
            <el-table-column prop="sku_name" label="名称" min-width="140" />
            <el-table-column prop="sku_code" label="编码" min-width="160" />
            <el-table-column prop="category_name" label="品类" width="90" />
            <el-table-column label="组件数" width="80">
              <template #default="{ row }">{{ (row.component_links || []).length }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.status" :active-value="1" :inactive-value="0" @change="handleSkuStatus(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openSkuDrawer('编辑', row)">编辑</el-button>
                <el-button type="danger" link @click="handleSkuDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="组件/子配方" name="component">
          <div class="toolbar">
            <el-select v-model="compFilters.component_type" placeholder="全部类型" clearable style="width: 140px" @change="loadCompList">
              <el-option label="酱料 sauce" value="sauce" />
              <el-option label="母馅 filling_base" value="filling_base" />
              <el-option label="辣油 condiment" value="condiment" />
              <el-option label="泡菜 pickle" value="pickle" />
              <el-option label="面皮 dough" value="dough" />
            </el-select>
            <el-input v-model="compFilters.keyword" placeholder="搜索组件" clearable style="width: 220px; margin-left: 10px" @keyup.enter="loadCompList" />
            <el-button type="primary" style="margin-left: 10px" @click="loadCompList">查询</el-button>
            <el-button type="primary" :icon="CirclePlus" style="margin-left: auto" @click="openCompDrawer('新增')">新增组件</el-button>
          </div>
          <el-table v-loading="compLoading" :data="compTable" style="margin-top: 12px">
            <el-table-column prop="component_name" label="名称" min-width="140" />
            <el-table-column prop="component_code" label="编码" min-width="160" />
            <el-table-column prop="component_type" label="类型" width="110" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.status" :active-value="1" :inactive-value="0" @change="handleCompStatus(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openCompDrawer('编辑', row)">编辑</el-button>
                <el-button type="danger" link @click="handleCompDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- SKU Drawer -->
    <el-drawer v-model="skuDrawerVisible" :title="skuDrawerTitle" size="760px" destroy-on-close>
      <el-form ref="skuFormRef" :model="skuForm" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="SKU编码" required><el-input v-model="skuForm.sku_code" :disabled="skuIsEdit" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="SKU名称" required><el-input v-model="skuForm.sku_name" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="品类编码"><el-input v-model="skuForm.category_code" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="品类名称"><el-input v-model="skuForm.category_name" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="别名"><el-select v-model="skuForm.aliases" multiple filterable allow-create default-first-option style="width:100%" /></el-form-item>
        <el-form-item label="出货配比"><el-input v-model="skuForm.pack_formula" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="护栏 JSON"><el-input v-model="skuGuardrailText" type="textarea" :rows="4" placeholder='{"contains":[],"excludes":[],"forbidden":[]}' /></el-form-item>
        <el-form-item label="过程文案 JSON"><el-input v-model="skuProcessText" type="textarea" :rows="4" placeholder="无组件关联时可填 SKU 级过程文案" /></el-form-item>
        <el-divider>组件关联</el-divider>
        <div v-for="(link, idx) in skuForm.component_links" :key="idx" class="link-row">
          <el-select v-model="link.component_code" placeholder="组件" style="width: 200px">
            <el-option v-for="opt in componentOptions" :key="opt.component_code" :label="opt.component_name" :value="opt.component_code" />
          </el-select>
          <el-select v-model="link.role" style="width: 140px; margin-left: 8px">
            <el-option label="主酱 primary_sauce" value="primary_sauce" />
            <el-option label="母馅 filling_base" value="filling_base" />
            <el-option label="辅料 condiment" value="condiment" />
            <el-option label="其他 other" value="other" />
          </el-select>
          <el-checkbox v-model="link.process_focus" style="margin-left: 8px">过程焦点</el-checkbox>
          <el-button type="danger" link @click="skuForm.component_links?.splice(idx, 1)">删除</el-button>
        </div>
        <el-button type="primary" link @click="addSkuLink">+ 添加关联</el-button>
      </el-form>
      <template #footer>
        <el-button @click="skuDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitSku">保存</el-button>
      </template>
    </el-drawer>

    <!-- Component Drawer -->
    <el-drawer v-model="compDrawerVisible" :title="compDrawerTitle" size="760px" destroy-on-close>
      <el-form :model="compForm" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="组件编码" required><el-input v-model="compForm.component_code" :disabled="compIsEdit" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组件名称" required><el-input v-model="compForm.component_name" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="组件类型">
          <el-select v-model="compForm.component_type" style="width: 200px">
            <el-option label="sauce" value="sauce" /><el-option label="filling_base" value="filling_base" />
            <el-option label="condiment" value="condiment" /><el-option label="pickle" value="pickle" />
            <el-option label="dough" value="dough" /><el-option label="other" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="别名"><el-select v-model="compForm.aliases" multiple filterable allow-create default-first-option style="width:100%" /></el-form-item>
        <el-form-item label="用法说明"><el-input v-model="compForm.pack_formula" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="护栏 JSON"><el-input v-model="compGuardrailText" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="过程文案 JSON"><el-input v-model="compProcessText" type="textarea" :rows="6" /></el-form-item>
        <el-form-item label="配方 JSON"><el-input v-model="compRecipeText" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="compDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitComp">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts" name="dingmaProductKnowledge">
import { onMounted, reactive, ref } from "vue";
import { CirclePlus } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  createKnowledgeComponentApi,
  createKnowledgeSkuApi,
  deleteKnowledgeComponentApi,
  deleteKnowledgeSkuApi,
  getKnowledgeComponentListApi,
  getKnowledgeComponentOptionsApi,
  getKnowledgeSkuCategoriesApi,
  getKnowledgeSkuListApi,
  updateKnowledgeComponentApi,
  updateKnowledgeComponentStatusApi,
  updateKnowledgeSkuApi,
  updateKnowledgeSkuStatusApi,
  type ComponentOption,
  type KnowledgeComponentItem,
  type KnowledgeSkuItem,
  type SkuCategory,
  type SkuComponentLink
} from "@/api/modules/dingmaProductKnowledge";

const activeTab = ref("sku");
const skuLoading = ref(false);
const compLoading = ref(false);
const submitting = ref(false);
const skuTable = ref<KnowledgeSkuItem[]>([]);
const compTable = ref<KnowledgeComponentItem[]>([]);
const skuCategories = ref<SkuCategory[]>([]);
const componentOptions = ref<ComponentOption[]>([]);

const skuFilters = reactive({ category_code: "", keyword: "" });
const compFilters = reactive({ component_type: "", keyword: "" });

const skuDrawerVisible = ref(false);
const compDrawerVisible = ref(false);
const skuDrawerTitle = ref("");
const compDrawerTitle = ref("");
const skuIsEdit = ref(false);
const compIsEdit = ref(false);
const editingSkuId = ref<number | null>(null);
const editingCompId = ref<number | null>(null);

const defaultSkuForm = (): Partial<KnowledgeSkuItem> => ({
  sku_code: "", sku_name: "", category_code: "", category_name: "", aliases: [],
  pack_formula: "", status: 1, sort_order: 0, source_version: "2026-01", component_links: []
});
const skuForm = ref<Partial<KnowledgeSkuItem>>(defaultSkuForm());
const skuGuardrailText = ref("");
const skuProcessText = ref("");

const defaultCompForm = (): Partial<KnowledgeComponentItem> => ({
  component_code: "", component_name: "", component_type: "sauce", aliases: [],
  pack_formula: "", status: 1, sort_order: 0, source_version: "2026-01"
});
const compForm = ref<Partial<KnowledgeComponentItem>>(defaultCompForm());
const compGuardrailText = ref("");
const compProcessText = ref("");
const compRecipeText = ref("");

const parseJson = (text: string, label: string) => {
  const t = text.trim();
  if (!t) return undefined;
  try { return JSON.parse(t); } catch { ElMessage.error(`${label} JSON 格式错误`); throw new Error("json"); }
};

const loadSkuList = async () => {
  skuLoading.value = true;
  try {
    const { data } = await getKnowledgeSkuListApi({
      pageNum: 1, pageSize: 100,
      category_code: skuFilters.category_code || undefined,
      keyword: skuFilters.keyword || undefined
    });
    skuTable.value = data?.list || [];
  } finally { skuLoading.value = false; }
};

const loadCompList = async () => {
  compLoading.value = true;
  try {
    const { data } = await getKnowledgeComponentListApi({
      pageNum: 1, pageSize: 100,
      component_type: compFilters.component_type || undefined,
      keyword: compFilters.keyword || undefined
    });
    compTable.value = data?.list || [];
  } finally { compLoading.value = false; }
};

const loadComponentOptions = async () => {
  const { data } = await getKnowledgeComponentOptionsApi();
  componentOptions.value = data || [];
};

const onTabChange = (name: string | number) => {
  if (name === "sku") loadSkuList();
  else loadCompList();
};

const openSkuDrawer = (mode: "新增" | "编辑", row?: KnowledgeSkuItem) => {
  skuDrawerTitle.value = mode === "新增" ? "新增 SKU" : "编辑 SKU";
  skuIsEdit.value = mode === "编辑";
  editingSkuId.value = row?.id ?? null;
  if (row) {
    skuForm.value = { ...row, component_links: [...(row.component_links || [])] };
    skuGuardrailText.value = row.guardrail ? JSON.stringify(row.guardrail, null, 2) : "";
    skuProcessText.value = row.process_copywriting ? JSON.stringify(row.process_copywriting, null, 2) : "";
  } else {
    skuForm.value = defaultSkuForm();
    skuGuardrailText.value = "";
    skuProcessText.value = "";
  }
  skuDrawerVisible.value = true;
};

const openCompDrawer = (mode: "新增" | "编辑", row?: KnowledgeComponentItem) => {
  compDrawerTitle.value = mode === "新增" ? "新增组件" : "编辑组件";
  compIsEdit.value = mode === "编辑";
  editingCompId.value = row?.id ?? null;
  if (row) {
    compForm.value = { ...row };
    compGuardrailText.value = row.guardrail ? JSON.stringify(row.guardrail, null, 2) : "";
    compProcessText.value = row.process_copywriting ? JSON.stringify(row.process_copywriting, null, 2) : "";
    compRecipeText.value = row.recipe_detail ? JSON.stringify(row.recipe_detail, null, 2) : "";
  } else {
    compForm.value = defaultCompForm();
    compGuardrailText.value = "";
    compProcessText.value = "";
    compRecipeText.value = "";
  }
  compDrawerVisible.value = true;
};

const addSkuLink = () => {
  if (!skuForm.value.component_links) skuForm.value.component_links = [];
  (skuForm.value.component_links as SkuComponentLink[]).push({
    component_code: "", role: "primary_sauce", process_focus: false, sort_order: skuForm.value.component_links.length
  });
};

const submitSku = async () => {
  let guardrail, process_copywriting;
  try {
    guardrail = parseJson(skuGuardrailText.value, "护栏");
    process_copywriting = parseJson(skuProcessText.value, "过程文案");
  } catch { return; }
  submitting.value = true;
  try {
    const payload = { ...skuForm.value, guardrail, process_copywriting };
    if (skuIsEdit.value && editingSkuId.value) {
      await updateKnowledgeSkuApi(editingSkuId.value, payload);
    } else {
      await createKnowledgeSkuApi(payload);
    }
    ElMessage.success("保存成功");
    skuDrawerVisible.value = false;
    await loadSkuList();
  } finally { submitting.value = false; }
};

const submitComp = async () => {
  let guardrail, process_copywriting, recipe_detail;
  try {
    guardrail = parseJson(compGuardrailText.value, "护栏");
    process_copywriting = parseJson(compProcessText.value, "过程文案");
    recipe_detail = parseJson(compRecipeText.value, "配方");
  } catch { return; }
  submitting.value = true;
  try {
    const payload = { ...compForm.value, guardrail, process_copywriting, recipe_detail };
    if (compIsEdit.value && editingCompId.value) {
      await updateKnowledgeComponentApi(editingCompId.value, payload);
    } else {
      await createKnowledgeComponentApi(payload);
    }
    ElMessage.success("保存成功");
    compDrawerVisible.value = false;
    await loadCompList();
    await loadComponentOptions();
  } finally { submitting.value = false; }
};

const handleSkuStatus = async (row: KnowledgeSkuItem) => {
  try { await updateKnowledgeSkuStatusApi(row.id, row.status); }
  catch { row.status = row.status === 1 ? 0 : 1; }
};

const handleCompStatus = async (row: KnowledgeComponentItem) => {
  try { await updateKnowledgeComponentStatusApi(row.id, row.status); }
  catch { row.status = row.status === 1 ? 0 : 1; }
};

const handleSkuDelete = async (row: KnowledgeSkuItem) => {
  await ElMessageBox.confirm(`确定删除「${row.sku_name}」？`, "提示", { type: "warning" });
  await deleteKnowledgeSkuApi(row.id);
  ElMessage.success("已删除");
  await loadSkuList();
};

const handleCompDelete = async (row: KnowledgeComponentItem) => {
  await ElMessageBox.confirm(`确定删除「${row.component_name}」？`, "提示", { type: "warning" });
  await deleteKnowledgeComponentApi(row.id);
  ElMessage.success("已删除");
  await loadCompList();
};

onMounted(async () => {
  const { data } = await getKnowledgeSkuCategoriesApi();
  skuCategories.value = data || [];
  await Promise.all([loadSkuList(), loadComponentOptions()]);
});
</script>

<style scoped lang="scss">
.product-knowledge-page {
  .card-header .title { font-size: 16px; font-weight: 600; }
  .toolbar { display: flex; flex-wrap: wrap; align-items: center; margin-bottom: 8px; }
  .link-row { display: flex; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 4px; }
}
</style>
