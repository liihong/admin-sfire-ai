<template>
  <view class="page-mine">
    <!-- 用户信息区 -->
    <view class="profile-hero" @tap="onProfileTap">
      <view class="profile-row">
        <view class="avatar-wrap">
          <image
            class="avatar-img"
            :src="avatarUrl"
            mode="aspectFill"
          />
          <view v-if="isVipMember" class="avatar-crown">👑</view>
        </view>
        <view class="profile-info">
          <text class="profile-name">{{ displayName }}</text>
          <view v-if="authStore.isLoggedIn && isVipMember" class="member-badge">
            <text class="member-badge-icon">💎</text>
            <text class="member-badge-text">{{ memberBadgeText }}</text>
          </view>
          <text v-else-if="authStore.isLoggedIn" class="profile-hint">开通会员解锁更多权益</text>
          <text v-else class="profile-hint">登录后查看专属数据</text>
        </view>
        <view v-if="authStore.isLoggedIn" class="profile-doc" @tap.stop="openPersonaModal">
          <SvgIcon name="works" :size="36" color="#9ca3af" />
          <view v-if="showPersonaDot" class="profile-doc-dot" />
        </view>
      </view>
    </view>

    <view class="page-content">
      <!-- 数据统计 -->
      <view class="stats-wrap">
        <view class="stats-card" :class="{ 'stats-card--locked': !authStore.isLoggedIn }">
          <view class="stats-head">
            <SvgIcon name="point" :size="28" color="#94a3b8" />
            <text class="stats-head-text">数据安全矩阵：</text>
          </view>
          <view class="stats-body">
            <view class="stat-col">
              <text class="stat-value">{{ companionDaysDisplay }}</text>
              <text class="stat-label">陪伴时间</text>
            </view>
            <view class="stat-divider" />
            <view class="stat-col tap" @tap.stop="goToPowerCenter">
              <text class="stat-value stat-value--orange">{{ powerDisplay }}</text>
              <text class="stat-label">剩余算力</text>
            </view>
          </view>
        </view>
        <view v-if="!authStore.isLoggedIn" class="stats-login-mask">
          <view class="stats-login-btn" @tap.stop="goToLogin">登录解锁数据</view>
        </view>
      </view>

      <!-- 未开通 VIP：会员权益介绍 -->
      <view v-if="!isVipMember" class="vip-annual-card" @tap="goToMembership">
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

      <!-- 操作菜单（独立卡片） -->
      <view
        v-for="item in menuList"
        :key="item.id"
        class="menu-card"
        @tap="handleMenuClick(item)"
      >
        <view class="menu-left">
          <view class="menu-icon-wrap">
            <SvgIcon :name="item.icon" :size="36" color="#F37021" />
            <view v-if="item.showDot" class="menu-icon-dot" />
          </view>
          <view class="menu-text-col">
            <text class="menu-name">{{ item.name }}</text>
            <text class="menu-desc">{{ item.desc }}</text>
          </view>
        </view>
        <text class="menu-chevron">›</text>
      </view>
    </view>

    <PersonaProfileModal
      v-model:visible="showPersonaModal"
      :default-name="userInfo.nickname"
      @saved="onPersonaSaved"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { getCoinStatistics, type CoinStatisticsData } from '@/api/coin'
import { getConversationList } from '@/api/conversation'
import { getInspirationList } from '@/api/inspiration'
import { useAuthStore } from '@/stores/auth'
import { DINGMA_DEFAULT_PROFILE_AVATAR_URL } from '@/constants/tenant'
import SvgIcon from '@/components/base/SvgIcon.vue'
import PersonaProfileModal from '@/components/mine/PersonaProfileModal.vue'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'

const authStore = useAuthStore()
const projectStore = useProjectStore()

const coinStats = ref<CoinStatisticsData | null>(null)
const conversationTotal = ref(0)
const inspirationTotal = ref(0)
const showPersonaModal = ref(false)
const personaIncomplete = ref(true)

const userInfo = computed(() => {
  const u = authStore.userInfo
  if (!u) {
    return {
      power: '0',
      level_code: 'normal',
      level_name: '普通用户'
    }
  }
  return {
    power: u.power || '0',
    level_code: u.level_code || 'normal',
    level_name: u.level_name || '普通用户',
    nickname: u.nickname || '用户'
  }
})

const isVipMember = computed(
  () => authStore.isLoggedIn && userInfo.value.level_code !== 'normal'
)

const avatarUrl = computed(() => {
  const u = authStore.userInfo
  const url = u?.avatarUrl || u?.avatar
  return url?.trim() ? url : DINGMA_DEFAULT_PROFILE_AVATAR_URL
})

