<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="管理员用户列表"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <el-button v-auth="'add'" type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增管理员</el-button>
      </template>

      <!-- 角色名称 -->
      <template #role_name="scope">
        <el-tag v-if="scope.row.role_name" type="info" effect="plain">
          {{ scope.row.role_name }}
        </el-tag>
        <span v-else class="text-gray-400">未分配</span>
      </template>

      <!-- 状态 -->
      <template #is_active="scope">
        <el-tag :type="scope.row.is_active ? 'success' : 'danger'" effect="plain">
          {{ scope.row.is_active ? "正常" : "封禁" }}
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
          {{ scope.row.is_active ? "封禁" : "启用" }}
        </el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteUser(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 用户编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="500px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" maxlength="64" show-word-limit :disabled="isEdit" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            maxlength="50"
            show-password
          />
        </el-form-item>
        <el-form-item v-else label="密码">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="留空则不修改密码"
            maxlength="50"
            show-password
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" maxlength="128" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="formData.role_id" placeholder="请选择角色" style="width: 100%" clearable>
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="formData.remark"
            type="textarea"
            placeholder="请输入备注"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="userManage">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Refresh } from "@element-plus/icons-vue";
import type { AdminUser, Role } from "@/api/interface";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import {
  getAdminUserList,
  addAdminUser,
  editAdminUser,
  deleteAdminUser as deleteAdminUserApi,
  changeAdminUserStatus
} from "@/api/modules/adminUser";
import { getRoleList } from "@/api/modules/role";

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 角色列表
const roleList = ref<Role.ResRole[]>([]);

// 数据回调处理
const dataCallback = (data: any) => {
  return {
    list: data.list || [],
    total: data.total || 0
  };
};

// 获取表格数据
const getTableList = (params: AdminUser.ReqAdminUserParams) => {
  return getAdminUserList(params);
};

// 获取角色列表
const loadRoleList = async () => {
  try {
    const res = await getRoleList();
    roleList.value = res.data?.list || [];
  } catch (error: any) {
    ElMessage.error(error.message || "获取角色列表失败");
  }
};

// 表格列配置
const columns = reactive<ColumnProps<AdminUser.ResAdminUserList>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "id",
    label: "ID",
    width: 80
  },
  {
    prop: "username",
    label: "用户名",
    width: 150,
    search: { el: "input" }
  },
  {
    prop: "email",
    label: "邮箱",
    width: 200,
    search: { el: "input" }
  },
  {
    prop: "role_id",
    label: "角色ID",
    width: 100
  },
  {
    prop: "role_name",
    label: "角色名称",
    width: 150
  },
  {
    prop: "role_code",
    label: "角色代码",
    width: 120
  },
  {
    prop: "is_active",
    label: "状态",
    width: 100
  },
  {
    prop: "remark",
    label: "备注",
    minWidth: 200,
    showOverflowTooltip: true
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

// ==================== 用户编辑抽屉 ====================
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive<AdminUser.ReqAdminUserCreate & AdminUser.ReqAdminUserUpdate & { id?: number }>({
  username: "",
  password: "",
  email: "",
  role_id: undefined,
  remark: ""
});

const formRules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [
    {
      required: true,
      message: "请输入密码",
      trigger: "blur",
      validator: (rule, value, callback) => {
        if (!isEdit.value && !value) {
          callback(new Error("请输入密码"));
        } else if (value && value.length < 6) {
          callback(new Error("密码至少6位"));
        } else {
          callback();
        }
      }
    }
  ],
  email: [
    {
      type: "email",
      message: "请输入正确的邮箱地址",
      trigger: "blur"
    }
  ]
};

const openDrawer = (title: string, row: Partial<AdminUser.ResAdminUserList> = {}) => {
  drawerTitle.value = title;
  isEdit.value = !!row.id;

  // 重置表单
  formData.username = row.username || "";
  formData.password = "";
  formData.email = row.email || "";
  formData.role_id = row.role_id || undefined;
  formData.remark = row.remark || "";
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
      const { id, username, ...updateData } = formData;
      // 如果密码为空，则不更新密码
      if (!updateData.password) {
        const { password, ...dataWithoutPassword } = updateData;
        await editAdminUser(id, dataWithoutPassword);
      } else {
        await editAdminUser(id, updateData);
      }
      ElMessage.success("编辑成功");
    } else {
      // 新增
      const { id, ...createData } = formData;
      await addAdminUser(createData as AdminUser.ReqAdminUserCreate);
      ElMessage.success("创建成功");
    }
    drawerVisible.value = false;
    proTable.value?.getTableList();
  } catch (error: any) {
    ElMessage.error(error.message || "操作失败");
  } finally {
    submitLoading.value = false;
  }
};

// 删除用户
const deleteUser = async (row: AdminUser.ResAdminUserList) => {
  await useHandleData(deleteAdminUserApi, row.id, `删除管理员【${row.username}】`);
  proTable.value?.getTableList();
};

// 修改状态
const changeStatus = async (row: AdminUser.ResAdminUserList) => {
  const newStatus = row.is_active ? 0 : 1;
  const statusText = newStatus === 1 ? "启用" : "封禁";
  await useHandleData(
    () => changeAdminUserStatus(row.id, newStatus),
    undefined,
    `${statusText}管理员【${row.username}】`
  );
  proTable.value?.getTableList();
};

// 初始化
onMounted(() => {
  loadRoleList();
});
</script>

<style scoped lang="scss">
.text-gray-400 {
  color: var(--el-text-color-secondary);
}
</style>

