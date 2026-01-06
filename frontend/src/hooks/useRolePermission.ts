import { ref } from "vue";
import { ElMessage } from "element-plus";
import { getAllMenus } from "@/api/modules/menu";
import { getRolePermissions, setRolePermissions } from "@/api/modules/role";
import type { Menu } from "@/api/interface";
import type { PermissionTreeNode } from "@/components/PermissionTree/index.vue";

/**
 * 角色权限管理 Hook
 */
export const useRolePermission = () => {
  const menuTree = ref<PermissionTreeNode[]>([]);

  /**
   * 将菜单列表转换为权限树节点
   */
  const convertMenuToTreeNode = (menus: Menu.ResMenuList[]): PermissionTreeNode[] => {
    return menus.map((menu) => ({
      id: menu.id,
      label: menu.title,
      children: menu.children ? convertMenuToTreeNode(menu.children) : undefined
    }));
  };

  /**
   * 加载菜单树
   */
  const loadMenuTree = async (): Promise<void> => {
    try {
      const response = await getAllMenus();
      if (response.data) {
        menuTree.value = convertMenuToTreeNode(response.data);
      }
    } catch (error: any) {
      ElMessage.error(error.message || "加载菜单树失败");
      throw error;
    }
  };

  /**
   * 加载角色权限
   */
  const loadRolePermissions = async (roleId: number): Promise<number[]> => {
    try {
      const response = await getRolePermissions(roleId);
      if (response.data && response.data.menu_ids) {
        return response.data.menu_ids;
      }
      return [];
    } catch (error: any) {
      ElMessage.error(error.message || "加载角色权限失败");
      throw error;
    }
  };

  /**
   * 保存角色权限
   */
  const saveRolePermissions = async (roleId: number, menuIds: number[]): Promise<boolean> => {
    try {
      await setRolePermissions(roleId, { menu_ids: menuIds });
      ElMessage.success("保存权限成功");
      return true;
    } catch (error: any) {
      ElMessage.error(error.message || "保存权限失败");
      throw error;
    }
  };

  return {
    menuTree,
    loadMenuTree,
    loadRolePermissions,
    saveRolePermissions
  };
};




