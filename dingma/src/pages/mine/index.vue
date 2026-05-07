<template>
  <view class="page-mine">
    <!-- 顶部渐变 + 个人信息 -->
    <view class="module-header">
      <view class="header-gradient" />
      <view class="header-inner">
        <view class="profile-row">
          <view class="avatar-side">
            <!-- #ifdef MP-WEIXIN -->
            <button
              v-if="authStore.isLoggedIn"
              class="avatar-btn"
              open-type="chooseAvatar"
              @chooseavatar="handleChooseAvatar"
            >
              <image
                class="avatar-img"
:src="userInfo.avatar || defaultProfileAvatarUrl"
                mode="aspectFill"
              />
            </button>
            <view v-else class="avatar-btn avatar-btn-static" @tap="goToLogin">
              <image class="avatar-img" :src="defaultProfileAvatarUrl" mode="aspectFill" />
            </view>
            <!-- #endif -->
            <!-- #ifndef MP-WEIXIN -->
            <view class="avatar-btn avatar-btn-static">
              <image class="avatar-img" :src="userInfo.avatar || defaultProfileAvatarUrl" mode="aspectFill" />
            </view>
            <!-- #endif -->
          </view>

          <view class="profile-text">
            <view v-if="!authStore.isLoggedIn" class="login-line">
              <text class="nickname" @tap="goToLogin">点击登录</text>
              <text class="sub-muted">登录后查看学员信息与算力</text>
            </view>
            <template v-else>
              <text class="nickname">{{ displayName }}</text>
              <view class="badge-row">
                <view class="vip-pill" v-if="showVipBadge">
                  <text class="vip-pill-icon">★</text>
                  <text class="vip-pill-text">{{ vipBadgeText }}</text>
                </view>
                <text class="user-id" v-if="displayUserId">ID: {{ displayUserId }}</text>
              </view>
            </template>
          </view>
        </view>

        <!-- 三列数据 -->
        <view class="stats-card">
          <view class="stat-col" @tap.stop="noop">
            <text class="stat-value stat-value-dark">{{ aiCallDisplay }}</text>
            <text class="stat-label">调用 AI（次）</text>
          </view>
          <view class="stat-divider" />
          <view class="stat-col tap" @tap="goToPowerCenter">
            <text class="stat-value stat-value-dark">{{ powerDisplay }}</text>
            <text class="stat-label">剩余算力</text>
          </view>
          <view class="stat-divider" />
          <view class="stat-col tap" @tap="goToReferral">
            <text class="stat-value stat-value-blue">{{ shareEarningDisplay }}</text>
            <text class="stat-label">分享收益</text>
          </view>
        </view>
      </view>
    </view>

    <view class="module-body">
      <!-- 合伙人计划 -->
      <!-- <view v-if="authStore.isLoggedIn" class="module-partner-banner" @tap="goToReferral">
        <view class="partner-icon-wrap">
          <text class="partner-emoji">🏆</text>
        </view>
        <view class="partner-copy">
          <text class="partner-title">合伙人计划</text>
          <text class="partner-sub">推荐学员享 20% 实时返佣</text>
        </view>
        <view class="partner-cta">
          <text class="partner-cta-text">去赚钱</text>
        </view>
      </view> -->

      <!-- 开通会员 -->
      <view v-if="authStore.isLoggedIn && userInfo.level_code === 'normal'" class="module-upgrade-banner" @tap="goToMembership">
        <view class="partner-icon-wrap upgrade-icon-wrap">
          <SvgIcon name="suanli" size="36" color="#FBBF24" />
        </view>
        <view class="partner-copy">
          <text class="partner-title upgrade-title-white">开通会员</text>
          <text class="partner-sub upgrade-sub-grey">解锁更多 AI 能力与算力优待</text>
        </view>
        <view class="partner-cta upgrade-cta-orange">
          <text class="partner-cta-text upgrade-cta-text-dark">立即开通</text>
        </view>
      </view>

      <!-- 菜单：每项独立白卡片，仅样式调整，功能不变 -->
      <view class="module-menus">
        <view
          v-for="(item, index) in menuList"
          :key="index"
          class="menu-card"
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
import { updateUserInfo, uploadAvatar } from '@/api/user'
import { getCoinStatistics, type CoinStatisticsData } from '@/api/coin'
import { useAuthStore } from '@/stores/auth'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { DINGMA_DEFAULT_PROFILE_AVATAR_URL } from '@/constants/tenant'

