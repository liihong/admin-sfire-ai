/**
 * v-auth
 * 按钮权限指令
 *
 * 使用方式：
 * 1. 基础用法：v-auth="'add'" - 检查当前页面是否有 add 权限
 * 2. 数组用法：v-auth="['add', 'edit']" - 检查是否同时拥有多个权限
 * 3. 全局权限：v-auth:global="'FINANCE_APPROVE'" - 检查全局权限码
 * 4. 等级限制：v-auth:level="1" - 检查用户等级是否 >= 1
 */
import { useAuthStore } from "@/stores/modules/auth";
import { useUserStore } from "@/stores/modules/user";
import type { Directive, DirectiveBinding } from "vue";

const auth: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value, arg } = binding;
    const authStore = useAuthStore();
    const userStore = useUserStore();

    let hasPermission = false;

    // 根据修饰符判断权限类型
    switch (arg) {
      case "global":
        // 全局权限码检查（如：FINANCE_APPROVE）
        hasPermission = checkGlobalPermission(value, authStore);
        break;
      case "level":
        // 用户等级检查
        hasPermission = checkUserLevel(value, userStore);
        break;
      default:
        // 默认：当前页面按钮权限
        hasPermission = checkPagePermission(value, authStore);
    }

    if (!hasPermission) {
      el.remove();
    }
  }
};

/**
 * 检查当前页面按钮权限
 */
const checkPagePermission = (value: string | string[], authStore: ReturnType<typeof useAuthStore>): boolean => {
  const currentPageRoles = authStore.authButtonListGet[authStore.routeName] ?? [];

  if (value instanceof Array && value.length) {
    return value.every(item => currentPageRoles.includes(String(item)));
  }
  return currentPageRoles.includes(String(value));
};

/**
 * 检查全局权限码
 */
const checkGlobalPermission = (value: string | string[], authStore: ReturnType<typeof useAuthStore>): boolean => {
  // 获取所有页面的权限列表，合并为全局权限
  const allPermissions = Object.values(authStore.authButtonListGet).flat();

  if (value instanceof Array && value.length) {
    return value.every(item => allPermissions.includes(String(item)));
  }
  return allPermissions.includes(String(value));
};

/**
 * 检查用户等级
 * @param requiredLevel 所需的最低等级（0-普通, 1-会员, 2-合伙人）
 */
const checkUserLevel = (requiredLevel: number, userStore: ReturnType<typeof useUserStore>): boolean => {
  const userLevel = userStore.userInfo?.level ?? 0;
  // 将字符串等级转换为数字进行比较
  const levelMap: Record<string, number> = {
    free: 0,
    v1: 1,
    v2: 2,
    v3: 3
  };
  const currentLevel = typeof userLevel === "string" ? (levelMap[userLevel] ?? 0) : userLevel;
  return currentLevel >= requiredLevel;
};

export default auth;
