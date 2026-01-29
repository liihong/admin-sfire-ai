<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="用户等级管理"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <el-button type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增等级</el-button>
      </template>

      <!-- 等级代码 -->
      <template #code="scope">
        <el-tag type="primary" effect="plain">
          {{ scope.row.code }}
        </el-tag>
      </template>

      <!-- IP类型 -->
      <template #ip_type="scope">
        <el-tag :type="scope.row.ip_type === 'permanent' ? 'success' : 'warning'" effect="plain">
          {{ scope.row.ip_type === 'permanent' ? '永久' : '临时' }}
        </el-tag>
      </template>

      <!-- 最大IP数量 -->
      <template #max_ip_count="scope">
        <span v-if="scope.row.max_ip_count === null || scope.row.max_ip_count === undefined">不限制</span>
        <span v-else>{{ scope.row.max_ip_count }}</span>
      </template>

      <!-- 每日AI能量限制 -->
      <template #daily_tokens_limit="scope">
        <span v-if="scope.row.daily_tokens_limit === null || scope.row.daily_tokens_limit === undefined">无限制</span>
        <span v-else>{{ scope.row.daily_tokens_limit }}</span>
      </template>

      <!-- 权限标识 -->
      <template #permissions="scope">
        <el-space wrap>
          <el-tag v-if="scope.row.can_use_advanced_agent" type="success" size="small">高级智能体</el-tag>
          <el-tag v-if="scope.row.unlimited_conversations" type="info" size="small">无限制对话</el-tag>
        </el-space>
      </template>

      <!-- 状态 -->
      <template #is_enabled="scope">
        <el-tag :type="scope.row.is_enabled ? 'success' : 'danger'" effect="plain">
          {{ scope.row.is_enabled ? "启用" : "禁用" }}
        </el-tag>
      </template>

      <!-- 表格操作 -->
      <template #operation="scope">
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', scope.row)">编辑</el-button>
        <el-button
          type="primary"
          link
          :icon="Refresh"
          @click="changeStatus(scope.row)"
        >
          {{ scope.row.is_enabled ? "禁用" : "启用" }}
        </el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteLevel(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 等级编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="600px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="140px">
        <el-form-item label="等级代码" prop="code">
          <el-input 
            v-model="formData.code" 
            placeholder="请输入等级代码（如：normal/vip/svip/max）" 
            maxlength="32" 
            show-word-limit 
            :disabled="isEdit"
          />
          <div class="form-tip">等级代码创建后不可修改</div>
        </el-form-item>
        <el-form-item label="等级名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入等级名称（中文显示）" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item label="最大IP数量" prop="max_ip_count">
          <el-input-number 
            v-model="formData.max_ip_count" 
            :min="1" 
            :max="999" 
            placeholder="留空表示不限制"
            style="width: 100%"
            :controls="false"
          />
          <div class="form-tip">留空表示不限制IP数量</div>
        </el-form-item>
        <el-form-item label="IP类型" prop="ip_type">
          <el-select v-model="formData.ip_type" placeholder="请选择IP类型" style="width: 100%">
            <el-option label="永久" value="permanent" />
            <el-option label="临时" value="temporary" />
          </el-select>
        </el-form-item>
        <el-form-item label="每日AI能量限制" prop="daily_tokens_limit">
          <el-input-number 
            v-model="formData.daily_tokens_limit" 
            :min="1" 
            :max="999999" 
            placeholder="留空表示无限制"
            style="width: 100%"
            :controls="false"
          />
          <div class="form-tip">留空表示无限制（normal用户默认限制3次）</div>
        </el-form-item>
        <el-form-item label="权限配置">
          <el-checkbox v-model="formData.can_use_advanced_agent">可使用高级智能体</el-checkbox>
          <el-checkbox v-model="formData.unlimited_conversations" style="margin-left: 20px">无限制对话</el-checkbox>
        </el-form-item>
        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number 
            v-model="formData.sort_order" 
            :min="0" 
            :max="999" 
            placeholder="数字越小越靠前"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_enabled">
          <el-switch v-model="formData.is_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="userLevelManage">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Refresh } from "@element-plus/icons-vue";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import {
  getUserLevelList,
  createUserLevel,
  updateUserLevel,
  deleteUserLevel,
  UserLevel
} from "@/api/modules/userLevel";

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 数据回调处理
const dataCallback = (data: any) => {
  return {
    list: data.list || [],
    total: data.total || 0
  };
};

