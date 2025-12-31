import { ref, Ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { getAllMenus } from "@/api/modules/menu";
import { getRolePermissions, setRolePermissions } from "@/api/modules/role";
import type { Menu } from "@/api/interface";
import type { PermissionTreeNode } from "@/components/PermissionTree/index.vue";

/**
 * 角色权限管理 Hook
 * 
 * @description 用于管理角色的菜单权限分配，包括：
 * - 获取菜单树数据
 * - 获取角色的已分配权限
 * - 保存角色的权限配置
 * 
 * @example
 * ```ts
 * const { 
 *   menuTree, 
 *   loading, 
 *   loadMenuTree, 
 *   loadRolePermissions, 
 *   saveRolePermissions 
 * } = useRolePermission();
 * ```
 */
export function useRolePermission() {
  /** 菜单树数据 */
  const menuTree = ref<PermissionTreeNode[]>([]);
  
  /** 加载状态 */
  const loading = ref(false);

  /**
   * 将菜单数据转换为权限树节点格式
   * 
   * @param menus 菜单数据
   * @returns 权限树节点数组
   */
  const convertToPermissionTree = (menus: Menu.ResMenuList[]): PermissionTreeNode[] => {
    return menus.map((menu) => ({
      id: menu.id,
      title: menu.title,
      label: menu.title,
      icon: menu.icon,
      perms: menu.perms || undefined,
      children: menu.children ? convertToPermissionTree(menu.children) : undefined
    }));
  };

  /**
   * 加载菜单树数据
   * 
   * @description 从后端获取所有菜单，并转换为权限树格式
   * @returns Promise<void>
   */
  const loadMenuTree = async (): Promise<void> => {
    try {
      loading.value = true;
      const res = await getAllMenus();
      menuTree.value = convertToPermissionTree(res.data || []);
    } catch (error: unknown) {
      const err = error as { message?: string };
      ElMessage.error(err.message || "加载菜单数据失败");
      menuTree.value = [];
    } finally {
      loading.value = false;
    }
  };

  /**
   * 加载角色的已分配权限
   * 
   * @param roleId 角色ID
   * @returns Promise<number[]> 已分配的菜单ID数组
   */
  const loadRolePermissions = async (roleId: number): Promise<number[]> => {
    try {
      loading.value = true;
      const res = await getRolePermissions(roleId);
      return res.data?.menu_ids || [];
    } catch (error: unknown) {
      const err = error as { message?: string };
      ElMessage.error(err.message || "加载角色权限失败");
      return [];
    } finally {
      loading.value = false;
    }
  };

  /**
   * 保存角色的权限配置
   * 
   * @param roleId 角色ID
   * @param menuIds 菜单ID数组
   * @returns Promise<boolean> 是否保存成功
   */
  const saveRolePermissions = async (roleId: number, menuIds: number[]): Promise<boolean> => {
    try {
      loading.value = true;
      await setRolePermissions(roleId, menuIds);
      ElMessage.success("权限分配成功");
      return true;
    } catch (error: unknown) {
      const err = error as { message?: string };
      ElMessage.error(err.message || "保存权限配置失败");
      return false;
    } finally {
      loading.value = false;
    }
  };

  return {
    menuTree,
    loading,
    loadMenuTree,
    loadRolePermissions,
    saveRolePermissions
  };
}

