import { useUserStore } from "@/stores/modules/user";

/**
 * 获取当前用户的 Token
 * @returns {string} 用户 Token
 */
export function getToken(): string {
  const userStore = useUserStore();
  return userStore.token || "";
}

