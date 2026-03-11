<template>
  <div class="dashboard-container">
    <!-- OpenRouter 余额预警 -->
    <Transition name="alert-slide">
      <el-alert
        v-if="showAlert"
        :title="alertMessage"
        type="warning"
        show-icon
        :closable="true"
        class="balance-alert"
        @close="showAlert = false"
      >
        <template #default>
          <span>当前 OpenRouter 余额: <strong>{{ formatCurrency(statsData.apiBalance) }}</strong>，低于预警阈值 {{ formatCurrency(alertThreshold) }}，请及时充值！</span>
        </template>
      </el-alert>
    </Transition>

    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="12" :lg="6" :xl="6">
        <div class="stat-card card-users">
          <div class="card-icon">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">
              <CountUp :end-val="statsData.todayNewUsers" :duration="1.5" />
            </div>
            <div class="card-label">今日新增用户</div>
            <div class="card-trend" :class="statsData.userGrowthRate >= 0 ? 'up' : 'down'">
              <el-icon v-if="statsData.userGrowthRate >= 0"><CaretTop /></el-icon>
              <el-icon v-else><CaretBottom /></el-icon>
              <span>{{ Math.abs(statsData.userGrowthRate) }}%</span>
              <span class="trend-label">较昨日</span>
            </div>
          </div>
          <div class="card-bg"></div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="12" :lg="6" :xl="6">
        <div class="stat-card card-balance">
          <div class="card-icon">
            <el-icon><Wallet /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">
              <span class="currency">$</span>
              <CountUp :end-val="statsData.apiBalance" :decimals="2" :duration="1.5" />
            </div>
            <div class="card-label">OpenRouter 余额</div>
            <div class="card-extra">
              <el-tag :type="statsData.apiBalance > alertThreshold ? 'success' : 'danger'" size="small">
                {{ statsData.apiBalance > alertThreshold ? "余额充足" : "余额不足" }}
              </el-tag>
            </div>
          </div>
          <div class="card-bg"></div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="12" :lg="6" :xl="6">
        <div class="stat-card card-compute">
          <div class="card-icon">
            <el-icon><Lightning /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">
              <CountUp :end-val="statsData.todayComputeUsage" :duration="1.5" />
              <span class="unit">次</span>
            </div>
            <div class="card-label">今日算力消耗</div>
            <div class="card-trend" :class="statsData.computeGrowthRate >= 0 ? 'up' : 'down'">
              <el-icon v-if="statsData.computeGrowthRate >= 0"><CaretTop /></el-icon>
              <el-icon v-else><CaretBottom /></el-icon>
              <span>{{ Math.abs(statsData.computeGrowthRate) }}%</span>
              <span class="trend-label">较昨日</span>
            </div>
          </div>
          <div class="card-bg"></div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="12" :lg="6" :xl="6">
        <div class="stat-card card-order">
          <div class="card-icon">
            <el-icon><ShoppingCart /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">
              <span class="currency">¥</span>
              <CountUp :end-val="statsData.todayOrderAmount" :decimals="2" :duration="1.5" />
            </div>
            <div class="card-label">今日订单额</div>
            <div class="card-trend" :class="statsData.orderGrowthRate >= 0 ? 'up' : 'down'">
              <el-icon v-if="statsData.orderGrowthRate >= 0"><CaretTop /></el-icon>
              <el-icon v-else><CaretBottom /></el-icon>
              <span>{{ Math.abs(statsData.orderGrowthRate) }}%</span>
              <span class="trend-label">较昨日</span>
            </div>
          </div>
          <div class="card-bg"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 中间图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 左侧折线图 - 用户增长趋势 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="14" :xl="14">
        <div class="chart-card card">
          <div class="chart-header">
            <h3 class="chart-title">
              <el-icon><TrendCharts /></el-icon>
              7天用户增长趋势
            </h3>
            <div class="chart-actions">
              <el-radio-group v-model="trendType" size="small">
                <el-radio-button value="new">新增用户</el-radio-button>
                <el-radio-button value="active">活跃用户</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="chart-body">
            <ECharts :option="userTrendOption" :height="320" />
          </div>
        </div>
      </el-col>

      <!-- 右侧柱状图 - 智能体调用排行 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="10" :xl="10">
        <div class="chart-card card">
          <div class="chart-header">
            <h3 class="chart-title">
              <el-icon><Histogram /></el-icon>
              智能体调用排行 (Top 5)
            </h3>
            <el-button type="primary" link size="small" @click="refreshAgentRank">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          <div class="chart-body">
            <ECharts :option="agentRankOption" :height="320" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部信息栏 -->
    <div class="dashboard-footer">
      <div class="refresh-info">
        <el-icon class="rotating" v-if="isRefreshing"><Loading /></el-icon>
        <el-icon v-else><Clock /></el-icon>
        <span>{{ isRefreshing ? "数据刷新中..." : `上次更新: ${lastUpdateTime}` }}</span>
        <span class="next-refresh">（每 10 分钟自动刷新）</span>
      </div>
      <el-button type="primary" plain size="small" :loading="isRefreshing" @click="refreshAllData">
        <el-icon><Refresh /></el-icon>
        立即刷新
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts" name="home">
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import {
  UserFilled,
  Wallet,
  ShoppingCart,
  CaretTop,
  CaretBottom,
  TrendCharts,
  Histogram,
  Refresh,
  Clock,
  Loading,
  Lightning
} from "@element-plus/icons-vue";
import { ECOption } from "@/components/ECharts/config";
import ECharts from "@/components/ECharts/index.vue";
import CountUp from "./components/CountUp.vue";
import { getStatsData, getUserTrend, getAgentRank, Dashboard } from "@/api/modules/dashboard";

