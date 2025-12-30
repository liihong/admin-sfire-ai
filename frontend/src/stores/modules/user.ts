import { defineStore } from "pinia";
import { UserState, UserInfo, UserLevelConfig } from "@/stores/interface";
import piniaPersistConfig from "@/stores/helper/persist";
import { loginApi } from "@/api/modules/login";
import { Login } from "@/api/interface";
import { ElMessage } from "element-plus";

// 默认用户信息
const defaultUserInfo: UserInfo = {
  id: "",
  username: "",
  avatar: "",
  email: "",
  phone: "",
  level: "free",
  computePower: 0,
  totalUsed: 0
};

export const useUserStore = defineStore({
  id: "sfire-user",
  state: (): UserState => ({
    token: "",
    userInfo: { ...defaultUserInfo },
    roles: []
  }),
  getters: {
    // 获取用户等级名称
    levelName: state => {
      return UserLevelConfig[state.userInfo.level]?.name || "未知等级";
    },
    // 获取用户折扣
    discount: state => {
      return UserLevelConfig[state.userInfo.level]?.discount || 1;
    },
    // 获取每日限额
    dailyLimit: state => {
      return UserLevelConfig[state.userInfo.level]?.dailyLimit || 0;
    },
    // 是否已登录
    isLogin: state => {
      return !!state.token && !!state.userInfo.id;
    },
    // 是否是会员
    isVip: state => {
      return state.userInfo.level !== "free";
    },
    // 是否有足够算力
    hasComputePower: state => {
      return state.userInfo.computePower > 0;
    }
  },
  actions: {
    // 设置 Token
    setToken(token: string) {
      this.token = token;
    },
    // 设置用户信息
    setUserInfo(userInfo: Partial<UserInfo>) {
      this.userInfo = { ...this.userInfo, ...userInfo };
    },
    // 设置用户角色
    setRoles(roles: string[]) {
      this.roles = roles;
    },
    // 更新算力
    updateComputePower(amount: number) {
      this.userInfo.computePower = Math.max(0, this.userInfo.computePower + amount);
    },
    // 消耗算力
    consumeComputePower(amount: number) {
      const discountedAmount = Math.ceil(amount * this.discount);
      this.userInfo.computePower = Math.max(0, this.userInfo.computePower - discountedAmount);
      this.userInfo.totalUsed += discountedAmount;
    },
    // 用户登录
    async login(loginForm: Login.ReqLoginForm) {
      try {
        // 调用登录接口
        const { data } = await loginApi(loginForm);

        // 保存 Token
        // 后端返回格式: { code: 200, data: { access_token: "..." }, msg: "..." }
        // axios 拦截器已经提取了 data，所以这里直接使用
        if (data?.access_token) {
          this.setToken(data.access_token);
          // TODO: 如果后端返回用户信息，可以在这里设置
          // this.setUserInfo({ ... });
          return true;
        } else {
          ElMessage.error("登录失败：未获取到 Token");
          return false;
        }
      } catch (error: any) {
        console.error("登录失败:", error);
        ElMessage.error(error?.msg || "登录失败，请检查用户名和密码");
        return false;
      }
    },
    // 重置用户状态（退出登录）
    resetUser() {
      this.token = "";
      this.userInfo = { ...defaultUserInfo };
      this.roles = [];
    }
  },
  persist: piniaPersistConfig("sfire-user")
});
