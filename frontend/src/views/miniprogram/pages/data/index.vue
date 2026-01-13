<template>
  <div class="mp-data">
    <el-row :gutter="20">
      <!-- 数据概览 -->
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in stats" :key="stat.label">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">{{ stat.label }}</p>
              <p class="stat-value">{{ stat.value }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <span>项目使用趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <span>算力消耗分布</span>
          </template>
          <div ref="powerChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 使用记录 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>使用记录</span>
      </template>
      <el-table :data="records" v-loading="recordsLoading" stripe>
        <el-table-column prop="typeName" label="类型" width="120" />
        <el-table-column prop="amount" label="消耗算力" width="120">
          <template #default="{ row }">
            <span :class="row.amount < 0 ? 'positive' : 'negative'">
              {{ row.amount > 0 ? "+" : "" }}{{ Math.abs(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="beforeBalance" label="变动前" width="120">
          <template #default="{ row }">
            {{ Number(row.beforeBalance) }}
          </template>
        </el-table-column>
        <el-table-column prop="afterBalance" label="变动后" width="120">
          <template #default="{ row }">
            {{ Number(row.afterBalance) }}
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        <el-table-column prop="createTime" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.createTime) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchRecords"
          @current-change="fetchRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts" name="MPData">
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { FolderOpened, DataAnalysis, Coin, TrendCharts } from "@element-plus/icons-vue";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import { getMPProjectListApi, getMPComputeRecordsApi, getMPCoinStatisticsApi } from "@/api/modules/miniprogram";
import type { MPComputeRecord, MPCoinStatistics } from "@/api/modules/miniprogram";
import * as echarts from "echarts";
import dayjs from "dayjs";

const mpUserStore = useMPUserStore();

// 统计数据
const stats = reactive([
  {
    label: "项目总数",
    value: "0",
    icon: "FolderOpened",
    color: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
  },
  {
    label: "算力余额",
    value: mpUserStore.userDetail?.power || "0",
    icon: "Coin",
    color: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
  },
  {
    label: "累计消耗",
    value: "0",
    icon: "DataAnalysis",
    color: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
  },
  {
    label: "使用趋势",
    value: "↑ 0%",
    icon: "TrendCharts",
    color: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
  }
]);

// 图表
const trendChartRef = ref<HTMLElement>();
const powerChartRef = ref<HTMLElement>();
let trendChart: echarts.ECharts | null = null;
let powerChart: echarts.ECharts | null = null;

// 使用记录
const records = ref<MPComputeRecord[]>([]);
const recordsLoading = ref(false);
const pageNum = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 算力统计数据
const statistics = ref<MPCoinStatistics | null>(null);

// 获取项目列表
const fetchProjects = async () => {
  try {
    const { data } = await getMPProjectListApi();
    if (data?.projects) {
      stats[0].value = String(data.projects.length);
    }
  } catch (error) {
    console.error("获取项目列表失败:", error);
  }
};

// 获取算力统计数据
const fetchStatistics = async () => {
  try {
    const response = await getMPCoinStatisticsApi();
    if (response?.data) {
      statistics.value = response.data;
      // 更新统计卡片
      stats[2].value = String(Math.abs(response.data.totalConsume || 0));
    }
  } catch (error: any) {
    console.error("获取算力统计失败:", error);
  }
};

// 获取使用记录
const fetchRecords = async () => {
  recordsLoading.value = true;
  try {
    const response = await getMPComputeRecordsApi({
      pageNum: pageNum.value,
      pageSize: pageSize.value
    });
    if (response?.data) {
      records.value = response.data.list || [];
      total.value = response.data.total || 0;
    } else {
      records.value = [];
      total.value = 0;
    }
  } catch (error: any) {
    console.error("获取使用记录失败:", error);
    records.value = [];
    total.value = 0;
  } finally {
    recordsLoading.value = false;
  }
};

// 初始化趋势图
const initTrendChart = () => {
  if (!trendChartRef.value) return;

  trendChart = echarts.init(trendChartRef.value);
  const option = {
    tooltip: {
      trigger: "axis"
    },
    xAxis: {
      type: "category",
      data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    },
    yAxis: {
      type: "value"
    },
    series: [
      {
        data: [0, 0, 0, 0, 0, 0, 0],
        type: "line",
        smooth: true,
        areaStyle: {}
      }
    ]
  };
  trendChart.setOption(option);
};

// 初始化算力消耗分布图
const initPowerChart = () => {
  if (!powerChartRef.value) return;

  powerChart = echarts.init(powerChartRef.value);
  const option = {
    tooltip: {
      trigger: "item"
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        data: [
          { value: 0, name: "项目创建" },
          { value: 0, name: "内容生成" },
          { value: 0, name: "其他" }
        ]
      }
    ]
  };
  powerChart.setOption(option);
};

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format("YYYY-MM-DD HH:mm:ss");
};

// 更新图表尺寸
const resizeCharts = () => {
  trendChart?.resize();
  powerChart?.resize();
};

onMounted(async () => {
  // 更新统计数据
  stats[1].value = mpUserStore.userDetail?.power || "0";

  // 获取项目列表
  await fetchProjects();

  // 获取算力统计数据
  await fetchStatistics();

  // 获取使用记录
  await fetchRecords();

  // 初始化图表
  setTimeout(() => {
    initTrendChart();
    initPowerChart();
    window.addEventListener("resize", resizeCharts);
  }, 100);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  trendChart?.dispose();
  powerChart?.dispose();
});
</script>

<style scoped lang="scss">
.mp-data {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 20px;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
      }

      .stat-info {
        flex: 1;

        .stat-label {
          margin: 0 0 8px;
          color: var(--el-text-color-regular);
          font-size: 14px;
        }

        .stat-value {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }
    }
  }

  .chart-container {
    width: 100%;
    height: 300px;
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }

  .positive {
    color: var(--el-color-success);
  }

  .negative {
    color: var(--el-color-danger);
  }
}
</style>















