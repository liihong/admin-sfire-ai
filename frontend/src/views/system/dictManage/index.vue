<template>
  <div class="dict-manage">
    <el-row :gutter="20">
      <!-- 左侧：字典类型列表 -->
      <el-col :span="10">
        <el-card class="dict-type-card">
          <template #header>
            <div class="card-header">
              <span>字典类型</span>
              <el-button type="primary" :icon="Plus" size="small" @click="openDictDialog('新增')">新增</el-button>
            </div>
          </template>

          <el-table
            v-loading="dictLoading"
            :data="dictList"
            :highlight-current-row="true"
            @row-click="handleDictClick"
            style="width: 100%"
          >
            <el-table-column prop="dict_name" label="字典名称" min-width="100" />
            <el-table-column prop="dict_code" label="字典编码" min-width="100">
              <template #default="{ row }">
                <el-tag type="info" effect="plain">{{ row.dict_code }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_enabled" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_enabled ? 'success' : 'danger'">
                  {{ row.is_enabled ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click.stop="openDictDialog('编辑', row)">编辑</el-button>
                <el-button type="danger" link size="small" @click.stop="handleDeleteDict(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="dictPage.pageNum"
            v-model:page-size="dictPage.pageSize"
            :total="dictPage.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            background
            small
            style="margin-top: 16px; justify-content: flex-end"
            @size-change="fetchDictList"
            @current-change="fetchDictList"
          />
        </el-card>
      </el-col>

      <!-- 右侧：字典项列表 -->
      <el-col :span="14">
        <el-card class="dict-item-card">
          <template #header>
            <div class="card-header">
              <span>
                字典项
                <el-tag v-if="currentDict" type="primary" style="margin-left: 8px">
                  {{ currentDict.dict_name }}
                </el-tag>
              </span>
              <el-button
                type="primary"
                :icon="Plus"
                size="small"
                :disabled="!currentDict"
                @click="openItemDialog('新增')"
              >
                新增
              </el-button>
            </div>
          </template>

          <el-empty v-if="!currentDict" description="请选择左侧字典类型" />

          <template v-else>
            <el-table v-loading="itemLoading" :data="itemList" style="width: 100%">
              <el-table-column prop="item_label" label="显示标签" min-width="100" />
              <el-table-column prop="item_value" label="选项值" min-width="100">
                <template #default="{ row }">
                  <el-tag type="info" effect="plain">{{ row.item_value }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="sort_order" label="排序" width="80" />
              <el-table-column prop="is_enabled" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.is_enabled ? 'success' : 'danger'">
                    {{ row.is_enabled ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="openItemDialog('编辑', row)">编辑</el-button>
                  <el-button type="danger" link size="small" @click="handleDeleteItem(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <el-pagination
              v-model:current-page="itemPage.pageNum"
              v-model:page-size="itemPage.pageSize"
              :total="itemPage.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              background
              small
              style="margin-top: 16px; justify-content: flex-end"
              @size-change="fetchItemList"
              @current-change="fetchItemList"
            />
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 字典类型编辑对话框 -->
    <el-dialog v-model="dictDialogVisible" :title="dictDialogTitle" width="500px" destroy-on-close>
      <el-form ref="dictFormRef" :model="dictFormData" :rules="dictFormRules" label-width="100px">
        <el-form-item label="字典编码" prop="dict_code">
          <el-input
            v-model="dictFormData.dict_code"
            placeholder="请输入字典编码（英文）"
            :disabled="isDictEdit"
            maxlength="64"
          />
        </el-form-item>
        <el-form-item label="字典名称" prop="dict_name">
          <el-input v-model="dictFormData.dict_name" placeholder="请输入字典名称" maxlength="128" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="dictFormData.description" type="textarea" placeholder="请输入描述（可选）" :rows="3" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="dictFormData.sort_order" :min="0" :max="999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="is_enabled">
          <el-switch v-model="dictFormData.is_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dictDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dictSubmitLoading" @click="handleDictSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 字典项编辑对话框 -->
    <el-dialog v-model="itemDialogVisible" :title="itemDialogTitle" width="500px" destroy-on-close>
      <el-form ref="itemFormRef" :model="itemFormData" :rules="itemFormRules" label-width="100px">
        <el-form-item label="显示标签" prop="item_label">
          <el-input v-model="itemFormData.item_label" placeholder="请输入显示标签" maxlength="128" />
        </el-form-item>
        <el-form-item label="选项值" prop="item_value">
          <el-input v-model="itemFormData.item_value" placeholder="请输入选项值" maxlength="128" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="itemFormData.description" type="textarea" placeholder="请输入描述（可选）" :rows="3" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="itemFormData.sort_order" :min="0" :max="999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="is_enabled">
          <el-switch v-model="itemFormData.is_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="itemSubmitLoading" @click="handleItemSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="dictManage">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import {
  getDictList,
  createDict,
  updateDict,
  deleteDict,
  getDictItemList,
  createDictItem,
  updateDictItem,
  deleteDictItem,
  Dictionary
} from "@/api/modules/dictionary";

// ==================== 字典类型相关 ====================
const dictLoading = ref(false);
const dictList = ref<Dictionary.DictType[]>([]);
const currentDict = ref<Dictionary.DictType | null>(null);
const dictPage = reactive({
  pageNum: 1,
  pageSize: 10,
  total: 0
});

// 获取字典类型列表
const fetchDictList = async () => {
  dictLoading.value = true;
  try {
    const { data } = await getDictList({
      pageNum: dictPage.pageNum,
      pageSize: dictPage.pageSize
    });
    dictList.value = data?.list || [];
    dictPage.total = data?.total || 0;
  } catch (error: any) {
    ElMessage.error(error?.msg || "获取字典类型失败");
  } finally {
    dictLoading.value = false;
  }
};

// 点击字典类型行
const handleDictClick = (row: Dictionary.DictType) => {
  currentDict.value = row;
  itemPage.pageNum = 1;
  fetchItemList();
};

// 字典类型对话框相关
const dictDialogVisible = ref(false);
const dictDialogTitle = ref("");
const isDictEdit = ref(false);
const dictSubmitLoading = ref(false);
const dictFormRef = ref<FormInstance>();
const dictFormData = reactive<Dictionary.ReqDictCreate & { id?: number }>({
  dict_code: "",
  dict_name: "",
  description: "",
  sort_order: 0,
  is_enabled: true
});

const dictFormRules: FormRules = {
  dict_code: [
    { required: true, message: "请输入字典编码", trigger: "blur" },
    { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: "编码必须以字母或下划线开头，只能包含字母、数字、下划线", trigger: "blur" }
  ],
  dict_name: [{ required: true, message: "请输入字典名称", trigger: "blur" }]
};

// 打开字典类型对话框
const openDictDialog = (title: string, row?: Dictionary.DictType) => {
  dictDialogTitle.value = title;
  isDictEdit.value = !!row;

  if (row) {
    dictFormData.id = row.id;
    dictFormData.dict_code = row.dict_code;
    dictFormData.dict_name = row.dict_name;
    dictFormData.description = row.description || "";
    dictFormData.sort_order = row.sort_order;
    dictFormData.is_enabled = row.is_enabled;
  } else {
    dictFormData.id = undefined;
    dictFormData.dict_code = "";
    dictFormData.dict_name = "";
    dictFormData.description = "";
    dictFormData.sort_order = 0;
    dictFormData.is_enabled = true;
  }

  dictDialogVisible.value = true;
};

// 提交字典类型表单
const handleDictSubmit = async () => {
  if (!dictFormRef.value) return;

  await dictFormRef.value.validate();
  dictSubmitLoading.value = true;

  try {
    if (isDictEdit.value && dictFormData.id) {
      const { id, dict_code, ...updateData } = dictFormData;
      await updateDict(id, updateData);
      ElMessage.success("更新成功");
    } else {
      await createDict(dictFormData);
      ElMessage.success("创建成功");
    }
    dictDialogVisible.value = false;
    fetchDictList();
  } catch (error: any) {
    ElMessage.error(error?.msg || "操作失败");
  } finally {
    dictSubmitLoading.value = false;
  }
};

// 删除字典类型
const handleDeleteDict = async (row: Dictionary.DictType) => {
  try {
    await ElMessageBox.confirm(`确定要删除字典类型【${row.dict_name}】吗？删除后所有字典项也会被删除！`, "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });

    await deleteDict(row.id);
    ElMessage.success("删除成功");

    // 如果删除的是当前选中的字典类型，清空右侧
    if (currentDict.value?.id === row.id) {
      currentDict.value = null;
      itemList.value = [];
    }

    fetchDictList();
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error?.msg || "删除失败");
    }
  }
};

// ==================== 字典项相关 ====================
const itemLoading = ref(false);
const itemList = ref<Dictionary.DictItem[]>([]);
const itemPage = reactive({
  pageNum: 1,
  pageSize: 10,
  total: 0
});

// 获取字典项列表
const fetchItemList = async () => {
  if (!currentDict.value) return;

  itemLoading.value = true;
  try {
    const { data } = await getDictItemList({
      dict_id: currentDict.value.id,
      pageNum: itemPage.pageNum,
      pageSize: itemPage.pageSize
    });
    itemList.value = data?.list || [];
    itemPage.total = data?.total || 0;
  } catch (error: any) {
    ElMessage.error(error?.msg || "获取字典项失败");
  } finally {
    itemLoading.value = false;
  }
};

// 字典项对话框相关
const itemDialogVisible = ref(false);
const itemDialogTitle = ref("");
const isItemEdit = ref(false);
const itemSubmitLoading = ref(false);
const itemFormRef = ref<FormInstance>();
const itemFormData = reactive<Dictionary.ReqDictItemCreate & { id?: number }>({
  dict_id: 0,
  item_value: "",
  item_label: "",
  description: "",
  sort_order: 0,
  is_enabled: true
});

const itemFormRules: FormRules = {
  item_label: [{ required: true, message: "请输入显示标签", trigger: "blur" }],
  item_value: [{ required: true, message: "请输入选项值", trigger: "blur" }]
};

// 打开字典项对话框
const openItemDialog = (title: string, row?: Dictionary.DictItem) => {
  if (!currentDict.value) return;

  itemDialogTitle.value = title;
  isItemEdit.value = !!row;

  if (row) {
    itemFormData.id = row.id;
    itemFormData.dict_id = row.dict_id;
    itemFormData.item_value = row.item_value;
    itemFormData.item_label = row.item_label;
    itemFormData.description = row.description || "";
    itemFormData.sort_order = row.sort_order;
    itemFormData.is_enabled = row.is_enabled;
  } else {
    itemFormData.id = undefined;
    itemFormData.dict_id = currentDict.value.id;
    itemFormData.item_value = "";
    itemFormData.item_label = "";
    itemFormData.description = "";
    itemFormData.sort_order = 0;
    itemFormData.is_enabled = true;
  }

  itemDialogVisible.value = true;
};

// 提交字典项表单
const handleItemSubmit = async () => {
  if (!itemFormRef.value) return;

  await itemFormRef.value.validate();
  itemSubmitLoading.value = true;

  try {
    if (isItemEdit.value && itemFormData.id) {
      const { id, dict_id, ...updateData } = itemFormData;
      await updateDictItem(id, updateData);
      ElMessage.success("更新成功");
    } else {
      await createDictItem(itemFormData);
      ElMessage.success("创建成功");
    }
    itemDialogVisible.value = false;
    fetchItemList();
  } catch (error: any) {
    ElMessage.error(error?.msg || "操作失败");
  } finally {
    itemSubmitLoading.value = false;
  }
};

// 删除字典项
const handleDeleteItem = async (row: Dictionary.DictItem) => {
  try {
    await ElMessageBox.confirm(`确定要删除字典项【${row.item_label}】吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });

    await deleteDictItem(row.id);
    ElMessage.success("删除成功");
    fetchItemList();
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error?.msg || "删除失败");
    }
  }
};

// 初始化
onMounted(() => {
  fetchDictList();
});
</script>

<style scoped lang="scss">
.dict-manage {
  padding: 10px;

  .dict-type-card,
  .dict-item-card {
    height: calc(100vh - 140px);
    display: flex;
    flex-direction: column;

    :deep(.el-card__body) {
      flex: 1;
      overflow: auto;
      display: flex;
      flex-direction: column;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  :deep(.el-table) {
    flex: 1;
  }

  :deep(.el-empty) {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
}
</style>
