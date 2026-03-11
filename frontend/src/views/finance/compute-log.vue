<template>
  <div class="compute-log-page">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="12" :lg="12" :xl="12">
        <div class="stat-card stat-consume">
          <div class="card-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ formatNumber(stats.totalConsume) }}</div>
            <div class="card-label">系统算力总消耗</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="12" :xl="12">
        <div class="stat-card stat-recharge">
          <div class="card-icon">
            <el-icon><Wallet /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ formatNumber(stats.totalRecharge) }}</div>
            <div class="card-label">系统算力总充值</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 用户汇总表格 -->
    <div class="table-box">
      <ProTable
        ref="proTable"
        title="用户算力汇总"
        row-key="userId"
        :columns="columns"
        :request-api="getTableList"
        :init-param="initParam"
        :data-callback="dataCallback"
      >
        <template #totalConsume="scope">
          <span class="amount consume">{{ formatNumber(scope.row.totalConsume) }}</span>
        </template>
        <template #totalRecharge="scope">
          <span class="amount recharge">{{ formatNumber(scope.row.totalRecharge) }}</span>
        </template>
        <template #operation="scope">
          <el-button type="primary" link :icon="View" @click="openDetailDrawer(scope.row)">
            详情
          </el-button>
        </template>
      </ProTable>
    </div>

    <!-- 用户算力明细抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`用户 ${detailUser?.username || detailUser?.userId || '-'} 的算力明细`"
      size="600px"
      destroy-on-close
      @close="resetDetail"
    >
      <div v-loading="detailLoading" class="detail-content">
        <div v-if="detailUser" class="detail-filters">
          <el-select
            v-model="detailLogType"
            placeholder="流水类型"
            clearable
            style="width: 140px"
            @change="loadUserLogs"
          >
            <el-option label="全部" value="" />
            <el-option label="消耗" value="consume" />
            <el-option label="充值" value="recharge" />
          </el-select>
        </div>
        <el-table :data="detailLogs" border stripe>
          <el-table-column prop="typeName" label="类型" width="90" />
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.type === 'recharge' ? 'amount recharge' : 'amount consume'">
                <template v-if="row.type === 'recharge' && row.paymentAmount != null">
                  ¥{{ row.paymentAmount.toFixed(2) }}
                </template>
                <template v-else>
                  {{ row.amount >= 0 ? '+' : '' }}{{ row.amount }}
                </template>
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="beforeBalance" label="变动前" width="100" align="right">
            <template #default="{ row }">{{ formatNumber(row.beforeBalance) }}</template>
          </el-table-column>
          <el-table-column prop="afterBalance" label="变动后" width="100" align="right">
            <template #default="{ row }">{{ formatNumber(row.afterBalance) }}</template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
          <el-table-column prop="createTime" label="时间" width="180">
            <template #default="{ row }">{{ formatTime(row.createTime) }}</template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="detailPageNum"
          v-model:page-size="detailPageSize"
          :total="detailTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="detail-pagination"
          @size-change="loadUserLogs"
          @current-change="loadUserLogs"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts" name="financeComputeLog">
import { ref, reactive, onMounted } from "vue";
import { View, TrendCharts, Wallet } from "@element-plus/icons-vue";
import ProTable from "@/components/ProTable/index.vue";
import type { ProTableInstance } from "@/components/ProTable/interface";
import type { ColumnProps } from "@/components/ProTable/interface";
import {
  getComputeStats,
  getComputeUserSummary,
  getUserComputeLogs,
  type ComputeStats,
  type UserComputeSummary,
  type ComputeLogItem
} from "@/api/modules/compute";

// 顶部统计
const stats = reactive<ComputeStats>({
  totalConsume: 0,
  totalRecharge: 0
});

// 表格
const proTable = ref<ProTableInstance>();
const initParam = reactive<Record<string, unknown>>({});
const dataCallback = (data: { list: UserComputeSummary[]; total: number }) => ({
  list: data.list,
  total: data.total
});

