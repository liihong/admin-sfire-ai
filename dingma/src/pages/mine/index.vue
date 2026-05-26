<template>
  <view class="page-mine">
    <!-- 已登录：第一排 头像 + 昵称 + 剩余算力（非 VIP）；ip信息 固定在行末 -->
    <view v-if="authStore.isLoggedIn" class="mine-user-strip-wrap">
      <view class="mine-user-strip">
        <view class="mine-user-strip__left" @tap="onUserStripCoreTap">
          <view class="mine-user-strip__avatar-wrap">
            <image class="mine-user-strip__avatar" :src="avatarUrl" mode="aspectFill" />
            <view v-if="isVipMember" class="mine-user-strip__crown">👑</view>
          </view>
          <view class="mine-user-strip__texts">
            <!-- VIP：昵称在上，等级胶囊在下（钻石档左侧 💎） -->
            <template v-if="isVipMember">
              <text class="mine-user-strip__name">{{ displayNickname }}</text>
              <view
                class="mine-user-strip__vip-badge"
                :class="{ 'mine-user-strip__vip-badge--diamond': vipBadgeShowDiamondIcon }"
                :style="{ backgroundColor: memberLevelBadgeStyle.backgroundColor }"
              >
                <text v-if="vipBadgeShowDiamondIcon" class="mine-user-strip__vip-badge-emoji">💎</text>
                <text
                  class="mine-user-strip__vip-badge-text"
                  :style="{ color: memberLevelBadgeStyle.color }"
                >
                  {{ memberBadgeText }}
                </text>
              </view>
            </template>
            <template v-else>
              <text class="mine-user-strip__name">{{ displayNickname }}</text>
              <text class="mine-user-strip__hint">开通会员解锁更多权益</text>
            </template>
          </view>
        </view>
        <!-- 非会员：顶部仅展示剩余算力；会员算力在下方尊享卡 -->
        <view
          v-if="!isVipMember"
          class="mine-user-strip__stats mine-user-strip__stats--solo-power"
        >
          <view class="mine-user-strip__stat mine-user-strip__stat--tap" @tap.stop="goToPowerCenter">
            <text class="mine-user-strip__stat-num mine-user-strip__stat-num--accent">{{ powerDisplay }}</text>
            <text class="mine-user-strip__stat-lab">剩余算力(tokens)</text>
          </view>
        </view>
        <view class="mine-user-strip__doc" @tap.stop="goToIpInfoPage">
          <view class="mine-user-strip__doc-inner">
            <SvgIcon name="works" :size="34" color="#D94B36" />
            <text class="mine-user-strip__doc-label">ip信息</text>
          </view>
          <view v-if="showPersonaDot" class="mine-user-strip__doc-dot" />
        </view>
      </view>
    </view>

    <view
      class="page-content"
      :class="{
        'page-content--guest': !authStore.isLoggedIn,
        'page-content--logged': authStore.isLoggedIn
      }"
    >
      <!-- 未登录：仅统计卡 + 登录遮罩 -->
      <view v-if="!authStore.isLoggedIn" class="stats-wrap">
        <view class="stats-card stats-card--locked">
          <view class="stats-body stats-body--single">
            <view class="stat-col tap" @tap.stop="goToPowerCenter">
              <text class="stat-value stat-value--accent">{{ powerDisplay }}</text>
              <text class="stat-label">剩余算力(tokens)</text>
            </view>
          </view>
        </view>
        <view class="stats-login-mask">
          <view class="stats-login-btn" @tap.stop="goToLogin">登录解锁数据</view>
        </view>
      </view>

      <!-- 第二排 · 已购会员：按等级换肤的尊享卡（仅展示权益氛围，不含头像与数据） -->
      <view v-if="authStore.isLoggedIn && isVipMember" class="member-tier-shell">
        <view
          class="member-tier-card"
          :class="memberTierSkinClass"
        >
          <view class="member-tier-card__gloss" aria-hidden="true" />
          <view class="member-tier-card__top">
            <view class="member-tier-card__title-row">
              <view class="vip-crown-box">
                <text class="vip-crown">👑</text>
              </view>
              <text class="member-tier-card__title">{{ memberTierTitle }}</text>
            </view>
            <view class="vip-pass-badge">
              <text class="vip-pass-text">VIP PASS</text>
            </view>
          </view>
          <text class="member-tier-card__desc">{{ memberTierDesc }}</text>
          <view class="member-tier-card__footer">
            <view class="member-tier-card__power" @tap.stop="goToPowerCenter">
              <text class="member-tier-card__power-num">{{ powerDisplay }}</text>
              <text class="member-tier-card__power-lab">剩余算力(tokens)</text>
            </view>
            <text class="member-tier-card__cta" @tap.stop="goToMembership">查看会员权益 ›</text>
          </view>
        </view>
      </view>

      <!-- 第二排 · 未开通：深色调推广卡（与稿图一致） -->
      <view v-if="authStore.isLoggedIn && !isVipMember" class="vip-annual-card" @tap="goToMembership">
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
        :class="{ 'menu-card--spotlight': item.id === 'referral' }"
        @tap="handleMenuClick(item)"
      >
        <view class="menu-left">
          <view class="menu-icon-wrap">
            <SvgIcon :name="item.icon" :size="42" :color="item.iconColor ?? '#D94B36'" />
          </view>
          <view class="menu-text-col">
            <text class="menu-name">{{ item.name }}</text>
            <text class="menu-desc">{{ item.desc }}</text>
          </view>
        </view>
        <text class="menu-chevron">›</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { getCoinStatistics, type CoinStatisticsData } from '@/api/coin'
