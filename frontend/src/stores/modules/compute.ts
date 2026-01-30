import { defineStore } from "pinia";
import { ComputeState } from "@/stores/interface";
import { getComputeBalance, getUserLevel } from "@/api/modules/ai";
import piniaPersistConfig from "@/stores/helper/persist";

export const useComputeStore = defineStore({
  id: "sfire-compute",
  state: (): ComputeState => ({
    balance: {
      total: 0,
      used: 0,
      remaining: 0,
      expireTime: undefined
    },
    userLevel: {
      level: 0,
      levelName: "免费用户",
      discount: 1,
      dailyLimit: 100,
      features: []
    },
    todayUsed: 0,
    loading: false
  }),
  getters: {
    // 获取剩余算力百分比
    remainingPercentage: state => {
      if (state.balance.total === 0) return 0;
      return Math.round((state.balance.remaining / state.balance.total) * 100);
    },
    // 判断算力是否充足
    hasEnoughBalance: state => {
      return state.balance.remaining > 0;
    },
    // 判断是否达到每日限制
    isReachedDailyLimit: state => {
      return state.todayUsed >= state.userLevel.dailyLimit;
    },
    // 获取折扣后的算力消耗
    getDiscountedCost: state => (cost: number) => {
      return Math.ceil(cost * state.userLevel.discount);
    }
  },
  actions: {
    // 获取算力余额
    async fetchBalance() {
      this.loading = true;
      try {
        const { data } = await getComputeBalance();
        this.balance = data;
      } catch (error) {
        console.error("获取算力余额失败:", error);
      } finally {
        this.loading = false;
      }
    },
    // 获取用户等级
    async fetchUserLevel() {
      try {
        const { data } = await getUserLevel();
        this.userLevel = data;
      } catch (error) {
        console.error("获取用户等级失败:", error);
      }
    },
    // 消耗算力
    consumeBalance(amount: number) {
      const discountedAmount = this.getDiscountedCost(amount);
      this.balance.used += discountedAmount;
      this.balance.remaining -= discountedAmount;
      this.todayUsed += discountedAmount;
    },
    // 重置每日使用量（每日零点调用）
    resetDailyUsage() {
      this.todayUsed = 0;
    },
    // 更新余额（用于实时同步）
    updateBalance(balance: Partial<ComputeState["balance"]>) {
      this.balance = { ...this.balance, ...balance };
    },
    // 初始化算力数据
    async initComputeData() {
      await Promise.all([this.fetchBalance(), this.fetchUserLevel()]);
    }
  },
  persist: piniaPersistConfig("sfire-compute")
});





































