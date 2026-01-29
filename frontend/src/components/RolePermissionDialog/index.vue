<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="700px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    destroy-on-close
    @close="handleClose"
  >
    <div class="role-permission-dialog">
      <!-- 角色信息 -->
      <div v-if="roleInfo.id" class="role-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="角色名称">
            <el-tag type="primary">{{ roleInfo.name }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="角色代码">
            <el-tag>{{ roleInfo.code }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="角色描述" :span="2">
            {{ roleInfo.description || "暂无描述" }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 权限树 -->
      <div class="permission-tree-container">
        <div class="tree-header">
          <span class="tree-title">菜单权限</span>
          <div class="tree-actions">
            <el-button size="small" text @click="expandAll">展开全部</el-button>
            <el-button size="small" text @click="collapseAll">折叠全部</el-button>
            <el-button size="small" text @click="selectAll">全选</el-button>
            <el-button size="small" text @click="clearAll">清空</el-button>
          </div>
        </div>
        <PermissionTree
          v-if="dialogVisible && treeData.length > 0"
          ref="permissionTreeRef"
          :data="treeData"
          :checked-keys="checkedKeys"
          :show-search="true"
          :default-expand-all="false"
          scroll-height="400px"
          @change="handlePermissionChange"
        />
        <el-empty v-else description="暂无菜单数据" :image-size="100" />
      </div>

      <!-- 统计信息 -->
      <div class="permission-stats">
        <el-text type="info">
          已选择 <el-text type="primary" tag="strong">{{ checkedCount }}</el-text> 个菜单权限
        </el-text>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleConfirm">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts" name="RolePermissionDialog">
import { ref, computed, watch } from "vue";
import { ElMessage } from "element-plus";
import PermissionTree from "@/components/PermissionTree/index.vue";
import type { PermissionTreeNode } from "@/components/PermissionTree/index.vue";

/**
 * 角色信息接口
 */
export interface RoleInfo {
  id: number;
  name: string;
  code: string;
  description?: string;
}

interface Props {
  /** 角色信息 */
  roleInfo?: RoleInfo;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  /** 确认提交 */
  confirm: [menuIds: number[]];
  /** 取消 */
  cancel: [];
}>();

const dialogVisible = ref(false);
const dialogTitle = ref("分配权限");
const submitLoading = ref(false);
const permissionTreeRef = ref<InstanceType<typeof PermissionTree>>();

const roleInfo = ref<RoleInfo>({
  id: 0,
  name: "",
  code: ""
});
const treeData = ref<PermissionTreeNode[]>([]);
const checkedKeys = ref<number[]>([]);
const currentCheckedKeys = ref<number[]>([]);

/** 已选择的权限数量 */
const checkedCount = computed(() => currentCheckedKeys.value.length);

/** 打开对话框 */
const open = async (role: RoleInfo, menus: PermissionTreeNode[], selectedMenuIds: number[] = []) => {
  roleInfo.value = { ...role };
  dialogTitle.value = `为角色【${role.name}】分配权限`;
  dialogVisible.value = true;
  treeData.value = menus;
  checkedKeys.value = selectedMenuIds;
  currentCheckedKeys.value = [...selectedMenuIds];

  // 等待DOM更新后设置选中状态
  await new Promise((resolve) => setTimeout(resolve, 100));
  permissionTreeRef.value?.setCheckedKeys(selectedMenuIds);
};

/** 关闭对话框 */
const close = () => {
  dialogVisible.value = false;
};

/** 处理权限变化 */
const handlePermissionChange = (keys: number[]) => {
  currentCheckedKeys.value = keys;
};

/** 展开全部 */
const expandAll = () => {
  permissionTreeRef.value?.expandAll();
};

/** 折叠全部 */
const collapseAll = () => {
  permissionTreeRef.value?.collapseAll();
};

/** 全选 */
const selectAll = () => {
  const allKeys: number[] = [];
  const collectKeys = (nodes: PermissionTreeNode[]) => {
    nodes.forEach((node) => {
      allKeys.push(node.id);
      if (node.children && node.children.length > 0) {
        collectKeys(node.children);
      }
    });
  };
  collectKeys(treeData.value);
  permissionTreeRef.value?.setCheckedKeys(allKeys);
  currentCheckedKeys.value = allKeys;
};

/** 清空 */
const clearAll = () => {
  permissionTreeRef.value?.clearChecked();
  currentCheckedKeys.value = [];
};

/** 处理确认 */
const handleConfirm = async () => {
  const keys = permissionTreeRef.value?.getCheckedKeys() || [];
  emit("confirm", keys);
};

/** 处理取消 */
const handleCancel = () => {
  handleClose();
  emit("cancel");
};

/** 处理关闭 */
const handleClose = () => {
  dialogVisible.value = false;
  // 重置状态
  roleInfo.value = { id: 0, name: "", code: "" };
  treeData.value = [];
  checkedKeys.value = [];
  currentCheckedKeys.value = [];
  submitLoading.value = false;
};

/** 设置提交加载状态 */
const setLoading = (loading: boolean) => {
  submitLoading.value = loading;
};

/** 暴露给父组件的方法和属性 */
defineExpose({
  open,
  close,
  setLoading,
  roleInfo
});
</script>

<style scoped lang="scss">
.role-permission-dialog {
  .role-info {
    margin-bottom: 20px;
    padding: 16px;
    background-color: var(--el-fill-color-extra-light);
    border-radius: 4px;
  }

  .permission-tree-container {
    .tree-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .tree-title {
        font-size: 16px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }

      .tree-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .permission-stats {
    margin-top: 16px;
    padding: 12px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;
    text-align: center;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>


