const displayName = computed(() => {
  if (!authStore.isLoggedIn) return '点击登录'
  const nick = userInfo.value.nickname || '用户'
  if (isVipMember.value && userInfo.value.level_name) {
    return `${userInfo.value.level_name} · ${nick}`
  }
  return nick
})

const memberBadgeText = computed(() => userInfo.value.level_name || '钻石会员')

const showPersonaDot = computed(() => authStore.isLoggedIn && personaIncomplete.value)

const vipCardTitle = '顶妈脑爆年卡 · 开通尊享特权'
const vipCardDesc = '每天只需1元钱，全自动解锁爆单文案与创业导师帮你思考'
const vipCardCta = '立即去开通'

const lockedPlaceholder = '---'

const formatNumberInt = (num: string | number): string => {
  const numStr = String(num ?? '0').split('.')[0]
  return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const companionDaysDisplay = computed(() => {
  if (!authStore.isLoggedIn) return lockedPlaceholder
  const days = coinStats.value?.withDay
  return days !== undefined && days !== null ? String(days) : '0'
})

const powerDisplay = computed(() => {
  if (!authStore.isLoggedIn) return lockedPlaceholder
  const fromStats = coinStats.value?.availableBalance
  if (fromStats !== undefined && fromStats !== null) {
    return formatNumberInt(fromStats)
  }
  return formatNumberInt(userInfo.value.power || '0')
})

interface MenuItem {
  id: string
  name: string
  desc: string
  icon: string
  path: string
  requiresLogin: boolean
  showDot?: boolean
}

const allMenuList = computed<MenuItem[]>(() => [
  {
    id: 'history',
    name: '历史对话',
    desc: authStore.isLoggedIn
      ? `累计 ${conversationTotal.value} 条对话记录`
      : '登录后查看历史对话',
    icon: 'book',
    path: '/pages/mine/creation-records/index',
    requiresLogin: true,
    showDot: conversationTotal.value > 0
  },
  {
    id: 'inspiration',
    name: '我的灵感夹',
    desc: authStore.isLoggedIn
      ? `共收录 ${inspirationTotal.value} 条灵感`
      : '登录后管理灵感素材',
    icon: 'linggan',
    path: '/pages/inspiration/index',
    requiresLogin: true,
    showDot: inspirationTotal.value > 0
  },
  {
    id: 'referral',
    name: '我要推荐',
    desc: '邀请好友一起体验，获得算力奖励',
    icon: 'send',
    path: '/pages/mine/referral/index',
    requiresLogin: false,
    showDot: false
  }
])

const menuList = computed(() => allMenuList.value)

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

const refreshMenuCounts = async () => {
  if (!authStore.isLoggedIn) {
    conversationTotal.value = 0
    inspirationTotal.value = 0
    return
  }
  try {
    const [convRes, inspRes] = await Promise.all([
      getConversationList({ pageNum: 1, pageSize: 1 }),
      getInspirationList({ pageNum: 1, pageSize: 1, status: 'active' })
    ])
    if (convRes.code === 200 && convRes.data) {
      conversationTotal.value = convRes.data.total ?? 0
    }
    if (inspRes.code === 200 && inspRes.data) {
      inspirationTotal.value = inspRes.data.total ?? 0
    }
  } catch {
    conversationTotal.value = 0
    inspirationTotal.value = 0
  }
}

const checkPersonaComplete = () => {
  const ps = projectStore.activeProject?.persona_settings
  if (!ps) {
    personaIncomplete.value = true
    return
  }
  personaIncomplete.value = !(
    (ps.ip_name || projectStore.activeProject?.name || '').trim() &&
    ps.ip_city?.trim() &&
    ps.ip_identityTag?.trim() &&
    ps.ip_experience?.trim() &&
    ps.cl_mainProducts?.trim()
  )
}

const refreshPersonaStatus = async () => {
  if (!authStore.isLoggedIn) {
    personaIncomplete.value = true
    return
  }
  try {
    const res = await fetchProjects()
    projectStore.setProjectList(res.projects, res.active_project_id)
    checkPersonaComplete()
  } catch {
    checkPersonaComplete()
  }
}

const refreshAll = async () => {
  await refreshUserInfo()
  await Promise.all([refreshCoinStatistics(), refreshMenuCounts(), refreshPersonaStatus()])
}

const goToPowerCenter = () => {
  if (!authStore.isLoggedIn) {
    goToLogin()
    return
  }
  uni.navigateTo({ url: '/pages/mine/power/index' })
}

const goToMembership = () => {
  uni.navigateTo({ url: '/pages/mine/membership/index' })
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/index' })
}

const openPersonaModal = () => {
  if (!authStore.isLoggedIn) {
    goToLogin()
    return
  }
  showPersonaModal.value = true
}

const onPersonaSaved = () => {
  checkPersonaComplete()
}

const onProfileTap = () => {
  if (!authStore.isLoggedIn) {
    goToLogin()
  }
}

const handleMenuClick = (item: MenuItem) => {
  if (item.requiresLogin && !authStore.isLoggedIn) {
    goToLogin()
    return
  }
  if (item.path) {
    uni.navigateTo({ url: item.path })
  }
}

onMounted(() => refreshAll())

onShow(() => refreshAll())

onPullDownRefresh(async () => {
  await refreshAll()
  uni.stopPullDownRefresh()
})
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-mine {
  min-height: 100vh;
  background: #faf8f5;
  padding-bottom: calc(120rpx + env(safe-area-inset-bottom));
  padding-bottom: calc(120rpx + constant(safe-area-inset-bottom));
  box-sizing: border-box;
}

.profile-hero {
  padding: 24rpx 28rpx 32rpx;
  background: linear-gradient(180deg, #fff5eb 0%, #faf8f5 100%);
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.avatar-wrap {
  position: relative;
  width: 108rpx;
  height: 108rpx;
  border-radius: 50%;
  background: $white;
  box-shadow: 0 6rpx 20rpx rgba(243, 112, 33, 0.12);
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.avatar-crown {
  position: absolute;
  right: 4rpx;
  bottom: 4rpx;
  font-size: 28rpx;
  line-height: 1;
}

.profile-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.profile-name {
  font-size: 34rpx;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.3;
}

.profile-hint {
  font-size: 24rpx;
  color: #86909c;
}

.member-badge {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  align-self: flex-start;
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  background: rgba(59, 130, 246, 0.1);
}

.member-badge-icon {
  font-size: 22rpx;
}

.member-badge-text {
  font-size: 22rpx;
  font-weight: 600;
  color: #2563eb;
}

.profile-doc {
  position: relative;
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &:active {
    opacity: 0.75;
  }
}

.profile-doc-dot {
  position: absolute;
  top: 12rpx;
  right: 12rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #ef4444;
  border: 2rpx solid $white;
}

.page-content {
  padding: 0 28rpx;
}

.stats-wrap {
  position: relative;
  margin-bottom: 20rpx;
}

.stats-card {
  background: $white;
  border-radius: 24rpx;
  padding: 24rpx 28rpx 28rpx;
  box-shadow: 0 6rpx 24rpx rgba(15, 23, 42, 0.05);

  &--locked .stat-value,
  &--locked .stat-label {
    filter: blur(6rpx);
    opacity: 0.45;
  }
}

.stats-head {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 20rpx;
}

.stats-head-text {
  font-size: 24rpx;
  color: #94a3b8;
}

.stats-body {
  display: flex;
  align-items: stretch;
}

.stat-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10rpx;

  &.tap:active {
    opacity: 0.75;
  }
}

.stat-divider {
  width: 1rpx;
  background: #eef0f3;
  margin: 4rpx 0;
}

.stat-value {
  font-size: 44rpx;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.1;

  &--orange {
    color: $primary-orange;
  }
}

.stat-label {
  font-size: 24rpx;
  color: #94a3b8;
}

.stats-login-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.35);
}

.stats-login-btn {
  padding: 20rpx 48rpx;
  background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: $white;
  box-shadow: 0 8rpx 24rpx rgba($primary-orange, 0.3);

  &:active {
    opacity: 0.88;
  }
}

.vip-annual-card {
  padding: 32rpx 28rpx 28rpx;
  border-radius: 24rpx;
  margin-bottom: 20rpx;
  background: linear-gradient(145deg, #3d3228 0%, #2a221c 42%, #1a1a1a 100%);
  box-shadow: 0 12rpx 36rpx rgba(26, 20, 14, 0.22);

  &:active {
    opacity: 0.94;
  }
}

.vip-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.vip-title-row {
  flex: 1;
  min-width: 0;
  display: flex;
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
  font-size: 28rpx;
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
}

.menu-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  background: $white;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);

  &:active {
    opacity: 0.92;
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
  min-width: 0;
}

.menu-icon-wrap {
  position: relative;
  width: 80rpx;
  height: 80rpx;
  border-radius: 20rpx;
  background: #fff7e6;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-icon-dot {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #3b82f6;
  border: 2rpx solid $white;
}

.menu-text-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 700;
  color: #1d2129;
}

.menu-desc {
  font-size: 24rpx;
  color: #86909c;
  line-height: 1.4;
}

.menu-chevron {
  font-size: 40rpx;
  color: #c9cdd4;
  font-weight: 300;
  flex-shrink: 0;
  margin-left: 12rpx;
}
</style>
