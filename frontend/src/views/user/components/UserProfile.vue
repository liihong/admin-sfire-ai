<template>
  <div class="user-profile" v-loading="loading">
    <template v-if="userDetail">
      <!-- 基本信息 -->
      <div class="profile-section">
        <div class="section-header">
          <el-icon><User /></el-icon>
          <span>基本信息</span>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ userDetail.username }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ userDetail.phone }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ userDetail.email || "-" }}</el-descriptions-item>
          <el-descriptions-item label="用户等级">
            <el-tag :type="getLevelTagType(userDetail.level)" effect="dark">
              {{ getLevelLabel(userDetail.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="邀请码">{{ userDetail.inviteCode || "-" }}</el-descriptions-item>
          <el-descriptions-item label="邀请人">{{ userDetail.inviterName || "-" }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ userDetail.createTime }}</el-descriptions-item>
          <el-descriptions-item label="最后登录">{{ userDetail.lastLoginTime || "-" }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 算力概览 -->
      <div class="profile-section">
        <div class="section-header">
          <el-icon><Coin /></el-icon>
          <span>算力概览</span>
        </div>
        <div class="compute-cards">
          <div class="compute-card balance">
            <div class="card-value">{{ formatNumber(userDetail.computePower.balance) }}</div>
            <div class="card-label">可用算力</div>
          </div>
          <div class="compute-card frozen">
            <div class="card-value">{{ formatNumber(userDetail.computePower.frozen) }}</div>
            <div class="card-label">冻结算力</div>
          </div>
          <div class="compute-card consumed">
            <div class="card-value">{{ formatNumber(userDetail.computePower.totalConsumed) }}</div>
            <div class="card-label">累计消耗</div>
          </div>
          <div class="compute-card recharged">
            <div class="card-value">{{ formatNumber(userDetail.computePower.totalRecharged) }}</div>
            <div class="card-label">累计充值</div>
          </div>
        </div>
      </div>

      <!-- 邀请数据 -->
      <div class="profile-section">
        <div class="section-header">
          <el-icon><Share /></el-icon>
          <span>邀请数据</span>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="邀请人数">{{ userDetail.inviteCount }} 人</el-descriptions-item>
          <el-descriptions-item label="累计佣金">{{ formatNumber(userDetail.totalCommission) }}</el-descriptions-item>
          <el-descriptions-item label="可提现佣金">
            <span class="highlight-value">{{ formatNumber(userDetail.withdrawableCommission) }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 最近活动 -->
      <div class="profile-section">
        <div class="section-header">
          <el-icon><Clock /></el-icon>
          <span>最近活动</span>
        </div>
        <el-timeline>
          <el-timeline-item
            v-for="activity in userDetail.recentActivities"
            :key="activity.id"
            :timestamp="activity.createTime"
            placement="top"
            :type="getActivityType(activity.type)"
          >
            <div class="activity-content">
              <span>{{ activity.description }}</span>
              <span v-if="activity.amount" class="activity-amount" :class="activity.type">
                {{ activity.type === 'consume' || activity.type === 'withdraw' ? '-' : '+' }}{{ activity.amount }}
              </span>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-if="!userDetail.recentActivities?.length" description="暂无活动记录" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts" name="UserProfile">
import { ref, onMounted } from "vue";
import { User as UserIcon, Coin, Share, Clock } from "@element-plus/icons-vue";
import type { User } from "@/api/interface";
import { getUserDetail } from "@/api/modules/userManage";
import { USER_LEVEL_CONFIG } from "@/config";

const props = defineProps<{
  userId: string;
}>();

const loading = ref(false);
const userDetail = ref<User.ResUserDetail | null>(null);

// 等级标签类型
const getLevelTagType = (level: User.LevelType) => {
  const typeMap: Record<User.LevelType, string> = {
    0: "info",
    1: "warning",
    2: "danger"
  };
  return typeMap[level] || "info";
};

// 等级标签文本
const getLevelLabel = (level: User.LevelType) => {
  return USER_LEVEL_CONFIG[level]?.label || "未知";
};

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + "万";
  }
  return num.toLocaleString();
};

// 活动类型
const getActivityType = (type: string) => {
  const typeMap: Record<string, string> = {
    login: "primary",
    consume: "danger",
    recharge: "success",
    withdraw: "warning"
  };
  return typeMap[type] || "info";
};

// 获取用户详情
const fetchUserDetail = async () => {
  loading.value = true;
  try {
    const { data } = await getUserDetail(props.userId);
    userDetail.value = data;
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchUserDetail();
});
</script>

<style scoped lang="scss">
.user-profile {
  padding: 0 16px;

  .profile-section {
    margin-bottom: 24px;

    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);

      .el-icon {
        color: var(--el-color-primary);
      }
    }
  }

  .compute-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;

    .compute-card {
      padding: 16px;
      border-radius: 8px;
      text-align: center;

      .card-value {
        font-size: 24px;
        font-weight: 700;
        font-family: "DIN", sans-serif;
        margin-bottom: 4px;
      }

      .card-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      &.balance {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;

        .card-label {
          color: rgba(255, 255, 255, 0.8);
        }
      }

      &.frozen {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);

        .card-value {
          color: #e6a23c;
        }
      }

      &.consumed {
        background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);

        .card-value {
          color: #f56c6c;
        }
      }

      &.recharged {
        background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);

        .card-value {
          color: #67c23a;
        }
      }
    }
  }

  .highlight-value {
    color: var(--el-color-primary);
    font-weight: 600;
  }

  .activity-content {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .activity-amount {
      font-family: "DIN", sans-serif;
      font-weight: 600;

      &.consume,
      &.withdraw {
        color: #f56c6c;
      }

      &.recharge {
        color: #67c23a;
      }
    }
  }
}
</style>



