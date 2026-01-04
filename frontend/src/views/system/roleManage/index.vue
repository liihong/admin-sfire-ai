<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="角色列表"
      :columns="columns"
      :request-api="getTableList"
      :data-callback="dataCallback"
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <!-- 角色是系统预定义的，暂不支持新增 -->
        <el-button v-auth="'add'" type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增角色</el-button>
      </template>

      <!-- 角色代码 -->
      <template #code="scope">
        <el-tag :type="getCodeTagType(scope.row.code)" effect="plain">
          {{ scope.row.code }}
        </el-tag>
      </template>

      <!-- 用户数量 -->
      <template #userCount="scope">
        <el-tag type="info" effect="plain">
          {{ scope.row.user_count }} 人
        </el-tag>
      </template>

      <!-- 表格操作 -->
      <template #operation="scope">
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', scope.row)">编辑</el-button>
        <el-button type="warning" link :icon="Key" @click="openPermissionDialog(scope.row)">分配权限</el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteRole(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 角色编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="500px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入角色名称" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="角色代码" prop="code">
          <el-select v-model="formData.code" placeholder="请选择角色代码" style="width: 100%">
            <el-option label="normal - 普通用户" value="normal" />
            <el-option label="member - 会员" value="member" />
            <el-option label="partner - 合伙人" value="partner" />
          </el-select>
          <div class="form-tip">系统预定义代码，只能选择已存在的角色代码</div>
        </el-form-item>
        <el-form-item v-else label="角色代码">
          <el-input :value="formData.code" disabled />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            placeholder="请输入角色描述"
            :rows="4"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="999" controls-position="right" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>

    <!-- 权限分配对话框 -->
    <RolePermissionDialog ref="permissionDialogRef" @confirm="handlePermissionConfirm" />
  </div>
</template>

<script setup lang="ts" name="roleManage">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen, Key } from "@element-plus/icons-vue";
import { Role } from "@/api/interface";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getRoleList, addRole, editRole, deleteRole as deleteRoleApi } from "@/api/modules/role";
import RolePermissionDialog from "@/components/RolePermissionDialog/index.vue";
import { useRolePermission } from "@/hooks/useRolePermission";
import type { RoleInfo } from "@/components/RolePermissionDialog/index.vue";

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
const getTableList = () => {
  return getRoleList();
};

// 角色代码标签类型
const getCodeTagType = (code: string): "success" | "info" | "warning" | "danger" => {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    normal: "info",
    member: "warning",
    partner: "danger"
  };
  return typeMap[code] || "info";
};

// 表格列配置
const columns = reactive<ColumnProps<Role.ResRole>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "name",
    label: "角色名称",
    width: 150,
    search: { el: "input" }
  },
  {
    prop: "code",
    label: "角色代码",
    width: 120
  },
  {
    prop: "description",
    label: "角色描述",
    minWidth: 200
  },
  {
    prop: "user_count",
    label: "用户数量",
    width: 120
  },
  {
    prop: "sort_order",
    label: "排序",
    width: 100
  },
  { prop: "operation", label: "操作", fixed: "right", width: 280 }
]);

// ==================== 角色编辑抽屉 ====================
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive<Role.ReqRoleCreate & { id?: number }>({
  name: "",
  code: "",
  description: "",
  sort_order: 0
});

const formRules: FormRules = {
  name: [{ required: true, message: "请输入角色名称", trigger: "blur" }],
  code: [
    { required: true, message: "请输入角色代码", trigger: "blur" },
    {
      pattern: /^(normal|member|partner)$/,
      message: "角色代码必须是：normal、member 或 partner",
      trigger: "blur"
    }
  ]
};

const openDrawer = (title: string, row: Partial<Role.ResRole> = {}) => {
  drawerTitle.value = title;
  isEdit.value = !!row.id;

  // 重置表单
  formData.name = row.name || "";
  formData.code = row.code || "";
  formData.description = row.description || "";
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
      await editRole(id, updateData);
      ElMessage.success("编辑成功");
    } else {
      // 新增（实际上是对现有角色代码的配置）
      await addRole(formData);
      ElMessage.success("配置成功");
    }
    drawerVisible.value = false;
    proTable.value?.getTableList();
  } catch (error: any) {
    ElMessage.error(error.message || "操作失败");
  } finally {
    submitLoading.value = false;
  }
};

// 删除角色
const deleteRole = async (row: Role.ResRole) => {
  await useHandleData(deleteRoleApi, row.id, `删除角色【${row.name}】`);
  proTable.value?.getTableList();
};

// ==================== 权限分配 ====================
const permissionDialogRef = ref<InstanceType<typeof RolePermissionDialog>>();
const { menuTree, loadMenuTree, loadRolePermissions, saveRolePermissions } = useRolePermission();

/** 打开权限分配对话框 */
const openPermissionDialog = async (row: Role.ResRole) => {
  if (!permissionDialogRef.value) return;

  try {
    // 加载菜单树（如果还未加载）
    if (menuTree.value.length === 0) {
      await loadMenuTree();
    }

    // 加载角色的已分配权限
    const menuIds = await loadRolePermissions(row.id);

    // 打开对话框
    const roleInfo: RoleInfo = {
      id: row.id,
      name: row.name,
      code: row.code,
      description: row.description
    };

    permissionDialogRef.value.open(roleInfo, menuTree.value, menuIds);
  } catch (error: unknown) {
    const err = error as { message?: string };
    ElMessage.error(err.message || "加载权限数据失败");
  }
};

/** 处理权限确认 */
const handlePermissionConfirm = async (menuIds: number[]) => {
  if (!permissionDialogRef.value) return;

  const currentRoleInfo = permissionDialogRef.value.roleInfo;
  const roleId = currentRoleInfo?.id;
  if (!roleId) {
    ElMessage.error("角色信息不存在");
    return;
  }

  permissionDialogRef.value.setLoading(true);

  try {
    const success = await saveRolePermissions(roleId, menuIds);
    if (success) {
      permissionDialogRef.value.close();
    }
  } catch (error: unknown) {
    const err = error as { message?: string };
    ElMessage.error(err.message || "保存权限失败");
  } finally {
    permissionDialogRef.value.setLoading(false);
  }
};

// 初始化菜单树
onMounted(() => {
  loadMenuTree();
});
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
