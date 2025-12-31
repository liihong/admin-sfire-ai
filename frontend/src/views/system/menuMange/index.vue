<template>
  <div class="table-box">
    <ProTable
      ref="proTable"
      title="菜单列表"
      row-key="id"
      :indent="20"
      :columns="columns"
      :data="menuData"
      :pagination="false"
      :tool-button="false"
      :tree-props="{ children: 'children' }"
      default-expand-all
    >
      <!-- 表格 header 按钮 -->
      <template #tableHeader>
        <el-button v-auth="'add'" type="primary" :icon="CirclePlus" @click="openDrawer('新增')">新增菜单</el-button>
      </template>

      <!-- 菜单图标 -->
      <template #icon="scope">
        <el-icon :size="18">
          <component :is="scope.row.icon"></component>
        </el-icon>
      </template>

      <!-- 状态 -->
      <template #isEnabled="scope">
        <el-tag :type="scope.row.isEnabled ? 'success' : 'danger'" effect="plain">
          {{ scope.row.isEnabled ? "启用" : "禁用" }}
        </el-tag>
      </template>

      <!-- 表格操作 -->
      <template #operation="scope">
        <el-button type="primary" link :icon="EditPen" @click="openDrawer('编辑', scope.row)">编辑</el-button>
        <el-button type="danger" link :icon="Delete" @click="deleteMenu(scope.row)">删除</el-button>
      </template>
    </ProTable>

    <!-- 菜单编辑抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="600px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="父菜单" prop="parent_id">
          <el-tree-select
            v-model="formData.parent_id"
            :data="parentMenuOptions"
            :props="{ label: 'title', children: 'children' }"
            placeholder="请选择父菜单（不选则为顶级菜单）"
            check-strictly
            clearable
            style="width: 100%"
          />
          <div class="form-tip">选择父菜单后，当前菜单将成为其子菜单</div>
        </el-form-item>

        <el-form-item label="菜单标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入菜单标题" maxlength="64" show-word-limit />
        </el-form-item>

        <el-form-item label="路由名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入路由名称（唯一标识）" maxlength="64" show-word-limit :disabled="isEdit" />
          <div class="form-tip">路由名称必须唯一，且与前端组件的name属性一致</div>
        </el-form-item>

        <el-form-item label="路由路径" prop="path">
          <el-input v-model="formData.path" placeholder="请输入路由路径，如：/user/index" maxlength="256" show-word-limit />
        </el-form-item>

        <el-form-item label="组件路径" prop="component">
          <el-input v-model="formData.component" placeholder="请输入组件路径，如：/user/index（相对于src/views）" maxlength="256" show-word-limit />
          <div class="form-tip">相对于 src/views 的路径，留空表示无组件（仅作为菜单分组）</div>
        </el-form-item>

        <el-form-item label="重定向路径" prop="redirect">
          <el-input v-model="formData.redirect" placeholder="请输入重定向路径" maxlength="256" show-word-limit />
        </el-form-item>

        <el-form-item label="菜单图标" prop="icon">
          <SelectIcon v-model:icon-value="formData.icon" placeholder="请选择菜单图标" />
        </el-form-item>

        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="999" controls-position="right" style="width: 100%" />
        </el-form-item>

        <el-divider content-position="left">Meta 选项</el-divider>

        <el-form-item label="是否隐藏" prop="is_hide">
          <el-switch v-model="formData.is_hide" />
          <div class="form-tip">隐藏后不会在菜单栏显示，但仍可通过路径访问</div>
        </el-form-item>

        <el-form-item label="是否全屏" prop="is_full">
          <el-switch v-model="formData.is_full" />
          <div class="form-tip">全屏显示模式，如数据大屏页面</div>
        </el-form-item>

        <el-form-item label="是否固定标签" prop="is_affix">
          <el-switch v-model="formData.is_affix" />
          <div class="form-tip">固定后标签页不可关闭</div>
        </el-form-item>

        <el-form-item label="是否缓存" prop="is_keep_alive">
          <el-switch v-model="formData.is_keep_alive" />
          <div class="form-tip">开启后页面会被KeepAlive缓存</div>
        </el-form-item>

        <el-form-item label="外链地址" prop="is_link">
          <el-input v-model="formData.is_link" placeholder="请输入外链地址（留空表示非外链）" maxlength="512" show-word-limit />
        </el-form-item>

        <el-form-item label="高亮菜单" prop="active_menu">
          <el-input v-model="formData.active_menu" placeholder="详情页时需要高亮的菜单路径" maxlength="256" show-word-limit />
          <div class="form-tip">用于详情页等高亮父菜单</div>
        </el-form-item>

        <el-divider content-position="left">扩展选项</el-divider>

        <el-form-item label="权限标识" prop="perms">
          <el-input v-model="formData.perms" placeholder="请输入权限标识，如：user:add" maxlength="256" show-word-limit />
        </el-form-item>

        <el-form-item label="用户等级要求" prop="required_level">
          <el-select v-model="formData.required_level" placeholder="请选择用户等级要求" clearable style="width: 100%">
            <el-option label="免费用户" value="free" />
            <el-option label="V1会员" value="v1" />
            <el-option label="V2会员" value="v2" />
            <el-option label="V3会员" value="v3" />
          </el-select>
        </el-form-item>

        <el-form-item label="所需最低算力" prop="required_compute_power">
          <el-input-number v-model="formData.required_compute_power" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>

        <el-form-item label="消耗算力" prop="consume_compute_power">
          <el-input-number v-model="formData.consume_compute_power" :min="0" controls-position="right" style="width: 100%" />
          <div class="form-tip">每次访问该页面消耗的算力</div>
        </el-form-item>

        <el-form-item label="是否启用" prop="is_enabled">
          <el-switch v-model="formData.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="tsx" name="menuMange">
