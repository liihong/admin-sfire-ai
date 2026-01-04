<template>
  <div class="permission-tree">
    <el-input
      v-if="showSearch"
      v-model="filterText"
      placeholder="输入关键字进行过滤"
      clearable
      class="search-input"
    />
    <el-scrollbar :style="{ height: scrollHeight }">
      <el-tree
        ref="treeRef"
        :data="props.data"
        :props="treeProps"
        :node-key="nodeKey"
        :default-expand-all="defaultExpandAll"
        :show-checkbox="true"
        :check-strictly="false"
        :default-checked-keys="checkedKeys"
        :filter-node-method="filterNode"
        @check="handleCheck"
      >
        <template #default="{ node, data }">
          <span class="tree-node-label">{{ data.label }}</span>
        </template>
      </el-tree>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts" name="PermissionTree">
import { ref, watch, nextTick } from "vue";
import { ElTree } from "element-plus";

/**
 * 权限树节点接口
 */
export interface PermissionTreeNode {
  id: number;
  label: string;
  children?: PermissionTreeNode[];
}

interface Props {
  /** 树形数据 */
  data: PermissionTreeNode[];
  /** 默认选中的节点ID数组 */
  checkedKeys?: number[];
  /** 是否显示搜索框 */
  showSearch?: boolean;
  /** 是否默认展开全部 */
  defaultExpandAll?: boolean;
  /** 滚动区域高度 */
  scrollHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  checkedKeys: () => [],
  showSearch: true,
  defaultExpandAll: false,
  scrollHeight: "400px"
});

const emit = defineEmits<{
  change: [keys: number[]];
}>();

const treeRef = ref<InstanceType<typeof ElTree>>();
const filterText = ref("");

const nodeKey = "id";
const treeProps = {
  children: "children",
  label: "label"
};

/** 过滤节点 */
const filterNode = (value: string, data: any) => {
  if (!value) return true;
  const nodeData = data as PermissionTreeNode;
  return nodeData.label.indexOf(value) !== -1;
};

/** 监听搜索框变化 */
watch(filterText, (val) => {
  treeRef.value?.filter(val);
});

/** 处理复选框变化 */
const handleCheck = () => {
  const checkedKeys = treeRef.value?.getCheckedKeys() as number[] || [];
  emit("change", checkedKeys);
};

/** 设置选中的节点 */
const setCheckedKeys = (keys: number[]) => {
  nextTick(() => {
    treeRef.value?.setCheckedKeys(keys, false);
  });
};

/** 获取选中的节点 */
const getCheckedKeys = (): number[] => {
  return (treeRef.value?.getCheckedKeys() as number[]) || [];
};

/** 清空选中 */
const clearChecked = () => {
  treeRef.value?.setCheckedKeys([], false);
  emit("change", []);
};

/** 展开全部 */
const expandAll = () => {
  const nodes = treeRef.value?.store.nodesMap;
  if (nodes) {
    Object.values(nodes).forEach((node: any) => {
      node.expanded = true;
    });
  }
};

/** 折叠全部 */
const collapseAll = () => {
  const nodes = treeRef.value?.store.nodesMap;
  if (nodes) {
    Object.values(nodes).forEach((node: any) => {
      node.expanded = false;
    });
  }
};

/** 暴露给父组件的方法 */
defineExpose({
  setCheckedKeys,
  getCheckedKeys,
  clearChecked,
  expandAll,
  collapseAll
});
</script>

<style scoped lang="scss">
.permission-tree {
  .search-input {
    margin-bottom: 12px;
  }
}

.tree-node-label {
  font-size: 14px;
}
</style>

