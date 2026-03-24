<template>
  <div class="tool-kit-manage">
    <el-card shadow="never">
      <template #header>
        <div class="head">
          <span>工具包管理</span>
          <el-button type="primary" @click="openDialog()">新增</el-button>
        </div>
      </template>

      <el-form :inline="true" class="filter" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" clearable placeholder="名称或 code" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="list" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="code" label="code" min-width="120" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="icon" label="图标" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="88">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" link @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.pageNum"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        class="pager"
        @size-change="load"
        @current-change="load"
      />
    </el-card>

    <el-dialog v-model="visible" :title="editId ? '编辑工具包' : '新增工具包'" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-form-item label="code" prop="code">
          <el-input v-model="form.code" :disabled="!!editId" placeholder="如 voice-clone" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-input v-model="form.icon" placeholder="Element Plus 图标名，如 Microphone" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="ToolKitManage">
import { ref, reactive, onMounted } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  getAdminToolPackageList,
  createToolPackage,
  updateToolPackage,
  deleteToolPackage
} from "@/api/modules/toolPackage";
import type { ToolPackageItem, ToolPackageCreate } from "@/api/modules/toolPackage";

const loading = ref(false);
const list = ref<ToolPackageItem[]>([]);
const total = ref(0);
const query = reactive({
  pageNum: 1,
  pageSize: 10,
  status: undefined as number | undefined,
  keyword: ""
});

const visible = ref(false);
const saving = ref(false);
const editId = ref<number | null>(null);
const formRef = ref<FormInstance>();
const form = reactive<ToolPackageCreate & { id?: number }>({
  code: "",
  name: "",
  description: "",
  icon: "Microphone",
  sort_order: 0,
  status: 1
});

const rules: FormRules = {
  code: [{ required: true, message: "必填", trigger: "blur" }],
  name: [{ required: true, message: "必填", trigger: "blur" }],
  icon: [{ required: true, message: "必填", trigger: "blur" }]
};

const load = async () => {
  loading.value = true;
  try {
    const res = await getAdminToolPackageList({
      pageNum: query.pageNum,
      pageSize: query.pageSize,
      status: query.status,
      keyword: query.keyword || undefined
    });
    if (res.data) {
      list.value = res.data.list || [];
      total.value = res.data.total ?? 0;
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false;
  }
};

const openDialog = (row?: ToolPackageItem) => {
  editId.value = row?.id ?? null;
  if (row) {
    form.code = row.code;
    form.name = row.name;
    form.description = row.description || "";
    form.icon = row.icon;
    form.sort_order = row.sort_order;
    form.status = row.status;
  } else {
    form.code = "";
    form.name = "";
    form.description = "";
    form.icon = "Microphone";
    form.sort_order = 0;
    form.status = 1;
  }
  visible.value = true;
};

const submit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();
  saving.value = true;
  try {
    if (editId.value) {
      await updateToolPackage(editId.value, {
        code: form.code,
        name: form.name,
        description: form.description || undefined,
        icon: form.icon,
        sort_order: form.sort_order,
        status: form.status
      });
      ElMessage.success("已更新");
    } else {
      await createToolPackage({
        code: form.code,
        name: form.name,
        description: form.description || undefined,
        icon: form.icon,
        sort_order: form.sort_order,
        status: form.status
      });
      ElMessage.success("已创建");
    }
    visible.value = false;
    await load();
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false;
  }
};

const onDelete = (row: ToolPackageItem) => {
  ElMessageBox.confirm(`确定删除「${row.name}」？`, "提示", { type: "warning" })
    .then(async () => {
      await deleteToolPackage(row.id);
      ElMessage.success("已删除");
      await load();
    })
    .catch(() => {});
};

onMounted(load);
</script>

<style scoped lang="scss">
.tool-kit-manage {
  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .filter {
    margin-bottom: 12px;
  }
  .pager {
    margin-top: 16px;
    justify-content: flex-end;
  }
}
</style>