import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormRules } from "element-plus";
import { CirclePlus, Delete, EditPen } from "@element-plus/icons-vue";
import { Menu } from "@/api/interface/index";
import { useHandleData } from "@/hooks/useHandleData";
import ProTable from "@/components/ProTable/index.vue";
import { ProTableInstance, ColumnProps } from "@/components/ProTable/interface";
import { getAllMenus, addMenu, editMenu, deleteMenu as deleteMenuApi, getMenuDetail } from "@/api/modules/menu";
import SelectIcon from "@/components/SelectIcon/index.vue";

// ProTable 实例
const proTable = ref<ProTableInstance>();

// 菜单数据
const menuData = ref<Menu.ResMenuList[]>([]);

// 加载菜单数据
const loadMenuData = async () => {
  try {
    const res = await getAllMenus();
    menuData.value = res.data || [];
  } catch (error: any) {
    ElMessage.error(error.message || "获取菜单列表失败");
  }
};

// 表格列配置
const columns = reactive<ColumnProps<Menu.ResMenuList>[]>([
  { type: "index", label: "#", width: 60 },
  {
    prop: "title",
    label: "菜单名称",
    align: "left",
    minWidth: 150,
    search: { el: "input" }
  },
  {
    prop: "icon",
    label: "图标",
    width: 100
  },
  {
    prop: "name",
    label: "路由名称",
    minWidth: 150,
    search: { el: "input" }
  },
  {
    prop: "path",
    label: "路由路径",
    minWidth: 200,
    search: { el: "input" }
  },
  {
    prop: "component",
    label: "组件路径",
    minWidth: 200
  },
  {
    prop: "sortOrder",
    label: "排序",
    width: 100
  },
  {
    prop: "isEnabled",
    label: "状态",
    width: 100
  },
  { prop: "operation", label: "操作", fixed: "right", width: 180 }
]);

// ==================== 菜单编辑抽屉 ====================
const drawerVisible = ref(false);
const drawerTitle = ref("");
const isEdit = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive<Menu.ReqMenuCreate & Menu.ReqMenuUpdate & { id?: number; icon: string }>({
  parent_id: null,
  name: "",
  path: "",
  component: null,
  redirect: null,
  sort_order: 0,
  icon: "Menu",
  title: "",
  is_link: "",
  is_hide: false,
  is_full: false,
  is_affix: false,
  is_keep_alive: true,
  active_menu: null,
  perms: null,
  required_level: null,
  required_compute_power: null,
  consume_compute_power: null,
  is_enabled: true
});

const formRules: FormRules = {
  name: [{ required: true, message: "请输入路由名称", trigger: "blur" }],
  path: [{ required: true, message: "请输入路由路径", trigger: "blur" }],
  title: [{ required: true, message: "请输入菜单标题", trigger: "blur" }]
};