// ==================== 数据定义 ====================

// 核心统计数据
const statsData = reactive<Dashboard.StatsData>({
  todayNewUsers: 0,
  apiBalance: 0,
  todayComputeUsage: 0,
  todayOrderAmount: 0,
  userGrowthRate: 0,
  computeGrowthRate: 0,
  orderGrowthRate: 0
});

// 用户趋势数据
const userTrendData = ref<Dashboard.UserTrendItem[]>([]);
const trendType = ref<"new" | "active">("new");

// 智能体排行数据
const agentRankData = ref<Dashboard.AgentRankItem[]>([]);

// 预警相关（OpenRouter 余额低于此阈值时显示预警，单位：美元）
const showAlert = ref(false);
const alertThreshold = ref(5); // 默认预警阈值 $5
const alertMessage = ref("OpenRouter API 余额不足预警");

// 刷新相关
const isRefreshing = ref(false);
const lastUpdateTime = ref("");
let refreshTimer: ReturnType<typeof setInterval> | null = null;

// ==================== 图表配置 ====================

// 用户增长趋势图表配置
const userTrendOption = computed<ECOption>(() => {
  const data = userTrendData.value;
  const isNewUser = trendType.value === "new";

  return {
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255, 119, 0, 0.9)",
      borderColor: "#FF7700",
      textStyle: { color: "#fff" },
      formatter: (params: any) => {
        const item = params[0];
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: 600; margin-bottom: 4px;">${item.name}</div>
          <div>${isNewUser ? "新增用户" : "活跃用户"}: <strong>${item.value}</strong></div>
        </div>`;
      }
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: "10%",
      containLabel: true
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: data.map(item => item.date),
      axisLine: { lineStyle: { color: "#E5E7EB" } },
      axisLabel: { color: "#6B7280", fontSize: 12 },
      axisTick: { show: false }
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: "#F3F4F6", type: "dashed" } },
      axisLabel: { color: "#6B7280", fontSize: 12 }
    },
    series: [
      {
        name: isNewUser ? "新增用户" : "活跃用户",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        data: data.map(item => (isNewUser ? item.newUsers : item.activeUsers)),
        lineStyle: {
          width: 3,
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: "#FF7700" },
              { offset: 1, color: "#FFB366" }
            ]
          }
        },
        itemStyle: {
          color: "#FF7700",
          borderWidth: 2,
          borderColor: "#fff"
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(255, 119, 0, 0.3)" },
              { offset: 1, color: "rgba(255, 119, 0, 0.02)" }
            ]
          }
        }
      }
    ]
  };
});

// 智能体排行柱状图配置
const agentRankOption = computed<ECOption>(() => {
  const data = agentRankData.value;

  // 如果没有数据，返回空配置
  if (!data || data.length === 0) {
    return {
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "8%", bottom: "3%", top: "10%", containLabel: true },
      xAxis: { type: "value" },
      yAxis: { type: "category", data: [] },
      series: [{ type: "bar", data: [] }]
    };
  }

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "rgba(255, 119, 0, 0.9)",
      borderColor: "#FF7700",
      textStyle: { color: "#fff" },
      formatter: (params: any) => {
        const item = params[0];
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: 600; margin-bottom: 4px;">${item.name}</div>
          <div>调用次数: <strong>${item.value.toLocaleString()}</strong></div>
        </div>`;
      }
    },
    grid: {
      left: "140px", // 增加左侧空间以显示完整的智能体名称
      right: "8%",
      bottom: "3%",
      top: "10%",
      containLabel: false // 设置为 false，因为我们已经手动设置了 left
    },
    xAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: "#F3F4F6", type: "dashed" } },
      axisLabel: {
        color: "#6B7280",
        fontSize: 12,
        formatter: (value: number) => {
          if (value >= 10000) return (value / 10000).toFixed(0) + "w";
          if (value >= 1000) return (value / 1000).toFixed(0) + "k";
          return value.toString();
        }
      }
    },
    yAxis: {
      type: "category",
      data: data.map(item => item.name),
      axisLine: { lineStyle: { color: "#E5E7EB" } },
      axisLabel: {
        color: "#374151",
        fontSize: 13,
        formatter: (value: string) => {
          // 直接显示名称，如果名称过长则截断并显示省略号
          if (!value) return "";
          return value.length > 12 ? value.slice(0, 12) + "..." : value;
        },
        width: 120, // 设置标签宽度，确保长名称能显示
        overflow: "truncate" // 超出部分截断
      },
      axisTick: { show: false }
    },
    series: [
      {
        name: "调用次数",
        type: "bar",
        data: data.map((item, index) => ({
          value: item.call_count,
          itemStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: [
                { offset: 0, color: index === 0 ? "#FF7700" : "#FFB366" },
                { offset: 1, color: index === 0 ? "#FFB366" : "#FFD9B3" }
              ]
            },
            borderRadius: [0, 4, 4, 0]
          }
        })),
        barWidth: 20,
        label: {
          show: true,
          position: "right",
          color: "#6B7280",
          fontSize: 12,
          formatter: (params: any) => params.value.toLocaleString()
        }
      }
    ]
  };
});