const getTableList = (params: Record<string, unknown>) => {
  return getComputeUserSummary({
    pageNum: (params.pageNum as number) || 1,
    pageSize: (params.pageSize as number) || 10,
    username: params.username as string | undefined,
    startTime: params.startTime as string | undefined,
    endTime: params.endTime as string | undefined
  });
};

const columns = reactive<ColumnProps<UserComputeSummary>[]>([
  { type: "index", label: "#", width: 60 },
  { prop: "userId", label: "用户ID", width: 100 },
  {
    prop: "username",
    label: "用户名",
    width: 140,
    search: { el: "input", props: { placeholder: "用户名模糊搜索" } }
  },
  { prop: "phone", label: "手机号", width: 130 },
  { prop: "totalConsume", label: "总消耗", width: 120 },
  { prop: "totalRecharge", label: "总充值", width: 120 },
  { prop: "operation", label: "操作", fixed: "right", width: 100 }
]);

// 详情抽屉
const drawerVisible = ref(false);
const detailLoading = ref(false);
const detailUser = ref<UserComputeSummary | null>(null);
const detailLogs = ref<ComputeLogItem[]>([]);
const detailLogType = ref<string>("");
const detailPageNum = ref(1);
const detailPageSize = ref(10);
const detailTotal = ref(0);

const openDetailDrawer = (row: UserComputeSummary) => {
  detailUser.value = row;
  detailLogType.value = "";
  detailPageNum.value = 1;
  detailPageSize.value = 10;
  drawerVisible.value = true;
  loadUserLogs();
};

const loadUserLogs = async () => {
  if (!detailUser.value) return;
  detailLoading.value = true;
  try {
    const { data } = await getUserComputeLogs(parseInt(detailUser.value.userId), {
      pageNum: detailPageNum.value,
      pageSize: detailPageSize.value,
      type: detailLogType.value ? (detailLogType.value as "consume" | "recharge") : undefined
    });
    detailLogs.value = data?.list ?? [];
    detailTotal.value = data?.total ?? 0;
  } finally {
    detailLoading.value = false;
  }
};

const resetDetail = () => {
  detailUser.value = null;
  detailLogs.value = [];
  detailTotal.value = 0;
};

// 工具函数
const formatNumber = (val: number | undefined): string => {
  if (val == null || isNaN(val)) return "0";
  if (val >= 1000000) return (val / 1000000).toFixed(2) + "M";
  if (val >= 1000) return (val / 1000).toFixed(2) + "K";
  return Math.round(val).toString();
};

const formatTime = (val: string | undefined): string => {
  if (!val) return "-";
  try {
    const d = new Date(val);
    return d.toLocaleString("zh-CN");
  } catch {
    return val;
  }
};

// 加载系统统计
const loadStats = async () => {
  try {
    const { data } = await getComputeStats();
    if (data) {
      stats.totalConsume = data.totalConsume ?? 0;
      stats.totalRecharge = data.totalRecharge ?? 0;
    }
  } catch {
    // 静默失败，保持默认 0
  }
};

onMounted(() => {
  loadStats();
});
</script>

<style scoped lang="scss">
.compute-log-page {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);

  .card-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16px;
    font-size: 24px;
  }

  .card-content {
    flex: 1;
  }

  .card-value {
    font-size: 24px;
    font-weight: 600;
    line-height: 1.2;
  }

  .card-label {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }

  &.stat-consume .card-icon {
    background: rgba(245, 108, 108, 0.15);
    color: var(--el-color-danger);
  }

  &.stat-recharge .card-icon {
    background: rgba(103, 194, 58, 0.15);
    color: var(--el-color-success);
  }
}

.table-box {
  :deep(.card) {
    padding: 20px;
  }
}

.amount {
  font-weight: 500;

  &.consume {
    color: var(--el-color-danger);
  }

  &.recharge {
    color: var(--el-color-success);
  }
}

.detail-content {
  padding: 0 4px;
}

.detail-filters {
  margin-bottom: 16px;
}

.detail-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