const authStore = useAuthStore()

const coinStats = ref<CoinStatisticsData | null>(null)

const defaultProfileAvatarUrl = DINGMA_DEFAULT_PROFILE_AVATAR_URL

const noop = () => {}

const userInfo = computed(() => {
  const storeUserInfo = authStore.userInfo
  if (!storeUserInfo) {
    return {
      avatar: '',
      avatarUrl: '',
      phone: '',
      nickname: '',
      expireDate: '',
      vip_expire_date: '',
      power: '0',
      balance: '0.00',
      partnerBalance: '0.00',
      partner_balance: '0.00',
      partnerStatus: '普通用户',
      partner_status: '普通用户',
      level_code: 'normal',
      level_name: '普通用户',
      user_id: undefined as number | undefined
    }
  }

  return {
    avatar: storeUserInfo.avatar || storeUserInfo.avatarUrl || '',
    avatarUrl: storeUserInfo.avatarUrl || storeUserInfo.avatar || '',
    phone: storeUserInfo.phone || '',
    nickname: storeUserInfo.nickname || '',
    expireDate: storeUserInfo.expireDate || storeUserInfo.vip_expire_date || '',
    vip_expire_date: storeUserInfo.vip_expire_date || storeUserInfo.expireDate || '',
    power: storeUserInfo.power || '0',
    balance: storeUserInfo.partnerBalance || storeUserInfo.partner_balance || '0.00',
    partnerBalance: storeUserInfo.partnerBalance || storeUserInfo.partner_balance || '0.00',
    partner_balance: storeUserInfo.partner_balance || storeUserInfo.partnerBalance || '0.00',
    partnerStatus: storeUserInfo.partnerStatus || storeUserInfo.partner_status || '普通用户',
    partner_status: storeUserInfo.partner_status || storeUserInfo.partnerStatus || '普通用户',
    level_code: storeUserInfo.level_code || 'normal',
    level_name: storeUserInfo.level_name || '普通用户',
    user_id: storeUserInfo.user_id
  }
})

const displayName = computed(() => {
  const n = userInfo.value.nickname?.trim()
  if (n) return n
  return '顶妈学员'
})

const displayUserId = computed(() => {
  const id = userInfo.value.user_id
  return id !== undefined && id !== null ? String(id) : ''
})

const showVipBadge = computed(() => authStore.isLoggedIn && userInfo.value.level_code !== 'normal')

const vipBadgeText = computed(() => {
  const name = userInfo.value.level_name?.trim()
  if (name && name !== '普通用户') return name
  return 'VIP 学员'
})

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

const aiCallDisplay = computed(() => {
  if (!authStore.isLoggedIn) return '—'
  const v = coinStats.value?.totalContent
  return v !== undefined && v !== null ? formatNumberInt(v) : '—'
})

const powerDisplay = computed(() => {
  if (!authStore.isLoggedIn) return '—'
  return formatNumberInt(userInfo.value.power || '0')
})

