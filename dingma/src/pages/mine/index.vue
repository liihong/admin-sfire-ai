<template>
  <view class="page-mine">
    <view class="page-content">
      <!-- 顶妈脑爆年卡 -->
      <view class="vip-annual-card" @tap="goToMembership">
        <view class="vip-card-top">
          <view class="vip-title-row">
            <view class="vip-crown-box">
              <text class="vip-crown">👑</text>
            </view>
            <text class="vip-title">{{ vipCardTitle }}</text>
          </view>
          <view class="vip-pass-badge">
            <text class="vip-pass-text">VIP PASS</text>
          </view>
        </view>
        <text class="vip-desc">{{ vipCardDesc }}</text>
        <text class="vip-cta">{{ vipCardCta }} ›</text>
      </view>

      <!-- 三列数据（未登录模糊 + 登录解锁） -->
      <view class="stats-wrap">
        <view class="stats-card" :class="{ 'stats-card--locked': !authStore.isLoggedIn }">
          <view class="stat-col" @tap.stop="noop">
            <text class="stat-value">{{ aiCallDisplay }}</text>
            <text class="stat-label">调用 AI（次）</text>
          </view>
          <view class="stat-divider" />
          <view class="stat-col tap" @tap="goToPowerCenter">
            <text class="stat-value">{{ powerDisplay }}</text>
            <text class="stat-label">剩余算力</text>
          </view>
          <view class="stat-divider" />
          <view class="stat-col tap" @tap="goToReferral">
            <text class="stat-value stat-value-blue">{{ shareEarningDisplay }}</text>
            <text class="stat-label">分享收益</text>
          </view>
        </view>
        <view v-if="!authStore.isLoggedIn" class="stats-login-mask">
          <view class="stats-login-btn" @tap.stop="goToLogin">登录解锁数据</view>
        </view>
      </view>

      <!-- 菜单：单卡片分组 -->
      <view class="menu-group-card">
        <view
          v-for="(item, index) in menuList"
          :key="item.id"
          class="menu-row"
          :class="{ 'menu-row--last': index === menuList.length - 1 }"
          @tap="handleMenuClick(item)"
        >
          <view class="menu-left">
            <view class="menu-icon-wrap" :style="{ background: item.iconBg }">
              <SvgIcon :name="item.icon" size="30" color="#FFFFFF" />
            </view>
            <view class="menu-text-col">
              <text class="menu-name">{{ item.name }}</text>
              <text class="menu-desc" v-if="item.desc">{{ item.desc }}</text>
            </view>
          </view>
          <text class="menu-chevron">›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { getCoinStatistics, type CoinStatisticsData } from '@/api/coin'
import { useAuthStore } from '@/stores/auth'
import SvgIcon from '@/components/base/SvgIcon.vue'

const authStore = useAuthStore()

const coinStats = ref<CoinStatisticsData | null>(null)

const noop = () => {}

const userInfo = computed(() => {
  const storeUserInfo = authStore.userInfo
  if (!storeUserInfo) {
    return {
      power: '0',
      partner_balance: '0.00',
      partnerBalance: '0.00',
      level_code: 'normal',
      level_name: '普通用户'
    }
  }

  return {
    power: storeUserInfo.power || '0',
    balance: storeUserInfo.partnerBalance || storeUserInfo.partner_balance || '0.00',
    partnerBalance: storeUserInfo.partnerBalance || storeUserInfo.partner_balance || '0.00',
    partner_balance: storeUserInfo.partner_balance || storeUserInfo.partnerBalance || '0.00',
    level_code: storeUserInfo.level_code || 'normal',
    level_name: storeUserInfo.level_name || '普通用户'
  }
})

const isVipMember = computed(
  () => authStore.isLoggedIn && userInfo.value.level_code !== 'normal'
)

const vipCardTitle = computed(() =>
  isVipMember.value ? '顶妈脑爆年卡 · 尊享特权生效中' : '顶妈脑爆年卡 · 开通尊享特权'
)