import { useAuthStore } from '@/stores/auth'
import { DINGMA_DEFAULT_PROFILE_AVATAR_URL } from '@/constants/tenant'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'

const authStore = useAuthStore()
const projectStore = useProjectStore()

const coinStats = ref<CoinStatisticsData | null>(null)
const personaIncomplete = ref(true)

const userInfo = computed(() => {
  const u = authStore.userInfo
  if (!u) {
    return {
      power: '0',
      level_code: 'normal',
      level_name: '普通用户',
      nickname: ''
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

const memberBadgeText = computed(() => userInfo.value.level_name || '尊贵会员')

function isDiamondMemberTier(): boolean {
  const code = String(userInfo.value.level_code || 'normal').toLowerCase().trim()
  const nameLower = String(userInfo.value.level_name || '').toLowerCase()
  return code.includes('diamond') || nameLower.includes('钻')
}

/** 会员等级胶囊：圆角背景色由用户 openid+等级 稳定映射，不同用户像「随机」配色 */
interface MemberLevelBadgeTint {
  backgroundColor: string
  color: string
}

/** 钻石档：饱和度更高的暖琥珀底，避免与白底糊成一块 */
const DIAMOND_MEMBER_BADGE_TINT: MemberLevelBadgeTint = {
  backgroundColor: '#EFD563',
  color: '#582F0E'
}

const MEMBER_LEVEL_BADGE_PALETTE: ReadonlyArray<Pick<MemberLevelBadgeTint, 'backgroundColor' | 'color'>> = [
  { backgroundColor: '#E3F2FD', color: '#1565C0' },
  { backgroundColor: '#FCE4EC', color: '#AD1457' },
  { backgroundColor: '#E8F5E9', color: '#2E7D32' },
  { backgroundColor: '#FFF3E0', color: '#E65100' },
  { backgroundColor: '#F3E5F5', color: '#6A1B9A' },
  { backgroundColor: '#E0F7FA', color: '#00695C' },
  { backgroundColor: '#FFF8E1', color: '#F57F17' },
  { backgroundColor: '#E8EAF6', color: '#3949AB' },
  { backgroundColor: '#FFEBEE', color: '#C62828' },
  { backgroundColor: '#E1F5FE', color: '#0277BD' }
]

function hashStringToNonNegativeInt(input: string): number {
  let h = 0
  for (let i = 0; i < input.length; i += 1) {
    h = Math.imul(31, h) + input.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

const memberLevelBadgeStyle = computed((): MemberLevelBadgeTint => {
  if (isDiamondMemberTier()) {
    return DIAMOND_MEMBER_BADGE_TINT
  }
  const u = authStore.userInfo
  const seed = `${u?.openid ?? ''}|${userInfo.value.level_code}|${memberBadgeText.value}`
  const idx = hashStringToNonNegativeInt(seed) % MEMBER_LEVEL_BADGE_PALETTE.length
  const pick = MEMBER_LEVEL_BADGE_PALETTE[idx]!
  return {
    backgroundColor: pick.backgroundColor,
    color: pick.color
  }
})

/** 钻石 etc.：胶囊左侧展示 💎；其它等级仅用文案 */
const vipBadgeShowDiamondIcon = computed(() => isDiamondMemberTier())

/** 第一排仅展示微信昵称 */
const displayNickname = computed(() => {
  if (!authStore.isLoggedIn) return ''
  return userInfo.value.nickname || '用户'
})

/** 已开通：第二排尊享卡主标题（等级已在顶部胶囊展示，此处不再重复「· 钻石会员」等后缀） */
const memberTierTitle = computed(() => '顶妈脑爆年卡')

/** 已开通：第二排尊享卡中段文案（与底部「查看会员权益」错位：情绪价值 + 使用提示，不单列权益） */
const memberTierDesc = computed(() => '顶妈陪着你，把好生意想明白、说清楚。')

/**
 * 第二排会员卡皮肤：对齐服务端 UserLevel（vip / svip / 钻石 / max）
 */
const memberTierSkinClass = computed(() => {
  const code = String(userInfo.value.level_code || 'normal').toLowerCase().trim()
  const nameLower = String(userInfo.value.level_name || '').toLowerCase()

  if (code === 'max') return 'member-tier-card--skin-max'
  if (code === 'svip') return 'member-tier-card--skin-svip'
  if (code.includes('diamond') || nameLower.includes('钻')) {
    return 'member-tier-card--skin-diamond'
  }
  if (code === 'vip') return 'member-tier-card--skin-vip'
  return 'member-tier-card--skin-vip'
})

const showPersonaDot = computed(() => authStore.isLoggedIn && personaIncomplete.value)

const vipCardTitle = '顶妈脑爆年卡 · 开通尊享特权'
const vipCardDesc = '每天只需1元钱，全自动解锁爆单文案与创业导师帮你思考'
const vipCardCta = '立即去开通'

const lockedPlaceholder = '---'

const formatNumberInt = (num: string | number): string => {
  const numStr = String(num ?? '0').split('.')[0]
  return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

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
  /** 单色 iconfont 时生效；彩色字体会变体为 linggan2 / send2 */
  iconColor?: string
  path: string
  requiresLogin: boolean
}

const allMenuList = computed<MenuItem[]>(() => [
  {
    id: 'inspiration',
    name: '我的灵感夹',
    desc: authStore.isLoggedIn
      ? `收录您随时随手捕捉的好点子脑洞`
      : '收录您随时随手捕捉的好点子脑洞（登录后查看）',
    // linggan 为彩色字形，不显色；换 linggan2 可走 CSS color
    icon: 'linggan2',
    iconColor: '#D94B36',
    path: '/pages/inspiration/index',
    requiresLogin: true
  },
  {
    id: 'history',
    name: '历史对话记录箱',
    desc: authStore.isLoggedIn
      ? `回顾您往期与AI沟通的手作爆单方案`
      : '回顾您往期与AI沟通的手作爆单方案（登录后查看）',
    icon: 'book',
    iconColor: '#F5A623',
    path: '/pages/mine/creation-records/index',
    requiresLogin: true
  },
  {
    id: 'referral',
    name: '我要推荐',
    desc: '邀请好友一起体验，获得算力奖励',
    icon: 'send2',
    iconColor: '#E65100',
    path: '/pages/mine/referral/index',
    requiresLogin: false
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
  await Promise.all([refreshCoinStatistics(), refreshPersonaStatus()])
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

/** 常驻 IP：独立页面编辑（与文案/分身页内的弹窗编辑共用一套 PersonaProfileEditor） */
const goToIpInfoPage = () => {
  if (!authStore.isLoggedIn) {
    goToLogin()
    return
  }
  uni.navigateTo({ url: '/pages/mine/ip-info/index' })
}
const onUserStripCoreTap = () => {
  if (!authStore.isLoggedIn) return
  if (!isVipMember.value) {
    goToMembership()
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
  background: $bg-base;
  padding-bottom: calc(168rpx + env(safe-area-inset-bottom));
  padding-bottom: calc(168rpx + constant(safe-area-inset-bottom));
  box-sizing: border-box;
}

/* ---------- 第一排：头像 + 昵称 + 数据统计 + 档案 ---------- */

.mine-user-strip-wrap {
  padding: 32rpx 40rpx 28rpx;
  box-sizing: border-box;
  background: $bg-base;
  border-bottom: 1rpx solid rgba(44, 30, 26, 0.06);
}

.mine-user-strip {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 18rpx;
}

.mine-user-strip__left {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 18rpx;
  flex-shrink: 0;
  min-width: 0;
}

.mine-user-strip__avatar-wrap {
  position: relative;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  flex-shrink: 0;
  overflow: hidden;
  border: 3rpx solid rgba(217, 75, 54, 0.12);
  background: $white;
  box-shadow: 0 6rpx 18rpx rgba(44, 30, 26, 0.07);
}

.mine-user-strip__avatar {
  width: 100%;
  height: 100%;
  display: block;
}

.mine-user-strip__crown {
  position: absolute;
  right: 2rpx;
  bottom: 2rpx;
  font-size: 28rpx;
  line-height: 1;
  filter: drop-shadow(0 2rpx 4rpx rgba(0, 0, 0, 0.2));
}

.mine-user-strip__texts {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.mine-user-strip__name {
  font-size: 36rpx;
  font-weight: 900;
  color: $text-main;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* VIP：等级名胶囊（横排 💎 | 文案，宽度随文案撑开、「钻石会员」不截断） */
.mine-user-strip__vip-badge {
  align-self: flex-start;
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
  box-sizing: border-box;
  max-width: 100%;

  /** 钻石档：浅色底上再加描边与小阴影，层次更明显 */
  &--diamond {
    border: 1rpx solid rgba(146, 64, 14, 0.35);
    box-shadow: 0 4rpx 12rpx rgba(180, 83, 9, 0.16);
  }
}

.mine-user-strip__vip-badge-emoji {
  font-size: 24rpx;
  line-height: 1;
  flex-shrink: 0;
}

.mine-user-strip__vip-badge-text {
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.35;
  flex-shrink: 0;
  white-space: nowrap;
}

.mine-user-strip__hint {
  font-size: 24rpx;
  font-weight: 600;
  color: rgba(44, 30, 26, 0.55);
  line-height: 1.35;
}

.mine-user-strip__stats {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  justify-content: flex-end;
  gap: 0;

  /* 非会员：仅剩余算力靠右 */
  &--solo-power {
    flex: 1;
    justify-content: flex-end;

    .mine-user-strip__stat {
      flex: 0 0 auto;
      max-width: none;
      min-width: 140rpx;
    }
  }
}

.mine-user-strip__stat {
  flex: 1;
  max-width: 200rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  min-width: 0;

  &--tap:active {
    opacity: 0.72;
  }
}

.mine-user-strip__stat-div {
  width: 1rpx;
  align-self: stretch;
  margin: 6rpx 4rpx;
  background: rgba(44, 30, 26, 0.08);
  flex-shrink: 0;
}

.mine-user-strip__stat-num {
  font-size: 34rpx;
  font-weight: 900;
  color: $text-main;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
  line-height: 1.1;

  &--accent {
    color: $accent-gold;
  }
}

.mine-user-strip__stat-lab {
  font-size: 20rpx;
  font-weight: 700;
  color: rgba(44, 30, 26, 0.52);
  text-align: center;
  line-height: 1.32;
}

.mine-user-strip__doc {
  position: relative;
  flex-shrink: 0;
  margin-left: auto;
  min-width: 100rpx;
  padding: 10rpx 12rpx 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20rpx;
  background: rgba(217, 75, 54, 0.06);
  border: 1rpx solid rgba(217, 75, 54, 0.12);
  box-sizing: border-box;

  &:active {
    opacity: 0.78;
  }
}

.mine-user-strip__doc-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.mine-user-strip__doc-label {
  font-size: 21rpx;
  font-weight: 800;
  color: rgba(44, 30, 26, 0.62);
  line-height: 1.15;
  letter-spacing: 0.2rpx;
}

.mine-user-strip__doc-dot {
  position: absolute;
  top: 6rpx;
  right: 8rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: $accent-gold;
  border: 2rpx solid $white;
  box-shadow: 0 4rpx 12rpx rgba(217, 75, 54, 0.25);
}

/* ---------- 第二排：已开通会员 · 尊享卡（仅皮肤与权益氛围） ---------- */

.member-tier-shell {
  margin-bottom: 20rpx;
}

.member-tier-card {
  position: relative;
  overflow: hidden;
  border-radius: 24rpx;
  padding: 32rpx 28rpx 28rpx;
  box-sizing: border-box;
  box-shadow: 0 14rpx 40rpx rgba(26, 20, 14, 0.22);

  &__gloss {
    pointer-events: none;
    position: absolute;
    top: -42%;
    right: -32%;
    width: 70%;
    height: 150%;
    background: radial-gradient(
      circle at 32% 32%,
      rgba(255, 255, 255, 0.2) 0%,
      transparent 56%
    );
    opacity: 0.92;
  }

  &__top {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16rpx;
    margin-bottom: 22rpx;
  }

  &__title-row {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 14rpx;
  }

  &__title {
    flex: 1;
    font-size: 30rpx;
    font-weight: 800;
    color: rgba(254, 243, 199, 0.98);
    line-height: 1.42;
  }

  &__desc {
    position: relative;
    z-index: 2;
    display: block;
    /** Slogan：略大字重，在长渐变卡上更易读 */
    font-size: 31rpx;
    font-weight: 600;
    color: rgba(254, 243, 199, 0.9);
    line-height: 1.52;
    /* 单行短文案时与底栏留白略加大，层级更清晰 */
    margin-bottom: 20rpx;
    letter-spacing: 0.02em;
  }

  &__footer {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
    gap: 20rpx;
    padding-top: 8rpx;
  }

  &__power {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-end;
    gap: 8rpx;
    padding: 8rpx 0 4rpx;

    &:active {
      opacity: 0.8;
    }
  }

  &__power-num {
    font-size: 38rpx;
    font-weight: 900;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
    color: rgba(255, 255, 255, 0.96);
    line-height: 1.12;
  }

  &__power-lab {
    font-size: 22rpx;
    font-weight: 700;
    color: rgba(255, 250, 235, 0.82);
    line-height: 1.3;
  }

  &__cta {
    flex-shrink: 0;
    align-self: flex-end;
    font-size: 28rpx;
    font-weight: 800;
    color: #fbbf24;
    line-height: 1.35;
    padding: 8rpx 0 10rpx 12rpx;
    white-space: nowrap;

    &:active {
      opacity: 0.78;
    }
  }

  &--skin-diamond {
    background: linear-gradient(148deg, #1b3d56 0%, #2f5f78 42%, #4a5966 100%);
    border: 1rpx solid rgba(255, 255, 255, 0.22);
  }

  &--skin-vip {
    background: linear-gradient(145deg, #3d3228 0%, #2a221c 46%, #1a1512 100%);
    border: 1rpx solid rgba(251, 191, 36, 0.18);
  }

  &--skin-svip {
    background: linear-gradient(152deg, #2a1f4a 0%, #533672 40%, #1a1430 100%);
    border: 1rpx solid rgba(240, 171, 252, 0.22);
  }

  &--skin-max {
    background: linear-gradient(152deg, #101012 0%, #282018 52%, rgba(212, 175, 55, 0.35) 100%);
    border: 1rpx solid rgba(252, 211, 77, 0.22);
  }

  &.member-tier-card--skin-vip &__power-num {
    color: #fde68a;
  }

  &.member-tier-card--skin-diamond &__cta,
  &.member-tier-card--skin-diamond &__power-num {
    color: #a5f3fc;
  }

  &.member-tier-card--skin-svip &__cta,
  &.member-tier-card--skin-svip &__power-num {
    color: #f0abfc;
  }

  &.member-tier-card--skin-max &__cta,
  &.member-tier-card--skin-max &__power-num {
    color: #fcd34d;
  }
}

.page-content {
  padding: 0 40rpx;

  &--logged {
    padding-top: 20rpx;
  }

  /* 未登录时无顶部资料区，补一段与标题栏下的呼吸间距 */
  &--guest {
    padding-top: 40rpx;
  }
}

.stats-wrap {
  position: relative;
  margin-bottom: 20rpx;
}

.stats-card {
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.04);
  border-radius: 56rpx;
  padding: 40rpx 36rpx 36rpx;
  box-shadow: $shadow-premium;

  &--locked .stat-value,
  &--locked .stat-label {
    filter: blur(6rpx);
    opacity: 0.45;
  }
}

.stats-body {
  display: flex;
  align-items: stretch;

  &--single {
    justify-content: center;

    .stat-col {
      flex: 1;
      max-width: 100%;
    }
  }
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
  background: rgba(51, 37, 30, 0.06);
  margin: 4rpx 0;
}

.stat-value {
  font-size: 46rpx;
  font-weight: 900;
  color: $text-main;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
  line-height: 1.12;

  &--accent {
    color: $accent-gold;
  }
}

.stat-label {
  font-size: 24rpx;
  font-weight: 700;
  color: rgba(44, 30, 26, 0.58);
  text-align: center;
  line-height: 1.42;
}

.stats-login-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 56rpx;
  background: rgba(255, 255, 255, 0.35);
}

.stats-login-btn {
  padding: 22rpx 52rpx;
  background: linear-gradient(135deg, $primary-orange 0%, $primary-orange-alt 100%);
  border-radius: 999rpx;
  font-size: 30rpx;
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
  font-size: 30rpx;
  font-weight: 700;
  color: #fef3c7;
  line-height: 1.42;
}

.vip-pass-badge {
  flex-shrink: 0;
  padding: 6rpx 16rpx;
  border: 1rpx solid rgba(251, 191, 36, 0.65);
  border-radius: 999rpx;
  background: rgba(251, 191, 36, 0.12);
}

.vip-pass-text {
  font-size: 22rpx;
  font-weight: 700;
  color: #fbbf24;
  letter-spacing: 1rpx;
}

.vip-desc {
  display: block;
  font-size: 26rpx;
  color: rgba(254, 243, 199, 0.9);
  line-height: 1.52;
  margin-bottom: 24rpx;
}

.vip-cta {
  font-size: 32rpx;
  font-weight: 700;
  color: #fbbf24;
}

/* 菜单行：对齐首页 `.task-card` 白卡 + $shadow-card-elevated； referral 再做一点暖色渐变凸显 */
.menu-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 36rpx;
  margin-bottom: 24rpx;
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.08);
  border-radius: 40rpx;
  box-sizing: border-box;
  overflow: hidden;
  box-shadow: $shadow-card-elevated;
  transition:
    opacity 0.2s ease,
    transform 0.22s cubic-bezier(0.33, 0.86, 0.42, 1),
    box-shadow 0.22s cubic-bezier(0.33, 0.86, 0.42, 1);

  &:active {
    opacity: 0.98;
    transform: translateY(2rpx) scale(0.992);
    box-shadow:
      inset 0 2rpx 0 rgba(255, 255, 255, 0.92),
      0 14rpx 32rpx -14rpx rgba(44, 30, 26, 0.1),
      0 6rpx 14rpx -6rpx rgba(44, 30, 26, 0.06);
  }

  &:last-child {
    margin-bottom: 0;
  }

  /** 「我要推荐」：与同级列表区分开，仍能看出是同系列任务卡 */
  &--spotlight {
    border-color: rgba(217, 75, 54, 0.22);
    background: linear-gradient(180deg, rgba(217, 75, 54, 0.06) 0%, #ffffff 44%, #ffffff 100%);
    box-shadow:
      inset 0 2rpx 0 rgba(255, 255, 255, 0.98),
      0 28rpx 58rpx -18rpx rgba(217, 75, 54, 0.16),
      0 26rpx 56rpx -18rpx rgba(44, 30, 26, 0.12),
      0 12rpx 28rpx -12rpx rgba(44, 30, 26, 0.09),
      0 4rpx 10rpx -2rpx rgba(44, 30, 26, 0.05);

    &:active {
      box-shadow:
        inset 0 2rpx 0 rgba(255, 255, 255, 0.9),
        0 16rpx 36rpx -14rpx rgba(217, 75, 54, 0.1),
        0 14rpx 32rpx -14rpx rgba(44, 30, 26, 0.08),
        0 6rpx 14rpx -6rpx rgba(44, 30, 26, 0.05);
    }
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
  width: 88rpx;
  height: 88rpx;
  border-radius: 28rpx;
  background: $accent-gold-light;
  border: 1rpx solid rgba(217, 75, 54, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-text-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.menu-name {
  font-size: 32rpx;
  font-weight: 800;
  color: $text-main;
  line-height: 1.38;
}

.menu-desc {
  font-size: 26rpx;
  font-weight: 500;
  color: rgba(44, 30, 26, 0.62);
  line-height: 1.46;
}

.menu-chevron {
  font-size: 44rpx;
  color: rgba(44, 30, 26, 0.28);
  font-weight: 300;
  flex-shrink: 0;
  margin-left: 12rpx;
}
</style>
