<template>
  <view class="page-mine">
   <!-- 已登录：头像金圈 + 昵称认证 + 会员徽章 + IP 毛玻璃卡 -->
    <view v-if="authStore.isLoggedIn" class="mine-user-strip-wrap">
      <view class="mine-user-strip">
        <view class="mine-user-strip__left" @tap="onUserStripCoreTap">
         <view class="mine-user-strip__avatar-ring">
            <view class="mine-user-strip__avatar-shell">
              <image class="mine-user-strip__avatar" :src="avatarUrl" mode="aspectFill" />
             <view class="mine-user-strip__online-dot" />
            </view>
          </view>
          <view class="mine-user-strip__texts">
           <view class="mine-user-strip__name-row">
              <text class="mine-user-strip__name">{{ displayNickname }}</text>
             <SvgIcon name="badge-check" :size="32" color="#F97316" />
            </view>
            <template v-if="isVipMember">
              <view
                class="mine-user-strip__vip-badge"
:class="{
                'mine-user-strip__vip-badge--gold': !vipBadgeShowDiamondIcon,
                'mine-user-strip__vip-badge--diamond': vipBadgeShowDiamondIcon
              }" :style="vipBadgeShowDiamondIcon
                ? { backgroundColor: memberLevelBadgeStyle.backgroundColor }
                : undefined
                "
              >
               <SvgIcon v-if="!vipBadgeShowDiamondIcon" name="crown" :size="22" color="#B45309" />
                <text v-else class="mine-user-strip__vip-badge-emoji">💎</text>
                <text
                  class="mine-user-strip__vip-badge-text"
                 :style="vipBadgeShowDiamondIcon ? { color: memberLevelBadgeStyle.color } : undefined"
                >
                  {{ memberBadgeText }}
                </text>
              </view>
              <text v-if="memberExpireDisplay" class="mine-user-strip__expire">
                {{ memberExpireDisplay }}
              </text>
            </template>
           <template v-else>
              <text class="mine-user-strip__hint">开通会员解锁更多权益</text>
            </template>
          </view>
       </view>
        <view
          v-if="!isVipMember"
          class="mine-user-strip__stats mine-user-strip__stats--solo-power"
        >
          <view class="mine-user-strip__stat mine-user-strip__stat--tap" @tap.stop="goToPowerCenter">
            <text class="mine-user-strip__stat-num mine-user-strip__stat-num--accent">{{ powerDisplay }}</text>
           <text class="mine-user-strip__stat-lab">剩余积分 (Tokens)</text>
          </view>
        </view>
       <view class="mine-user-strip__ip-card" @tap.stop="goToIpInfoPage">
          <view class="mine-user-strip__ip-icon-wrap">
            <SvgIcon name="contact-2" :size="32" color="#FFFFFF" />
          </view>
         <text class="mine-user-strip__ip-label">IP信息</text>
          <view v-if="showPersonaDot" class="mine-user-strip__ip-dot" />
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
              <text class="stat-label">剩余积分(tokens)</text>
            </view>
          </view>
        </view>
        <view class="stats-login-mask">
          <view class="stats-login-btn" @tap.stop="goToLogin">登录解锁数据</view>
        </view>
      </view>

    <!-- 第二排 · 已购会员：黑金尊享卡 + 积分能量条 -->
      <view v-if="authStore.isLoggedIn && isVipMember" class="member-tier-shell">
       <view class="member-tier-card" :class="memberTierSkinClass">
          <view class="member-tier-card__gloss" aria-hidden="true" />
         <view class="member-tier-card__mesh" aria-hidden="true" />
          <view class="member-tier-card__top">
            <view class="member-tier-card__title-row">
             <view class="vip-crown-box vip-crown-box--dark">
                <SvgIcon name="crown" :size="32" color="#FBBF24" />
              </view>
              <text class="member-tier-card__title">{{ memberTierTitle }}</text>
            </view>
            <view class="vip-pass-badge">
              <text class="vip-pass-text">VIP PASS</text>
            </view>
          </view>
         <text class="member-tier-card__desc">「{{ memberTierDesc }}」</text>
          <view class="member-tier-card__footer">
            <view class="member-tier-card__power" @tap.stop="goToPowerCenter">
              <text class="member-tier-card__power-num">{{ powerDisplay }}</text>
             <text class="member-tier-card__power-lab">剩余积分 (Tokens)</text>
            </view>
           <view
             v-if="!releaseReviewEnabled"
             class="member-tier-card__cta-btn"
             @tap.stop="goToMembership"
           >
              <text class="member-tier-card__cta-text">查看会员权益</text>
              <SvgIcon name="chevron-right" :size="22" color="#FCD34D" />
            </view>
          </view>
          <view v-if="powerTotalTokens > 0" class="member-tier-card__energy">
            <view class="member-tier-card__energy-track">
              <view class="member-tier-card__energy-fill" :style="{ width: powerRemainPercent + '%' }" />
            </view>
            <view class="member-tier-card__energy-labels">
              <text>已用 {{ powerUsedPercent }}%</text>
              <text>总量 {{ powerTotalDisplay }} Tokens</text>
            </view>
          </view>
        </view>
      </view>

    <!-- 第二排 · 未开通：黑金推广卡 -->
      <view v-if="authStore.isLoggedIn && !isVipMember" class="vip-annual-card" @tap="goToMembership">
       <view class="vip-annual-card__gloss" aria-hidden="true" />
        <view class="vip-annual-card__mesh" aria-hidden="true" />
        <view class="vip-card-top">
          <view class="vip-title-row">
           <view class="vip-crown-box vip-crown-box--dark">
              <SvgIcon name="crown" :size="32" color="#FBBF24" />
            </view>
            <text class="vip-title">{{ vipCardTitle }}</text>
          </view>
          <view class="vip-pass-badge">
            <text class="vip-pass-text">VIP PASS</text>
          </view>
        </view>
        <text class="vip-desc">{{ vipCardDesc }}</text>
       <view class="vip-cta-row">
          <text class="vip-cta">{{ vipCardCta }}</text>
          <SvgIcon name="chevron-right" :size="28" color="#FBBF24" />
        </view>
      </view>

    <view v-if="authStore.isLoggedIn" class="assets-section-title">
        <text>我的个人资产与记录</text>
      </view>

      <!-- 功能列表 -->
      <view class="menu-list">
        <view v-for="item in menuList" :key="item.id" class="menu-card" @tap="handleMenuClick(item)">
          <view class="menu-left">
           <view class="menu-icon-wrap" :class="item.iconBgClass">
              <SvgIcon :name="item.icon" :size="44" :color="item.iconColor ?? '#D94B36'" />
            </view>
            <view class="menu-text-col">
              <text class="menu-name">{{ item.name }}</text>
              <text class="menu-desc">{{ item.desc }}</text>
            </view>
          </view>
         <view class="menu-right">
            <view v-if="item.badge" class="menu-badge" :class="{ 'menu-badge--pulse': item.badgeHighlight }">
              <SvgIcon v-if="item.badgeHighlight" name="badge-plus" :size="22" color="#B45309" />
              <text>{{ item.badge }}</text>
            </view>
            <SvgIcon name="chevron-right" :size="32" color="#D6D3D1" />
          </view>
        </view>
      </view>

      <view class="mine-version-footer">
        <text>顶顶妈 AI 系统 v1.1.0 • 火源文化技术支持</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { getCoinStatistics, type CoinStatisticsData } from '@/api/coin'
