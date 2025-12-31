<template>
  <div class="permission-tree">
    <!-- 搜索框 -->
    <div v-if="showSearch" class="search-box">
      <el-input
        v-model="filterText"
        placeholder="输入关键字进行过滤"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <!-- 树形选择器 -->
    <el-scrollbar :height="scrollHeight" class="tree-scrollbar">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :show-checkbox="true"
        :check-strictly="false"
        :default-expand-all="defaultExpandAll"
        :expand-on-click-node="false"
        :filter-node-method="filterNode"
        node-key="id"
        :default-checked-keys="checkedKeys"
        @check="handleCheck"
      >
        <template #default="{ node, data }">
          <span class="tree-node-label">
            <el-icon v-if="data.icon" class="node-icon">
              <component :is="data.icon" />
            </el-icon>
            <span class="node-title">{{ data.title || data.label }}</span>
            <el-tag v-if="data.perms" size="small" type="info" effect="plain" class="perms-tag">
              {{ data.perms }}
            </el-tag>
          </span>
        </template>
      </el-tree>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts" name="PermissionTree">
import { ref, watch, nextTick, onMounted } from "vue";
import { ElTree, ElMessage } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import type { TreeNodeData } from "element-plus/es/components/tree/src/tree.type";

/**
 * 权限树节点数据结构
 */
export interface PermissionTreeNode {
  id: number;
  title: string;
  label?: string;
  icon?: string;
  perms?: string;
  children?: PermissionTreeNode[];
  [key: string]: unknown;
}

interface Props {
  /** 树形数据 */
  data: PermissionTreeNode[];
  /** 已选中的节点ID数组 */
  checkedKeys?: number[];
  /** 树节点属性配置 */
  props?: {
    children?: string;
    label?: string;
  };
  /** 是否显示搜索框 */
  showSearch?: boolean;
  /** 是否默认展开所有节点 */
  defaultExpandAll?: boolean;
  /** 滚动区域高度 */
  scrollHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  checkedKeys: () => [],
  props: () => ({
    children: "children",
    label: "title"
  }),
  showSearch: true,
  defaultExpandAll: true,
  scrollHeight: "400px"
});

const emit = defineEmits<{
  /** 节点选中状态变化 */
  change: [checkedKeys: number[], checkedNodes: PermissionTreeNode[], halfCheckedKeys: number[]];
}>();

const treeRef = ref<InstanceType<typeof ElTree>>();
const filterText = ref("");
const treeData = ref<PermissionTreeNode[]>([]);

/** 树节点属性配置 */
const treeProps = {
  children: props.props.children || "children",
  label: props.props.label || "title"
};

/** 初始化树数据 */
const initTreeData = () => {
  treeData.value = props.data;
};

/** 过滤节点 */
const filterNode = (value: string, data: TreeNodeData) => {
  if (!value) return true;
  const label = (data.title as string) || (data.label as string) || "";
  return label.toLowerCase().includes(value.toLowerCase());
};

/** 监听搜索文本变化 */
watch(
  () => filterText.value,
  (val) => {
    treeRef.value?.filter(val);
  }
);

/** 监听数据变化 */
watch(
  () => props.data,
  () => {
    initTreeData();
    nextTick(() => {
      // 重新设置选中状态
      if (props.checkedKeys.length > 0) {
        treeRef.value?.setCheckedKeys(props.checkedKeys);
      }
    });
  },
  { deep: true, immediate: true }
);

/** 监听选中键变化 */
watch(
  () => props.checkedKeys,
  (newKeys) => {
    if (treeRef.value) {
      const currentKeys = treeRef.value.getCheckedKeys() as number[];
      // 只有当外部传入的keys与当前keys不同时才更新
      if (JSON.stringify(currentKeys.sort()) !== JSON.stringify([...newKeys].sort())) {
        treeRef.value.setCheckedKeys(newKeys);
      }
    }
  },
  { deep: true }
);

/** 处理节点选中事件 */
const handleCheck = (
  data: PermissionTreeNode,
  checkedInfo: {
    checkedKeys: number[];
    checkedNodes: PermissionTreeNode[];
    halfCheckedKeys: number[];
  }
) => {
  // 获取所有选中和半选的节点
  const { checkedKeys, checkedNodes, halfCheckedKeys } = checkedInfo;
  
  emit("change", checkedKeys as number[], checkedNodes, halfCheckedKeys as number[]);
};

/** 获取所有选中的节点ID */
const getCheckedKeys = (): number[] => {
  return (treeRef.value?.getCheckedKeys() || []) as number[];
};

/** 获取所有半选的节点ID */
const getHalfCheckedKeys = (): number[] => {
  return (treeRef.value?.getHalfCheckedKeys() || []) as number[];
};

/** 获取所有选中的节点 */
const getCheckedNodes = (): PermissionTreeNode[] => {
  return (treeRef.value?.getCheckedNodes() || []) as PermissionTreeNode[];
};

/** 设置选中的节点 */
const setCheckedKeys = (keys: number[]) => {
  treeRef.value?.setCheckedKeys(keys);
};

/** 清空所有选中状态 */
const clearChecked = () => {
  treeRef.value?.setCheckedKeys([]);
};

/** 展开所有节点 */
const expandAll = () => {
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
  allKeys.forEach((key) => {
    treeRef.value?.store.nodesMap[key]?.expand();
  });
};

/** 折叠所有节点 */
const collapseAll = () => {
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
  allKeys.forEach((key) => {
    treeRef.value?.store.nodesMap[key]?.collapse();
  });
};

/** 暴露给父组件的方法 */
defineExpose({
  getCheckedKeys,
  getHalfCheckedKeys,
  getCheckedNodes,
  setCheckedKeys,
  clearChecked,
  expandAll,
  collapseAll
});

onMounted(() => {
  initTreeData();
});
</script>

<style scoped lang="scss">
.permission-tree {
  width: 100%;

  .search-box {
    margin-bottom: 12px;
  }

  .tree-scrollbar {
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    padding: 8px;
  }

  .tree-node-label {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;

    .node-icon {
      font-size: 16px;
      color: var(--el-text-color-regular);
    }

    .node-title {
      flex: 1;
    }

    .perms-tag {
      margin-left: auto;
    }
  }

  :deep(.el-tree-node__content) {
    height: 32px;
    line-height: 32px;

    &:hover {
      background-color: var(--el-fill-color-light);
    }
  }

  :deep(.el-checkbox) {
    margin-right: 8px;
  }
}
</style>