const vipCardDesc = computed(() =>
  isVipMember.value
    ? `当前身份：${userInfo.value.level_name || 'VIP 学员'}，畅享爆单文案与创业导师`
    : '每天只需1元钱，全自动解锁爆单文案与创业导师帮你思考'
)

const vipCardCta = computed(() => (isVipMember.value ? '查看会员权益' : '立即去开通'))

const formatNumberInt = (num: string | number): string => {
  const numStr = String(num ?? '0').split('.')[0]
  return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const formatMoneyYuan = (s: string | number): string => {
  const n = typeof s === 'number' ? s : parseFloat(String(s || '0'))
  if (Number.isNaN(n)) return '¥ 0.00'
  const fixed = (Math.round(n * 100) / 100).toFixed(2)
  const [intPart, decPart] = fixed.split('.')
  const withSep = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return `¥ ${decPart !== undefined ? `${withSep}.${decPart}` : withSep}`
}

const lockedPlaceholder = '---'

const aiCallDisplay = computed(() => {
  if (!authStore.isLoggedIn) return lockedPlaceholder
  const v = coinStats.value?.totalContent
  return v !== undefined && v !== null ? formatNumberInt(v) : '0'
})

const powerDisplay = computed(() => {
  if (!authStore.isLoggedIn) return lockedPlaceholder
  return formatNumberInt(userInfo.value.power || '0')
})

const shareEarningDisplay = computed(() => {
  if (!authStore.isLoggedIn) return lockedPlaceholder
  return formatMoneyYuan(userInfo.value.partner_balance || userInfo.value.partnerBalance || '0')
})

const allMenuList = [
  {
    id: 'creation-records',
    name: '我的创作记录',
    desc: '查看您的历史创作记录',
    icon: 'works',
    iconBg: '#7C3AED',
    path: '/pages/mine/creation-records/index',
    requiresLogin: true
  },
  {
    id: 'referral',
    name: '我要推荐',
    desc: '邀请好友一起体验，获得算力奖励',
    icon: 'send',
    iconBg: '#3B82F6',
    path: '/pages/mine/referral/index',
    requiresLogin: false
  },
  {
    id: 'contact',
    name: '联系客服',
    desc: '升级会员或寻求使用帮助',
    icon: 'service',
    iconBg: '#10B981',
    path: '/pages/mine/contact/index',
    requiresLogin: false
  }
]

const menuList = computed(() => allMenuList.filter(item => !item.requiresLogin || authStore.isLoggedIn))

const refreshUserInfo = async () => {
  try {
    await authStore.refreshUserInfo()
  } catch {
    //
  }
}

const refreshCoinStatistics = async () => {
  if (!authStore.isLoggedIn) {
    coinStats.value = null
    return
  }
  try {
    const res = await getCoinStatistics()
    if (res.code === 200 && res.data) {
      coinStats.value = res.data
    }
  } catch {
    coinStats.value = null
  }
}

const goToPowerCenter = () => {
  if (!authStore.isLoggedIn) {
    goToLogin()
    return
  }
  uni.navigateTo({ url: '/pages/mine/power/index' })
}

const goToReferral = () => {
  if (!authStore.isLoggedIn) {
    goToLogin()
    return
  }
  uni.navigateTo({ url: '/pages/mine/referral/index' })
}

const goToMembership = () => {
  uni.navigateTo({ url: '/pages/mine/membership/index' })
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/index' })
}

const handleMenuClick = (item: (typeof allMenuList)[number]) => {
  if (item.path) {
    uni.navigateTo({ url: item.path })
  }
}

onMounted(async () => {
  if (!authStore.userInfo) await refreshUserInfo()
  await refreshCoinStatistics()
})

onShow(async () => {
  await refreshUserInfo()
  await refreshCoinStatistics()
})

onPullDownRefresh(async () => {
  await refreshUserInfo()
  await refreshCoinStatistics()
  uni.stopPullDownRefresh()
})
</script>

<style scoped lang="scss">
.page-mine {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

.page-content {
  padding: 24rpx 28rpx 0;
}

/* ---------- 顶妈脑爆年卡 ---------- */
.vip-annual-card {
  position: relative;
  padding: 32rpx 28rpx 28rpx;
  border-radius: 28rpx;
  margin-bottom: 24rpx;
  background: linear-gradient(145deg, #3d3228 0%, #2a221c 42%, #1a1a1a 100%);
  box-shadow: 0 12rpx 36rpx rgba(26, 20, 14, 0.28);
  overflow: hidden;

  &:active {
    opacity: 0.94;
  }
}

.vip-card-top {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.vip-title-row {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14rpx;
}

.vip-crown-box {
  width: 52rpx;
  height: 52rpx;
  border-radius: 14rpx;
  background: linear-gradient(135deg, #fcd34d 0%, #f59e0b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.vip-crown {
  font-size: 28rpx;
  line-height: 1;
}

.vip-title {
  flex: 1;
  font-size: 30rpx;
  font-weight: 700;
  color: #fef3c7;
  line-height: 1.35;
}

.vip-pass-badge {
  flex-shrink: 0;
  padding: 6rpx 16rpx;
  border: 1rpx solid rgba(251, 191, 36, 0.65);
  border-radius: 999rpx;
  background: rgba(251, 191, 36, 0.12);
}

.vip-pass-text {
  font-size: 20rpx;
  font-weight: 700;
  color: #fbbf24;
  letter-spacing: 1rpx;
}

.vip-desc {
  display: block;
  font-size: 24rpx;
  color: rgba(254, 243, 199, 0.72);
  line-height: 1.5;
  margin-bottom: 24rpx;
}

.vip-cta {
  font-size: 30rpx;
  font-weight: 700;
  color: #fbbf24;
  line-height: 1.2;
}

/* ---------- 数据统计 ---------- */
.stats-wrap {
  position: relative;
  margin-bottom: 24rpx;
}

.stats-card {
  background: #fff;
  border-radius: 28rpx;
  padding: 40rpx 16rpx 36rpx;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  justify-content: space-between;
  box-shadow: 0 6rpx 24rpx rgba(15, 23, 42, 0.05);

  &--locked .stat-value,
  &--locked .stat-label {
    filter: blur(6rpx);
    opacity: 0.45;
  }

  &--locked .stat-value-blue {
    color: #94a3b8;
  }
}

.stat-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  min-width: 0;

  &.tap:active {
    opacity: 0.75;
  }
}

.stat-divider {
  width: 1rpx;
  background: #eef0f3;
  margin: 8rpx 0;
  align-self: stretch;
}

.stat-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.15;
}

.stat-value-blue {
  color: #2563eb;
}

.stat-label {
  font-size: 22rpx;
  color: #94a3b8;
  text-align: center;
}

.stats-login-mask {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.35);
}

.stats-login-btn {
  padding: 22rpx 56rpx;
  background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
  border-radius: 999rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
  box-shadow: 0 8rpx 24rpx rgba(15, 39, 68, 0.28);

  &:active {
    opacity: 0.88;
  }
}

/* ---------- 菜单分组卡片 ---------- */
.menu-group-card {
  background: #fff;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 6rpx 24rpx rgba(15, 23, 42, 0.05);
}

.menu-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  border-bottom: 1rpx solid #f0f2f5;

  &:active {
    background: #fafbfc;
  }

  &--last {
    border-bottom: none;
  }
}

.menu-left {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 22rpx;
  flex: 1;
  min-width: 0;
}

.menu-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-text-col {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
  min-width: 0;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #1d2129;
}

.menu-desc {
  font-size: 24rpx;
  color: #86909c;
  line-height: 1.35;
}

.menu-chevron {
  font-size: 36rpx;
  color: #c9cdd4;
  font-weight: 300;
  flex-shrink: 0;
  margin-left: 12rpx;
}
</style>