// 递归获取所有菜单ID（包括子菜单），用于排除父菜单选择
const getAllMenuIds = (menus: Menu.ResMenuList[], excludeId?: number): number[] => {
  const ids: number[] = [];
  menus.forEach(menu => {
    if (menu.id !== excludeId) {
      ids.push(menu.id);
      if (menu.children && menu.children.length > 0) {
        ids.push(...getAllMenuIds(menu.children, excludeId));
      }
    }
  });
  return ids;
};

// 递归构建父菜单选项树（编辑时排除自身及其子菜单）
const buildParentMenuOptions = (menus: Menu.ResMenuList[], excludeId?: number): any[] => {
  return menus
    .filter(menu => menu.id !== excludeId)
    .map(menu => {
      const item: any = {
        id: menu.id,
        title: menu.title,
        children: menu.children && menu.children.length > 0 ? buildParentMenuOptions(menu.children, excludeId) : undefined
      };
      return item;
    });
};

// 父菜单选项
const parentMenuOptions = computed(() => {
  if (isEdit.value && formData.id) {
    // 编辑时排除自身及其所有子菜单
    return buildParentMenuOptions(menuData.value, formData.id);
  }
  // 新增时返回所有菜单
  return buildParentMenuOptions(menuData.value);
});

const openDrawer = async (title: string, row: Partial<Menu.ResMenuList> = {}) => {
  drawerTitle.value = title;
  isEdit.value = !!row.id;

  // 重置表单
  formData.parent_id = null;
  formData.name = "";
  formData.path = "";
  formData.component = null;
  formData.redirect = null;
  formData.sort_order = 0;
  formData.icon = "Menu";
  formData.title = "";
  formData.is_link = "";
  formData.is_hide = false;
  formData.is_full = false;
  formData.is_affix = false;
  formData.is_keep_alive = true;
  formData.active_menu = null;
  formData.perms = null;
  formData.required_level = null;
  formData.required_compute_power = null;
  formData.consume_compute_power = null;
  formData.is_enabled = true;

  if (row.id) {
    // 编辑模式：获取详细信息
    try {
      const res = await getMenuDetail(row.id);
      const detail = res.data;
      formData.id = detail.id;
      formData.parent_id = detail.parentId;
      formData.name = detail.name;
      formData.path = detail.path;
      formData.component = detail.component || null;
      formData.redirect = detail.redirect || null;
      formData.sort_order = detail.sortOrder;
      formData.icon = detail.icon;
      formData.title = detail.title;
      formData.is_link = detail.isLink || "";
      formData.is_hide = detail.isHide;
      formData.is_full = detail.isFull;
      formData.is_affix = detail.isAffix;
      formData.is_keep_alive = detail.isKeepAlive;
      formData.active_menu = detail.activeMenu || null;
      formData.perms = detail.perms || null;
      formData.required_level = detail.requiredLevel || null;
      formData.required_compute_power = detail.requiredComputePower || null;
      formData.consume_compute_power = detail.consumeComputePower || null;
      formData.is_enabled = detail.isEnabled;
    } catch (error: any) {
      ElMessage.error(error.message || "获取菜单详情失败");
      return;
    }
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
      const { id, ...updateData } = formData;
      await editMenu(id, updateData as Menu.ReqMenuUpdate);
      ElMessage.success("编辑成功");
    } else {
      // 新增
      const { id, ...createData } = formData;
      await addMenu(createData as Menu.ReqMenuCreate);
      ElMessage.success("创建成功");
    }
    drawerVisible.value = false;
    await loadMenuData();
  } catch (error: any) {
    ElMessage.error(error.message || "操作失败");
  } finally {
    submitLoading.value = false;
  }
};

// 删除菜单
const deleteMenu = async (row: Menu.ResMenuList) => {
  // 检查是否有子菜单
  const hasChildren = row.children && row.children.length > 0;
  const message = hasChildren
    ? `删除菜单【${row.title}】将级联删除所有子菜单，确定要删除吗？`
    : `确定要删除菜单【${row.title}】吗？`;

  await useHandleData(deleteMenuApi, row.id, message);
  await loadMenuData();
};

// 初始化
onMounted(() => {
  loadMenuData();
});
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}
</style>