// 获取表格数据
const getTableList = (params: UserLevel.ReqUserLevelParams) => {
  return getUserLevelList(params);
};

// 表格列配置
const columns = reactive<ColumnProps<UserLevel.ResUserLevel>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "id",
    label: "ID",
    width: 80
  },
  {
    prop: "code",
    label: "等级代码",
    width: 120,
    isShow: true,
    search: { el: "input" }
  },
  {
    prop: "name",
    label: "等级名称",
    width: 150,
    search: { el: "input" }
  },
  {
    prop: "max_ip_count",
    label: "最大IP数",
    width: 100
  },
  {
    prop: "ip_type",
    label: "IP类型",
    width: 100
  },
  {
    prop: "daily_tokens_limit",
    label: "每日AI能量",
    width: 120
  },
  {
    prop: "permissions",
    label: "权限",
    minWidth: 150
  },
  {
    prop: "sort_order",
    label: "排序",
    width: 80
  },
  {
    prop: "is_enabled",
    label: "状态",
    width: 100,
    search: { el: "select", props: { filterable: true }, options: [{ label: "启用", value: true }, { label: "禁用", value: false }] }
  },
  {
    prop: "created_at",
    label: "创建时间",
    width: 180
  },
  {
    prop: "updated_at",
    label: "更新时间",
    width: 180
  },
  { prop: "operation", label: "操作", fixed: "right", width: 250 }
]);

// ==================== 等级编辑抽屉 ====================
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive<UserLevel.ReqUserLevelCreate & UserLevel.ReqUserLevelUpdate & { id?: number }>({
  code: "",
  name: "",
  max_ip_count: null,
  ip_type: "permanent",
  daily_tokens_limit: null,
  can_use_advanced_agent: false,
  unlimited_conversations: false,
  is_enabled: true,
  sort_order: 0
});

const formRules: FormRules = {
  code: [
    { required: true, message: "请输入等级代码", trigger: "blur" },
    { pattern: /^[a-z][a-z0-9_]*$/, message: "等级代码必须以小写字母开头，只能包含小写字母、数字、下划线", trigger: "blur" }
  ],
  name: [{ required: true, message: "请输入等级名称", trigger: "blur" }],
  ip_type: [{ required: true, message: "请选择IP类型", trigger: "change" }]
};

const openDrawer = (title: string, row: Partial<UserLevel.ResUserLevel> = {}) => {
  drawerTitle.value = title;
  isEdit.value = !!row.id;

  // 重置表单
  formData.code = row.code || "";
  formData.name = row.name || "";
  formData.max_ip_count = row.max_ip_count ?? null;
  formData.ip_type = row.ip_type || "permanent";
  formData.daily_tokens_limit = row.daily_tokens_limit ?? null;
  formData.can_use_advanced_agent = row.can_use_advanced_agent || false;
  formData.unlimited_conversations = row.unlimited_conversations || false;
  formData.is_enabled = row.is_enabled !== undefined ? row.is_enabled : true;
  formData.sort_order = row.sort_order || 0;
  if (row.id) {
    formData.id = row.id;
  } else {
    delete formData.id;
  }

  drawerVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate();
  submitLoading.value = true;

  try {
    if (isEdit.value && formData.id) {
      // 编辑
      const { id, code, ...updateData } = formData;
      await updateUserLevel(id, updateData);
      ElMessage.success("更新成功");
    } else {
      // 新增
      const { id, ...createData } = formData;
      await createUserLevel(createData as UserLevel.ReqUserLevelCreate);
      ElMessage.success("创建成功");
    }
    drawerVisible.value = false;
    proTable.value?.getTableList();
  } catch (error: any) {
    ElMessage.error(error.msg || error.message || "操作失败");
  } finally {
    submitLoading.value = false;
  }
};

// 删除等级
const deleteLevel = async (row: UserLevel.ResUserLevel) => {
  await useHandleData(deleteUserLevel, row.id, `删除等级【${row.name}】`);
  proTable.value?.getTableList();
};

// 修改状态
const changeStatus = async (row: UserLevel.ResUserLevel) => {
  const newStatus = !row.is_enabled;
  const statusText = newStatus ? "启用" : "禁用";
  await useHandleData(
    () => updateUserLevel(row.id, { is_enabled: newStatus }),
    undefined,
    `${statusText}等级【${row.name}】`
  );
  proTable.value?.getTableList();
};
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>