// ==================== 方法定义 ====================

// 格式化货币（OpenRouter 余额单位为美元）
const formatCurrency = (value: number) => {
  return "$" + value.toLocaleString("zh-CN", { minimumFractionDigits: 2 });
};

// 获取当前时间
const getCurrentTime = () => {
  return new Date().toLocaleString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
};

// 获取统计数据（后端返回 overview + api_monitoring，需映射为前端格式）
const fetchStatsData = async () => {
  try {
    const { data } = await getStatsData();
    const overview = data?.overview || {};
    const apiMonitoring = data?.api_monitoring || {};
    // 优先使用 OpenRouter 余额，若无则用 OpenAI
    const balance = apiMonitoring.openrouter_balance ?? apiMonitoring.openai_balance ?? 0;
    const apiBalanceNum = typeof balance === "number" ? balance : parseFloat(balance) || 0;

    Object.assign(statsData, {
      todayNewUsers: overview.new_users_today ?? 0,
      apiBalance: apiBalanceNum,
      todayComputeUsage: apiMonitoring.today_api_calls ?? 0,
      todayOrderAmount: parseFloat(apiMonitoring.today_cost) || 0,
      userGrowthRate: 0,
      computeGrowthRate: 0,
      orderGrowthRate: 0
    });

    // 余额不足时显示预警
    if (apiBalanceNum < alertThreshold.value) {
      showAlert.value = true;
    } else {
      showAlert.value = false;
    }
  } catch (error) {
    // 使用模拟数据
    Object.assign(statsData, {
      todayNewUsers: 156,
      apiBalance: 8520.5,
      todayComputeUsage: 23456,
      todayOrderAmount: 12680.0,
      userGrowthRate: 12.5,
      computeGrowthRate: -5.2,
      orderGrowthRate: 8.3
    });
  }
};

// 获取用户趋势数据（后端返回 { date, count }，映射为 { date, newUsers, activeUsers }）
const fetchUserTrend = async () => {
  try {
    const { data } = await getUserTrend(7);
    userTrendData.value = (data || []).map((item: { date: string; count?: number }) => ({
      date: item.date,
      newUsers: item.count ?? 0,
      activeUsers: 0
    }));
  } catch (error) {
    // 使用模拟数据
    const today = new Date();
    userTrendData.value = Array.from({ length: 7 }, (_, i) => {
      const date = new Date(today);
      date.setDate(date.getDate() - (6 - i));
      return {
        date: `${date.getMonth() + 1}/${date.getDate()}`,
        newUsers: Math.floor(Math.random() * 200) + 50,
        activeUsers: Math.floor(Math.random() * 1000) + 500
      };
    });
  }
};

// 获取智能体排行数据
const fetchAgentRank = async () => {
  try {
    const { data } = await getAgentRank(5);
    agentRankData.value = data;
  } catch (error) {
    // 使用模拟数据
    agentRankData.value = [
      { id: "1", name: "智能客服", icon: "💬", call_count: 15680 },
      { id: "2", name: "文案助手", icon: "✍️", call_count: 12450 },
      { id: "3", name: "代码专家", icon: "💻", call_count: 9820 },
      { id: "4", name: "数据分析", icon: "📊", call_count: 7650 },
      { id: "5", name: "翻译大师", icon: "🌐", call_count: 5430 }
    ];
  }
};

