import { ref, computed, onMounted, onUnmounted } from "vue";
import { useComputeStore } from "@/stores/modules/compute";
import { storeToRefs } from "pinia";

/**
 * @description 算力实时计算 Hook
 * @param autoRefresh 是否自动刷新余额（默认 true）
 * @param refreshInterval 刷新间隔（毫秒，默认 30000）
 */
export const useCompute = (autoRefresh: boolean = true, refreshInterval: number = 30000) => {
  const computeStore = useComputeStore();
  const { balance, userLevel, todayUsed, loading } = storeToRefs(computeStore);

  // 实时消耗的 tokens 数量（用于流式对话时的实时计算）
  const realtimeTokens = ref(0);
  // 刷新定时器
  let refreshTimer: ReturnType<typeof setInterval> | null = null;

  // 计算预估消耗
  const estimatedCost = computed(() => {
    return computeStore.getDiscountedCost(realtimeTokens.value);
  });

  // 计算剩余可用 tokens（考虑实时消耗）
  const availableTokens = computed(() => {
    return Math.max(0, balance.value.remaining - estimatedCost.value);
  });

  // 是否可以继续对话
  const canContinue = computed(() => {
    return availableTokens.value > 0 && !computeStore.isReachedDailyLimit;
  });

  // 格式化算力显示
  const formatBalance = (value: number): string => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(2) + "M";
    } else if (value >= 1000) {
      return (value / 1000).toFixed(2) + "K";
    }
    return value.toString();
  };

  // 开始计算实时消耗
  const startRealtimeCount = () => {
    realtimeTokens.value = 0;
  };

  // 更新实时消耗
  const updateRealtimeTokens = (tokens: number) => {
    realtimeTokens.value = tokens;
  };

  // 确认消耗（对话结束后调用）
  const confirmConsumption = () => {
    if (realtimeTokens.value > 0) {
      computeStore.consumeBalance(realtimeTokens.value);
      realtimeTokens.value = 0;
    }
  };

  // 取消消耗（对话取消时调用）
  const cancelConsumption = () => {
    realtimeTokens.value = 0;
  };

  // 检查是否有足够算力执行操作
  const checkBalance = (requiredTokens: number): boolean => {
    const discountedCost = computeStore.getDiscountedCost(requiredTokens);
    return balance.value.remaining >= discountedCost;
  };

  // 刷新余额
  const refreshBalance = async () => {
    await computeStore.fetchBalance();
  };

  // 启动自动刷新
  const startAutoRefresh = () => {
    if (refreshTimer) return;
    refreshTimer = setInterval(refreshBalance, refreshInterval);
  };

  // 停止自动刷新
  const stopAutoRefresh = () => {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  };

  // 组件挂载时初始化
  onMounted(async () => {
    await computeStore.initComputeData();
    if (autoRefresh) {
      startAutoRefresh();
    }
  });

  // 组件卸载时清理
  onUnmounted(() => {
    stopAutoRefresh();
  });

  return {
    // 状态
    balance,
    userLevel,
    todayUsed,
    loading,
    realtimeTokens,
    estimatedCost,
    availableTokens,
    canContinue,

    // 方法
    formatBalance,
    startRealtimeCount,
    updateRealtimeTokens,
    confirmConsumption,
    cancelConsumption,
    checkBalance,
    refreshBalance,
    startAutoRefresh,
    stopAutoRefresh
  };
};








































