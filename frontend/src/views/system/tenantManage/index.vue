<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="租户列表"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <template #tableHeader>
        <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增租户')">新增租户</el-button>
      </template>

      <template #is_default="scope">
        <el-tag :type="scope.row.is_default ? 'warning' : 'info'" effect="plain">
          {{ scope.row.is_default ? "主租户" : "普通" }}
        </el-tag>
      </template>

      <template #operation="scope">
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑租户', scope.row)">编辑</el-button>
      </template>
    </ProTable>

    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="520px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="110px">
        <el-form-item label="租户代码" prop="code">
          <el-input
            v-model="formData.code"
            placeholder="英文唯一标识，如 dingma"
            maxlength="64"
            show-word-limit
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="formData.name" placeholder="显示名称" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="主租户">
          <el-switch v-model="formData.is_default" active-text="是" inactive-text="否" />
          <div class="form-tip">全局仅能有一条主租户，勾选后会自动取消其他租户的主租户标记</div>
        </el-form-item>
        <el-form-item label="小程序 AppID" prop="wechat_app_id">
          <el-input v-model="formData.wechat_app_id" placeholder="可选，与小程序登录解析租户一致" maxlength="64" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="tenantManage">
import { ref, reactive } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { CirclePlus, EditPen } from "@element-plus/icons-vue";
import type { Tenant } from "@/api/interface";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getTenantListApi, createTenantApi, updateTenantApi } from "@/api/modules/tenant";

const proTable = ref<ProTableInstance>();

const dataCallback = (data: any) => ({
  list: data.list || [],
  total: data.total || 0
});

const getTableList = (params: Tenant.ReqTenantParams) => getTenantListApi(params);

const columns = reactive<ColumnProps<Tenant.ResTenant>[]>([
  { type: "index", label: "#", width: 56 },
  { prop: "id", label: "ID", width: 72 },
  {
    prop: "code",
    label: "租户代码",
    minWidth: 120,
    search: { el: "input" }
  },
  {
    prop: "name",
    label: "租户名称",
    minWidth: 140,
    search: { el: "input" }
  },
  { prop: "is_default", label: "类型", width: 100 },
  {
    prop: "wechat_app_id",
    label: "小程序 AppID",
    minWidth: 160,
    showOverflowTooltip: true
  },
  {
    prop: "remark",
    label: "备注",
    minWidth: 160,
    showOverflowTooltip: true
  },
  { prop: "created_at", label: "创建时间", width: 170 },
  { prop: "operation", label: "操作", fixed: "right", width: 120 }
]);

const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();

const formData = reactive<Tenant.ReqTenantCreate & { id?: number }>({
  code: "",
  name: "",
  is_default: false,
  remark: "",
  wechat_app_id: ""
});

const formRules: FormRules = {
  code: [{ required: true, message: "请输入租户代码", trigger: "blur" }],
  name: [{ required: true, message: "请输入租户名称", trigger: "blur" }]
};

const openDrawer = (title: string, row?: Tenant.ResTenant) => {
  drawerTitle.value = title;
  isEdit.value = !!row?.id;
  if (row?.id) {
    formData.id = row.id;
    formData.code = row.code;
    formData.name = row.name;
    formData.is_default = row.is_default;
    formData.remark = row.remark || "";
    formData.wechat_app_id = row.wechat_app_id || "";
  } else {
    delete formData.id;
    formData.code = "";
    formData.name = "";
    formData.is_default = false;
    formData.remark = "";
    formData.wechat_app_id = "";
  }
  drawerVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();
  submitLoading.value = true;
  try {
    if (isEdit.value && formData.id) {
      const { id, code: _c, ...rest } = formData;
      await updateTenantApi(id, rest as Tenant.ReqTenantUpdate);
      ElMessage.success("更新成功");
    } else {
      const { id: _i, ...createPayload } = formData;
      await createTenantApi(createPayload as Tenant.ReqTenantCreate);
      ElMessage.success("创建成功");
    }
    drawerVisible.value = false;
    proTable.value?.getTableList();
  } catch (e: any) {
    ElMessage.error(e?.msg || e?.message || "操作失败");
  } finally {
    submitLoading.value = false;
  }
};
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}
</style>