const shareEarningDisplay = computed(() => {
  if (!authStore.isLoggedIn) return '—'
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
    desc: '升级会员或寻求帮助',
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

const handleChooseAvatar = async (e: any) => {
  const avatarUrl = e.detail.avatarUrl
  if (!avatarUrl) {
    uni.showToast({ title: '获取头像失败', icon: 'none' })
    return
  }

  try {
    const uploadResponse = await uploadAvatar(avatarUrl)

    if (uploadResponse.code === 200 && uploadResponse.data?.url) {
      const updateResponse = await updateUserInfo({
        avatar: uploadResponse.data.url
      })

      if (updateResponse.code === 200) {
        uni.showToast({ title: '头像更新成功', icon: 'success' })
        await refreshUserInfo()
      } else {
        uni.showToast({ title: (updateResponse as any).msg || '更新失败', icon: 'none' })
      }
    } else {
      uni.showToast({ title: uploadResponse.msg || '上传失败', icon: 'none' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '上传失败，请重试', icon: 'none' })
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
  background: #f1f5f9;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

/* ---------- 顶部：渐变 + 资料 + 三列 ---------- */
.module-header {
  position: relative;
  padding-bottom: 8rpx;
}

.header-gradient {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 320rpx;
  background: linear-gradient(180deg, #dfefff 0%, #f1f5f9 100%);
  pointer-events: none;
}

.header-inner {
  position: relative;
  z-index: 1;
  padding: 48rpx 32rpx 0;
}

.profile-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 28rpx;
  margin-bottom: 36rpx;
}

.avatar-side {
  flex-shrink: 0;
}

.avatar-btn {
  width: 132rpx;
  height: 132rpx;
  padding: 0;
  margin: 0;
  border-radius: 50%;
  overflow: hidden;
  border: 4rpx solid #fff;
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.12);
  background: #e2e8f0;
  line-height: 1;
}

.avatar-btn::after {
  border: none;
}

.avatar-btn-static {
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.profile-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.login-line {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.nickname {
  font-size: 40rpx;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
}

.sub-muted {
  font-size: 26rpx;
  color: #94a3b8;
}

.badge-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx 20rpx;
}

.vip-pill {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 6rpx;
  padding: 6rpx 18rpx;
  background: #3b82f6;
  border-radius: 999rpx;
}

.vip-pill-icon {
  font-size: 22rpx;
  color: #fff;
  line-height: 1;
}

.vip-pill-text {
  font-size: 22rpx;
  color: #fff;
  font-weight: 600;
  line-height: 1;
}

.user-id {
  font-size: 24rpx;
  color: #94a3b8;
}

.stats-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 36rpx 16rpx;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  justify-content: space-between;
  box-shadow: 0 8rpx 32rpx rgba(15, 23, 42, 0.06);
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
  background: #e9ecf0;
  margin: 8rpx 0;
  align-self: stretch;
}

.stat-value {
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.15;
}

.stat-value-dark {
  color: #0f172a;
}

.stat-value-blue {
  color: #2563eb;
}

.stat-label {
  font-size: 22rpx;
  color: #94a3b8;
  text-align: center;
}

/* ---------- 下方模块 ---------- */
.module-body {
  padding: 28rpx 24rpx 0;
}

.module-partner-banner,
.module-upgrade-banner {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx 28rpx;
  border-radius: 24rpx;
  margin-bottom: 28rpx;
  box-shadow: 0 8rpx 28rpx rgba(15, 23, 42, 0.12);

  &:active {
    opacity: 0.92;
  }
}

.module-partner-banner {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 92%);
}

.module-upgrade-banner {
  background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 95%);
}

.partner-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upgrade-icon-wrap {
  background: rgba(251, 191, 36, 0.15);
}

.partner-emoji {
  font-size: 38rpx;
  line-height: 1;
}

.partner-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.partner-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.upgrade-title-white {
  color: #fff;
}

.partner-sub {
  font-size: 24rpx;
  color: #94a3b8;
  line-height: 1.35;
}

.upgrade-sub-grey {
  color: #cbd5e1;
}

.partner-cta {
  flex-shrink: 0;
  padding: 16rpx 28rpx;
  background: #ffd60a;
  border-radius: 999rpx;
}

.upgrade-cta-orange {
  background: #f37021;
}

.partner-cta-text {
  font-size: 26rpx;
  font-weight: 700;
  color: #0f172a;
}

.upgrade-cta-text-dark {
  color: #fff;
}

/* ---------- 菜单独立卡片 ---------- */
.module-menus {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  padding-bottom: 24rpx;
}

.menu-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx 32rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4rpx 20rpx rgba(15, 23, 42, 0.05);

  &:active {
    opacity: 0.9;
    background: #fafbfc;
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
  font-weight: 500;
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