// 刷新智能体排行
const refreshAgentRank = async () => {
  await fetchAgentRank();
  ElMessage.success("智能体排行已刷新");
};

// 刷新所有数据
const refreshAllData = async () => {
  isRefreshing.value = true;
  try {
    await Promise.all([fetchStatsData(), fetchUserTrend(), fetchAgentRank()]);
    lastUpdateTime.value = getCurrentTime();
    ElMessage.success("数据已刷新");
  } finally {
    isRefreshing.value = false;
  }
};

// 启动定时刷新
const startAutoRefresh = () => {
  // 每 10 分钟刷新一次
  refreshTimer = setInterval(
    () => {
      refreshAllData();
    },
    10 * 60 * 1000
  );
};

// 停止定时刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
};

// ==================== 生命周期 ====================

onMounted(async () => {
  // 初始化加载数据
  isRefreshing.value = true;
  await Promise.all([fetchStatsData(), fetchUserTrend(), fetchAgentRank()]);
  lastUpdateTime.value = getCurrentTime();
  isRefreshing.value = false;

  // 启动自动刷新
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 20px;
  min-height: 100%;
  background: var(--el-bg-color-page);
}

// 预警提示
.balance-alert {
  margin-bottom: 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;

  :deep(.el-alert__title) {
    font-weight: 600;
    color: #c2410c;
  }

  strong {
    color: #ea580c;
    font-family: "DIN", sans-serif;
  }
}

.alert-slide-enter-active,
.alert-slide-leave-active {
  transition: all 0.3s ease;
}

.alert-slide-enter-from,
.alert-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

// 统计卡片
.stats-row {
  margin-bottom: 20px;

  .el-col {
    margin-bottom: 20px;
  }
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  padding: 24px;
  border-radius: 12px;
  background: var(--el-bg-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  }

  .card-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20px;
    flex-shrink: 0;

    .el-icon {
      font-size: 28px;
      color: #fff;
    }
  }

  .card-content {
    flex: 1;
    position: relative;
    z-index: 1;
  }

  .card-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    font-family: "DIN", sans-serif;
    line-height: 1.2;
    margin-bottom: 4px;

    .currency {
      font-size: 18px;
      margin-right: 2px;
    }

    .unit {
      font-size: 14px;
      font-weight: 400;
      color: var(--el-text-color-secondary);
      margin-left: 4px;
    }
  }

  .card-label {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
  }

  .card-trend {
    display: flex;
    align-items: center;
    font-size: 13px;
    font-weight: 500;

    .el-icon {
      margin-right: 2px;
    }

    &.up {
      color: #10b981;
    }

    &.down {
      color: #ef4444;
    }

    .trend-label {
      margin-left: 6px;
      font-weight: 400;
      color: var(--el-text-color-placeholder);
    }
  }

  .card-extra {
    margin-top: 4px;
  }

  .card-bg {
    position: absolute;
    right: -20px;
    bottom: -20px;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    opacity: 0.1;
  }

  // 不同卡片的主题色
  &.card-users {
    .card-icon {
      background: linear-gradient(135deg, #ff7700 0%, #ffb366 100%);
    }
    .card-bg {
      background: #ff7700;
    }
  }

  &.card-balance {
    .card-icon {
      background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
    }
    .card-bg {
      background: #10b981;
    }
  }

  &.card-compute {
    .card-icon {
      background: linear-gradient(135deg, #6366f1 0%, #a5b4fc 100%);
    }
    .card-bg {
      background: #6366f1;
    }
  }

  &.card-order {
    .card-icon {
      background: linear-gradient(135deg, #f59e0b 0%, #fcd34d 100%);
    }
    .card-bg {
      background: #f59e0b;
    }
  }
}

// 图表区域
.charts-row {
  margin-bottom: 20px;

  .el-col {
    margin-bottom: 20px;
  }
}

.chart-card {
  border-radius: 12px;
  padding: 20px;
  background: var(--el-bg-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);

  .el-icon {
    color: #ff7700;
  }
}

.chart-body {
  height: 320px;
}

// 底部信息栏
.dashboard-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.refresh-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--el-text-color-secondary);

  .el-icon {
    font-size: 16px;
    color: #ff7700;
  }

  .next-refresh {
    color: var(--el-text-color-placeholder);
  }
}

// 旋转动画
.rotating {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;

    .card-icon {
      width: 48px;
      height: 48px;
      margin-right: 12px;

      .el-icon {
        font-size: 22px;
      }
    }

    .card-value {
      font-size: 22px;
    }
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .dashboard-footer {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