import { getInspirationList } from '@/api/inspiration'
import { getConversationList } from '@/api/conversation'
import { useAuthStore } from '@/stores/auth'
import { DINGMA_DEFAULT_PROFILE_AVATAR_URL } from '@/constants/tenant'
import SvgIcon from '@/components/base/SvgIcon.vue'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'
import { getTenantPublicConfig } from '@/api/tenant'

/** 会员到期日展示（YYYY-MM-DD），避免独立 utils 模块在小程序 lazyCodeLoading 下未注册 */
function formatVipExpireDate(raw: string): string {
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return ''
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const authStore = useAuthStore()
const projectStore = useProjectStore()

const coinStats = ref<CoinStatisticsData | null>(null)
const personaIncomplete = ref(true)
const inspirationCount = ref<number | null>(null)
const conversationCount = ref<number | null>(null)
/** 上线审查开启时隐藏「查看会员权益」 */
const releaseReviewEnabled = ref(false)

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

const memberExpireDisplay = computed(() => {
  const u = authStore.userInfo
  const raw = u?.vip_expire_date || u?.expireDate
  if (!raw) return ''
  const formatted = formatVipExpireDate(String(raw))
  return formatted ? `${formatted} 到期` : ''
})

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
const memberTierTitle = computed(() => '顶妈AI分身年卡')

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

const vipCardTitle = '顶妈AI分身年卡 · 开通尊享特权'
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

const powerTotalTokens = computed(() => {
  const s = coinStats.value
  if (!s) return 0
  const avail = Number(s.availableBalance) || 0
  const consumed = Number(s.totalConsume) || 0
  if (avail + consumed > 0) return avail + consumed
  return Number(s.balance) || avail
})

const powerUsedPercent = computed(() => {
  const total = powerTotalTokens.value
  if (total <= 0) return 0
  const avail = Number(coinStats.value?.availableBalance ?? 0)
  const used = Math.max(0, total - avail)
  return Math.min(100, Math.max(0, Math.round((used / total) * 100)))
})

const powerRemainPercent = computed(() =>
  Math.min(100, Math.max(0, 100 - powerUsedPercent.value))
)

const powerTotalDisplay = computed(() => formatNumberInt(powerTotalTokens.value))

interface MenuItem {
  id: string
  name: string
  desc: string
  icon: string
  iconColor?: string
  iconBgClass?: string
  badge?: string
  badgeHighlight?: boolean
  path: string
  requiresLogin: boolean
}

const allMenuList = computed<MenuItem[]>(() => [
  {
    id: 'inspiration',
    name: '我的灵感夹',
    desc: authStore.isLoggedIn
      ? '收录您随时随手捕捉的好点子脑洞'
      : '收录您随时随手捕捉的好点子脑洞（登录后查看）',
    icon: 'lightbulb',
    iconColor: '#F43F5E',
    iconBgClass: 'menu-icon-wrap--rose',
    badge:
      authStore.isLoggedIn && inspirationCount.value != null
        ? `${inspirationCount.value} 个想法`
        : undefined,
    path: '/pages/inspiration/index',
    requiresLogin: true
  },
  {
    id: 'history',
    name: '历史对话记录箱',
    desc: authStore.isLoggedIn
      ? '回顾您往期与AI沟通的手作爆单方案'
      : '回顾您往期与AI沟通的手作爆单方案（登录后查看）',
    icon: 'history',
    iconColor: '#D97706',
    iconBgClass: 'menu-icon-wrap--amber',
    badge:
      authStore.isLoggedIn && conversationCount.value != null
        ? `${conversationCount.value} 组记录`
        : undefined,
    path: '/pages/mine/creation-records/index',
    requiresLogin: true
  },
  {
    id: 'referral',
    name: '我要推荐',
    desc: '邀请好友一起体验，获得积分奖励',
    icon: 'send',
    iconColor: '#EC4899',
    iconBgClass: 'menu-icon-wrap--pink',
    badge: '送积分',
    badgeHighlight: true,
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

const refreshMenuCounts = async () => {
  if (!authStore.isLoggedIn) {
    inspirationCount.value = null
    conversationCount.value = null
    return
  }
  try {
    const [inspRes, convRes] = await Promise.all([
      getInspirationList({ pageNum: 1, pageSize: 1 }),
      getConversationList({ pageNum: 1, pageSize: 1, status: 'active' })
    ])
    if (inspRes.code === 200 && inspRes.data) {
      inspirationCount.value = inspRes.data.total ?? 0
    }
    if (convRes.code === 200 && convRes.data) {
      conversationCount.value = convRes.data.total ?? 0
    }
  } catch {
    // 计数失败时保留上次值或隐藏角标
  }
}

const refreshTenantConfig = async () => {
  try {
    const res = await getTenantPublicConfig()
    if (res.code === 200 && res.data) {
      releaseReviewEnabled.value = !!res.data.release_review_enabled
    }
  } catch {
    releaseReviewEnabled.value = false
  }
}

const refreshAll = async () => {
  await Promise.all([refreshUserInfo(), refreshTenantConfig()])
  await Promise.all([
    refreshCoinStatistics(),
    refreshPersonaStatus(),
    refreshMenuCounts()
  ])
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
  padding: 24rpx 32rpx 28rpx;
  box-sizing: border-box;
  background: $bg-base;
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

.mine-user-strip__avatar-ring {
  flex-shrink: 0;
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  padding: 4rpx;
  background: linear-gradient(135deg, #fbbf24 0%, #f97316 48%, #f43f5e 100%);
  box-shadow: 0 8rpx 20rpx rgba(249, 115, 22, 0.22);
}

.mine-user-strip__avatar-shell {
  position: relative;
  width: 100%;
    height: 100%;
  border-radius: 50%;
  padding: 3rpx;
  background: $white;
  box-sizing: border-box;
    overflow: hidden;
}

.mine-user-strip__avatar {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 50%;
    background: #f5f5f4;
}

.mine-user-strip__online-dot {
  position: absolute;
  right: 4rpx;
    bottom: 4rpx;
    width: 24rpx;
    height: 24rpx;
    border-radius: 50%;
    background: #10b981;
    border: 4rpx solid $white;
    box-sizing: border-box;
  }
  
  .mine-user-strip__name-row {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 10rpx;
    min-width: 0;
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
  font-weight: 800;
    color: #292524;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
    min-width: 0;
}

.mine-user-strip__vip-badge {
  align-self: flex-start;
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  box-sizing: border-box;
  max-width: 100%;

  &--gold {
      background: linear-gradient(90deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.2) 100%);
      border: 1rpx solid rgba(245, 158, 11, 0.28);
      box-shadow: 0 4rpx 12rpx rgba(180, 83, 9, 0.08);
  
      .mine-user-strip__vip-badge-text {
        color: #b45309;
        font-size: 20rpx;
        font-weight: 700;
      }
    }
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

.mine-user-strip__expire {
  font-size: 22rpx;
  font-weight: 500;
  color: rgba(44, 30, 26, 0.45);
  line-height: 1.35;
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

  /* 非会员：仅剩余积分靠右 */
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

.mine-user-strip__ip-card {
  position: relative;
  flex-shrink: 0;
  margin-left: auto;
  width: 152rpx;
    height: 152rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
    border-radius: 32rpx;
    background: linear-gradient(145deg, #fffbeb 0%, rgba(255, 237, 213, 0.65) 100%);
    border: 1rpx solid rgba(251, 146, 60, 0.35);
    box-shadow: 0 8rpx 20rpx rgba(251, 146, 60, 0.12);
  box-sizing: border-box;

  &:active {
    transform: scale(0.96);
      opacity: 0.92;
  }
}

.mine-user-strip__ip-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #f97316 0%, #fbbf24 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 14rpx rgba(249, 115, 22, 0.28);
}

.mine-user-strip__ip-label {
  font-size: 20rpx;
  font-weight: 800;
  color: #44403c;
    letter-spacing: 2rpx;
}

.mine-user-strip__ip-dot {
  position: absolute;
  top: -4rpx;
    right: -4rpx;
    width: 20rpx;
    height: 20rpx;
  border-radius: 50%;
  background: #f43f5e;
    border: 4rpx solid $white;
    box-sizing: border-box;
}

/* ---------- 第二排：已开通会员 · 尊享卡（仅皮肤与权益氛围） ---------- */

.member-tier-shell {
  margin-bottom: 20rpx;
}

.member-tier-card {
  position: relative;
  overflow: hidden;
  border-radius: 32rpx;
    padding: 36rpx 32rpx 30rpx;
  box-sizing: border-box;
  box-shadow: 0 16rpx 44rpx rgba(18, 17, 16, 0.28);

  &__gloss {
    pointer-events: none;
    position: absolute;
    top: -30%;
      right: -20%;
      width: 72%;
      height: 120%;
    background: radial-gradient(
      circle at 70% 20%,
        rgba(245, 158, 11, 0.22) 0%,
        transparent 58%
    );
    opacity: 0.75;
    }
    
    &__mesh {
      pointer-events: none;
      position: absolute;
      inset: 0;
      opacity: 0.35;
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
      background-size: 32rpx 32rpx;
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
    font-size: 24rpx;
      font-weight: 400;
      color: rgba(214, 211, 209, 0.92);
      line-height: 1.55;
      margin-bottom: 24rpx;
      letter-spacing: 0.04em;
  }

  &__footer {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16rpx;
      padding-top: 4rpx;
    }
    
    &__energy {
      position: relative;
      z-index: 2;
      margin-top: 20rpx;
      display: flex;
      flex-direction: column;
      gap: 8rpx;
    }
    
    &__energy-track {
      width: 100%;
      height: 6rpx;
      border-radius: 999rpx;
      background: #292524;
      overflow: hidden;
    }
    
    &__energy-fill {
      height: 100%;
      border-radius: 999rpx;
      background: linear-gradient(90deg, #f97316 0%, #fbbf24 48%, #fde047 100%);
      box-shadow: 0 0 16rpx rgba(245, 158, 11, 0.45);
      transition: width 0.35s ease;
    }
    
    &__energy-labels {
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      font-size: 16rpx;
      font-weight: 600;
      color: rgba(168, 162, 158, 0.95);
      letter-spacing: 0.02em;
    }
    
    &__cta-btn {
      flex-shrink: 0;
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 6rpx;
      padding: 12rpx 22rpx;
      border-radius: 999rpx;
      background: rgba(255, 255, 255, 0.06);
      border: 1rpx solid rgba(255, 255, 255, 0.12);
    
      &:active {
        opacity: 0.78;
      }
    }
    
    &__cta-text {
      font-size: 22rpx;
      font-weight: 800;
      color: #fcd34d;
      line-height: 1.2;
      white-space: nowrap;
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
    font-size: 56rpx;
    font-weight: 900;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
    line-height: 1.05;
      color: #fde68a;
      background: linear-gradient(90deg, #fde68a 0%, #fcd34d 42%, #fb923c 100%);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
  }

  &__power-lab {
    font-size: 20rpx;
      font-weight: 600;
      color: rgba(168, 162, 158, 0.95);
    line-height: 1.3;
    letter-spacing: 0.06em;
      text-transform: uppercase;
  }

  &--skin-diamond {
    background: linear-gradient(148deg, #1b3d56 0%, #2f5f78 42%, #4a5966 100%);
    border: 1rpx solid rgba(255, 255, 255, 0.22);
  }

  &--skin-vip {
    background: linear-gradient(145deg, #2d2926 0%, #1e1c1a 52%, #121110 100%);
      border: 1rpx solid #44403c;
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
  position: relative;
    overflow: hidden;
    padding: 36rpx 32rpx 30rpx;
    border-radius: 32rpx;
  margin-bottom: 20rpx;
  background: linear-gradient(145deg, #2d2926 0%, #1e1c1a 52%, #121110 100%);
    border: 1rpx solid #44403c;
    box-shadow: 0 16rpx 44rpx rgba(18, 17, 16, 0.28);

  &:active {
    opacity: 0.94;
  }
&__gloss {
  pointer-events: none;
  position: absolute;
  top: -30%;
  right: -20%;
  width: 72%;
  height: 120%;
  background: radial-gradient(circle at 70% 20%,
      rgba(245, 158, 11, 0.2) 0%,
      transparent 58%);
}

&__mesh {
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: 0.35;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 32rpx 32rpx;
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
  &--dark {
    background: rgba(245, 158, 11, 0.12);
    border: 1rpx solid rgba(251, 191, 36, 0.28);
  }
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

.vip-cta-row {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
}
.vip-cta {
  font-size: 32rpx;
  font-weight: 700;
  color: #fbbf24;
}

.assets-section-title {
  padding: 8rpx 0 20rpx;

  text {
    font-size: 24rpx;
    font-weight: 800;
    color: rgba(120, 113, 108, 0.95);
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
  padding-bottom: 12rpx;
}
.menu-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 28rpx;
    margin-bottom: 0;
  background: $white;
  border: 1rpx solid rgba(44, 30, 26, 0.06);
    border-radius: 32rpx;
  box-sizing: border-box;
  overflow: hidden;
  box-shadow: $shadow-card-elevated;

  &:active {
    opacity: 0.96;
      transform: translateX(2rpx);
  }
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
  min-width: 0;
}

.menu-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.menu-badge {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 4rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #f5f5f4;
  font-size: 20rpx;
  font-weight: 600;
  color: #78716c;

  &--pulse {
    background: #fef3c7;
    border: 1rpx solid #fde68a;
    color: #b45309;
    font-weight: 800;
    animation: mine-badge-pulse 2s ease-in-out infinite;
  }
}

@keyframes mine-badge-pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.72;
  }
}
.menu-icon-wrap {
  position: relative;
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &--rose {
    background: #fff1f2;
    border: 1rpx solid #fecdd3;
  }

  &--amber {
    background: #fffbeb;
    border: 1rpx solid #fde68a;
  }

  &--pink {
    background: #fdf2f8;
    border: 1rpx solid #fbcfe8;
  }
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

.mine-version-footer {
  width: 100%;
  padding: 16rpx 0 24rpx;
  text-align: center;

  text {
    font-size: 20rpx;
    color: rgba(120, 113, 108, 0.72);
    letter-spacing: 0.04em;
  }
}
</style>
