import { defineStore } from "pinia";
import piniaPersistConfig from "@/stores/helper/persist";
import { wechatLoginApi, accountLoginApi, getMPUserInfoApi, getMPUserDetailInfoApi, updateMPUserInfoApi } from "@/api/modules/miniprogram";
import type {
  WechatLoginRequest,
  WechatLoginResponse,
  MPUserInfo,
  MPUserDetailInfo,
  UpdateMPUserRequest
} from "@/api/modules/miniprogram";
import { ElMessage } from "element-plus";

/**
 * 小程序用户信息
 */
export interface MPUserInfoState {
  openid: string;
  nickname: string;
  avatarUrl: string;
  gender?: number;
  city?: string;
  province?: string;
  country?: string;
}

/**
 * 小程序用户详细信息
 */
export interface MPUserDetailState {
  phone: string;
  avatar: string;
  nickname: string;
  power: string; // 算力余额
  partnerBalance: string; // 合伙人资产余额
  partnerStatus: string; // 合伙人状态
  expireDate?: string; // 会员到期时间
}

/**
 * 小程序用户 Store 状态
 */
interface MPUserState {
  token: string;
  userInfo: MPUserInfoState;
  userDetail: MPUserDetailState | null;
}

// 默认用户信息
const defaultUserInfo: MPUserInfoState = {
  openid: "",
  nickname: "",
  avatarUrl: "",
  gender: 0,
  city: "",
  province: "",
  country: ""
};

// 默认用户详细信息
const defaultUserDetail: MPUserDetailState = {
  phone: "",
  avatar: "",
  nickname: "",
  power: "0",
  partnerBalance: "0.00",
  partnerStatus: "普通用户",
  expireDate: undefined
};

export const useMPUserStore = defineStore({
  id: "sfire-mp-user",
  state: (): MPUserState => ({
    token: "",
    userInfo: { ...defaultUserInfo },
    userDetail: null
  }),
  getters: {
    // 是否已登录
    isLogin: state => {
      return !!state.token && !!state.userInfo.openid;
    },
    // 获取算力余额（数字）
    computePower: state => {
      return parseFloat(state.userDetail?.power || "0");
    },
    // 获取合伙人资产余额（数字）
    partnerBalance: state => {
      return parseFloat(state.userDetail?.partnerBalance || "0");
    }
  },
  actions: {
    // 设置 Token
    setToken(token: string) {
      this.token = token;
    },
    // 设置用户信息
    setUserInfo(userInfo: Partial<MPUserInfoState>) {
      this.userInfo = { ...this.userInfo, ...userInfo };
    },
    // 设置用户详细信息
    setUserDetail(userDetail: Partial<MPUserDetailState>) {
      if (!this.userDetail) {
        this.userDetail = { ...defaultUserDetail };
      }
      this.userDetail = { ...this.userDetail, ...userDetail };
    },
    // 微信登录
    async wechatLogin(params: WechatLoginRequest) {
      try {
        const { data } = await wechatLoginApi(params);
        if (data?.token && data?.userInfo) {
          this.setToken(data.token);
          this.setUserInfo(data.userInfo);
          // 登录成功后获取详细信息
          await this.fetchUserDetail();
          return true;
        } else {
          ElMessage.error("登录失败：未获取到 Token");
          return false;
        }
      } catch (error: any) {
        console.error("微信登录失败:", error);
        ElMessage.error(error?.msg || "登录失败，请稍后重试");
        return false;
      }
    },
    // 获取用户信息
    async fetchUserInfo() {
      try {
        const { data } = await getMPUserInfoApi();
        if (data?.userInfo) {
          this.setUserInfo(data.userInfo);
          return true;
        }
        return false;
      } catch (error: any) {
        console.error("获取用户信息失败:", error);
        return false;
      }
    },
    // 获取用户详细信息
    async fetchUserDetail() {
      try {
        const { data } = await getMPUserDetailInfoApi();
        if (data) {
          this.setUserDetail(data);
          return true;
        }
        return false;
      } catch (error: any) {
        console.error("获取用户详细信息失败:", error);
        return false;
      }
    },
    // 更新用户信息
    async updateUserInfo(params: UpdateMPUserRequest) {
      try {
        const { data } = await updateMPUserInfoApi(params);
        if (data?.userInfo) {
          this.setUserInfo(data.userInfo);
          // 如果更新了头像或昵称，也更新详细信息
          if (params.avatar !== undefined || params.nickname !== undefined) {
            await this.fetchUserDetail();
          }
          ElMessage.success("更新成功");
          return true;
        }
        return false;
      } catch (error: any) {
        console.error("更新用户信息失败:", error);
        ElMessage.error(error?.msg || "更新失败，请稍后重试");
        return false;
      }
    },
    // 重置用户状态（退出登录）
    resetUser() {
      this.token = "";
      this.userInfo = { ...defaultUserInfo };
      this.userDetail = null;
    },
    // 手机号+密码登录
    async accountLogin(params: { phone: string; password: string }) {
      try {
        const { data } = await accountLoginApi(params);
        if (data?.token && data?.userInfo) {
          this.setToken(data.token);
          this.setUserInfo(data.userInfo);
          // 登录成功后获取详细信息
          await this.fetchUserDetail();
          return true;
        } else {
          ElMessage.error("登录失败：未获取到 Token");
          return false;
        }
      } catch (error: any) {
        console.error("账号登录失败:", error);
        ElMessage.error(error?.msg || "登录失败，请稍后重试");
        return false;
      }
    }
  },
  persist: piniaPersistConfig("sfire-mp-user")
});

