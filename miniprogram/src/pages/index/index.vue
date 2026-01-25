<template>
  <scroll-view scroll-y class="container">
    <view class="banner-wrapper glass-card hairline">
      <swiper class="banner-swiper" :indicator-dots="true" :autoplay="true"
:interval="4200"
        :duration="500"
        indicator-color="rgba(255,255,255,0.2)"
        indicator-active-color="#ffffff"
        circular
      >
        <swiper-item v-for="(banner, index) in bannerList" :key="index">
          <view class="banner-item">
            <view class="banner-overlay" :style="{ background: banner.bgGradient }"></view>
            <view class="banner-content">
              <view class="banner-tag" :class="{ active: index === 0 }">
                <text class="tag-text">{{ banner.tag }}</text>
              </view>
              <view class="banner-slogan">{{ banner.slogan }}</view>
              <view class="banner-main">
                <text class="main-text">{{ banner.mainText }}</text>
                <text class="main-highlight">{{ banner.highlight }}</text>
              </view>
              <view class="banner-sub">「{{ banner.subText }}」</view>
            </view>
            <image class="banner-image" :src="banner.image" mode="aspectFill" />
          </view>
        </swiper-item>
      </swiper>
    </view>

    <view class="mission-card">
      <view class="mission-text">
        <text class="mission-title">一键点火 · 创作引擎</text>
        <text class="mission-desc">深度优化的文案流程，轻盈发起任务</text>
        <view class="mission-actions">
          <view class="pill-btn" @tap="handleHotClick">
            <text class="pill-text">蹭热点</text>
          </view>
          <view class="pill-btn ghost" @tap="handleFeatureClick(featureCards[0])">
            <text class="pill-text">合成视频</text>
          </view>
        </view>
      </view>
      <text class="mission-icon">🚀</text>
    </view>

    <view class="tags-card glass-card hairline">
      <view class="tags-header">
        <text class="section-title">趋势赛道</text>
        <view class="pill-btn" @tap="handleHotClick">
          <text class="pill-text">蹭热点</text>
        </view>
      </view>
      <view class="tags-list">
        <view
class="tag-chip" v-for="(tag, index) in industryTags" :key="tag"
          :class="{ active: activeIndustry === tag, breathing: breathingTag === tag }" @tap="selectIndustry(tag)">
          <text class="chip-text">{{ tag }}</text>
        </view>
      </view>
    </view>

    <view class="nav-grid glass-card hairline">
      <view class="nav-item" v-for="(item, index) in navList" :key="index" @tap="handleNavClick(item)">
        <!-- 如果是 emoji 图标，使用原来的样式 -->
        <view v-if="isEmojiIcon(item.icon)" class="nav-icon-wrapper">
          <text class="nav-icon">{{ item.icon }}</text>
        </view>
        <!-- 否则使用 AgentIcon 组件 -->
        <AgentIcon v-else :iconName="item.icon" :size="96" />
        <text class="nav-label clamp">{{ item.label }}</text>
        <view class="nav-dot" v-if="index === activeNavIndex" />
      </view>
    </view>

    <view class="hot-card glass-card hairline">
      <view class="hot-header">
        <text class="section-title">热点快讯</text>
        <text class="hot-more">更多 〉</text>
      </view>
      <view class="hot-list">
        <view class="hot-item" v-for="(hot, index) in hotList" :key="hot.id">
          <text class="hot-rank" :class="{ top: index < 2 }">{{ index + 1 }}</text>
          <text class="hot-title clamp">{{ hot.title }}</text>
          <text class="hot-chip">实时</text>
        </view>
      </view>
    </view>

    <view class="bottom-gap" />
  </scroll-view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { getAgentList, type Agent } from '@/api/agent'
import { AgentIcon } from '@/components/base'

const authStore = useAuthStore()
const projectStore = useProjectStore()

/**
 * 判断是否为 emoji 图标
 */
const isEmojiIcon = (icon: string): boolean => {
  if (!icon) return false
  // emoji 通常是一个或多个 Unicode 字符
  const emojiRegex = /^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]+$/u
  return emojiRegex.test(icon)
}

// 顶部标题状态
const titlePrefix = ref('创意中台')
const isTitleOpen = ref(false)

const toggleTitle = () => {
  isTitleOpen.value = !isTitleOpen.value
}

// 金刚区导航数据
const navList = ref<
  Array<{
    icon: string
    label: string
    bgColor: string
    route?: string
    agentId?: string
    isMore?: boolean
  }>
>([])

// 赛道标签
const industryTags = reactive(['商业热点', '电商大促', '娱乐风向', '科技出圈', '城市事件', '生活方式'])
const activeIndustry = ref(industryTags[0])
const breathingTag = ref(industryTags[0])

const selectIndustry = (tag: string) => {
  activeIndustry.value = tag
  breathingTag.value = tag
  // 触发呼吸灯动画重置
  setTimeout(() => {
    breathingTag.value = ''
  }, 2400)
}

// 热点列表
const hotList = reactive([
  { id: 1, title: '短剧赛道 ROI 飙升，十步成片打法揭秘' },
  { id: 2, title: 'AI 主播降本 60%，直播行业进入长尾爆发期' },
  { id: 3, title: '春节档宣发提前锁量，抖音投放策略调整' },
  { id: 4, title: '城市夜经济主题视频走红，线下店铺引流指南' }
])

const activeNavIndex = computed(() => 0)

// 加载智能体列表
const loadAgentList = async () => {
  try {
    const response = await getAgentList()
    if (response.code === 200 && response.data?.agents) {
      const agents = response.data.agents
      const maxDisplay = 7 // 最多显示7个

      // 生成背景色数组
      const bgColors = [
        'linear-gradient(135deg, rgba(255, 136, 0, 0.15) 0%, rgba(255, 184, 77, 0.2) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.12) 0%, rgba(255, 184, 77, 0.18) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.18) 0%, rgba(255, 184, 77, 0.22) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.14) 0%, rgba(255, 184, 77, 0.19) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.16) 0%, rgba(255, 184, 77, 0.21) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.13) 0%, rgba(255, 184, 77, 0.17) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.17) 0%, rgba(255, 184, 77, 0.23) 100%)',
        'linear-gradient(135deg, rgba(255, 136, 0, 0.15) 0%, rgba(255, 184, 77, 0.2) 100%)'
      ]

      // 转换智能体数据为导航项
      const agentNavItems = agents.slice(0, maxDisplay).map((agent, index) => ({
        icon: agent.icon || '🤖',
        label: agent.name || '智能体',
        bgColor: bgColors[index % bgColors.length],
        route: '/pages/copywriting/index',
        agentId: agent.id
      }))

      // 添加"更多"按钮
      const moreItem = {
        icon: '⭐',
        label: '更多',
        bgColor: 'linear-gradient(135deg, rgba(255, 136, 0, 0.15) 0%, rgba(255, 184, 77, 0.2) 100%)',
        route: '/pages/agent/index',
        isMore: true
      }

      navList.value = [...agentNavItems, moreItem]
    } else {
      console.warn('获取智能体列表失败，使用默认数据')
      setDefaultNavList()
    }
  } catch (error) {
    console.error('加载智能体列表失败:', error)
    setDefaultNavList()
  }
}

// 设置默认导航列表
const setDefaultNavList = () => {
  const defaultBgColors = [
    'linear-gradient(135deg, rgba(255, 136, 0, 0.15) 0%, rgba(255, 184, 77, 0.2) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.12) 0%, rgba(255, 184, 77, 0.18) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.18) 0%, rgba(255, 184, 77, 0.22) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.14) 0%, rgba(255, 184, 77, 0.19) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.16) 0%, rgba(255, 184, 77, 0.21) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.13) 0%, rgba(255, 184, 77, 0.17) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.17) 0%, rgba(255, 184, 77, 0.23) 100%)',
    'linear-gradient(135deg, rgba(255, 136, 0, 0.15) 0%, rgba(255, 184, 77, 0.2) 100%)'
  ]
  navList.value = [
    { icon: '👥', label: 'IP问答型文案', bgColor: defaultBgColors[0], route: '/pages/copywriting/index' },
    { icon: '💬', label: '高效口播文案', bgColor: defaultBgColors[1], route: '/pages/copywriting/index' },
    { icon: '🔥', label: '爆款选题创作', bgColor: defaultBgColors[2], route: '/pages/copywriting/index' },
    { icon: '▶️', label: '爆款文案拆解', bgColor: defaultBgColors[3], route: '/pages/copywriting/index' },
    { icon: '📝', label: '爆款文案仿写', bgColor: defaultBgColors[4], route: '/pages/copywriting/index' },
    { icon: '🎵', label: '抖音热点文案', bgColor: defaultBgColors[5], route: '/pages/copywriting/index' },
    { icon: '👍', label: '使用技巧', bgColor: defaultBgColors[6], route: '/pages/copywriting/index' },
    { icon: '⭐', label: '更多', bgColor: defaultBgColors[7], route: '/pages/agent/index', isMore: true }
  ]
}

// 初始化时加载项目
onMounted(async () => {
  await loadAgentList()
})

// Banner 轮播数据
const bannerList = reactive([
  {
    tag: 'ARTIFICIAL INTELLIGENCE',
    slogan: 'New Future',
    mainText: '一次投入，',
    highlight: '持续收益',
    subText: '加入我们，成为终身代理',
    bgGradient: 'linear-gradient(135deg, #FF8800 0%, #F37021 100%)',
    image: '/static/default-avatar.png'
  },
  {
    tag: 'AI COPYWRITING',
    slogan: 'Smart Content',
    mainText: '智能文案，',
    highlight: '高效创作',
    subText: '让AI为你的创意赋能',
    bgGradient: 'linear-gradient(135deg, #FF8800 0%, #FFB84D 100%)',
    image: '/static/default-avatar.png'
  },
  {
    tag: 'DIGITAL HUMAN',
    slogan: 'Virtual Avatar',
    mainText: '数字分身，',
    highlight: '无限可能',
    subText: '打造你的专属数字人',
    bgGradient: 'linear-gradient(135deg, #F37021 0%, #FF8800 100%)',
    image: '/static/default-avatar.png'
  }
])

// 功能卡片数据
const featureCards = reactive([
  {
    title: '合成视频',
    desc: 'AI数字人视频',
    icon: '🎬',
    bgGradient: 'linear-gradient(135deg, #FF8800 0%, #FFB84D 100%)',
    route: '/pages/video/create'
  },
  {
    title: '形象克隆',
    desc: '定制专属数字人',
    icon: '▶️',
    bgGradient: 'linear-gradient(135deg, #F37021 0%, #FF8800 100%)',
    route: '/pages/avatar/clone'
  }
])

// 事件处理
const handleNavClick = async (item: any) => {
  console.log('导航点击:', item.label)
  if (item.isMore) {
    uni.navigateTo({ url: '/pages/agent/index' })
    return
  }
  if (item.route) {
    uni.navigateTo({ url: item.route })
  }
}

const handleFeatureClick = async (card: any) => {
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return
  console.log('功能卡片点击:', card.title)
}

const handleHotClick = () => {
  console.log('蹭热点触发')
}
</script>

<style scoped lang="scss">
.container {
  position: relative;
  height: 100vh;
    padding: 28rpx 32rpx 10rpx;
    background: linear-gradient(180deg, #f5f7fb 0%, #eef2f7 100%);
    box-sizing: border-box;

  .bg-decoration {
    position: absolute;
      inset: 0;
    pointer-events: none;

    .deco-circle {
      position: absolute;
      width: 480rpx;
        height: 480rpx;
      border-radius: 50%;
      filter: blur(90rpx);
        opacity: 0.35;

      &.c1 {
        top: -120rpx;
          left: -140rpx;
          background: radial-gradient(circle at 30% 30%, #ffd7b0 0%, rgba(255, 156, 75, 0) 55%);
      }

      &.c2 {
        bottom: -180rpx;
          right: -160rpx;
          background: radial-gradient(circle at 60% 50%, #d7e6ff 0%, rgba(87, 140, 255, 0) 60%);
      }
    }
    }

    .glass-card {
      position: relative;
      background: rgba(255, 255, 255, 0.78);
      border-radius: 28rpx;
      backdrop-filter: blur(12rpx);
      box-shadow: 0 18rpx 36rpx rgba(32, 58, 103, 0.08);
      margin-bottom: 28rpx;
  
      &.hairline {
        border: 1rpx solid rgba(255, 255, 255, 0.65);
      }
    }
  
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 28rpx 26rpx;
      margin-bottom: 32rpx;
      box-shadow: 0 14rpx 32rpx rgba(255, 136, 0, 0.08);

      .top-title {
        display: flex;
        align-items: center;
        gap: 10rpx;
        color: #1f2937;
        font-size: 32rpx;
        font-weight: 700;

        .title-strong {
          color: #ff8800;
        }

        .title-sub {
          color: #111827;
        }

        .chevron {
          display: inline-block;
          font-size: 26rpx;
          color: #9ca3af;
          transition: transform 0.25s ease;

          &.open {
            transform: rotate(180deg);
          }
        }
      }

      .top-subtext {
        color: #9ca3af;
        font-size: 24rpx;
      }

      .loader {
        width: 18rpx;
        height: 18rpx;
        border-radius: 50%;
        border: 3rpx solid rgba(255, 136, 0, 0.25);
        border-top-color: #ff8800;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    }

    .banner-wrapper {
      padding: 0;
      overflow: hidden;

      .banner-swiper {
        height: 360rpx;
      }

      .banner-item {
        position: relative;
        height: 100%;
        border-radius: 28rpx;
        overflow: hidden;

        .banner-overlay {
          position: absolute;
          inset: 0;
          opacity: 0.85;
        }

        .banner-content {
          position: absolute;
          inset: 0;
          padding: 40rpx 36rpx;
          display: flex;
          flex-direction: column;
          gap: 12rpx;
          color: #ffffff;
          z-index: 1;

          .banner-tag {
            align-self: flex-start;
            padding: 10rpx 20rpx;
            border-radius: 999rpx;
            font-size: 20rpx;
            letter-spacing: 1rpx;
            background: rgba(255, 255, 255, 0.22);
            color: #ffffff;

            &.active {
              box-shadow: 0 12rpx 20rpx rgba(255, 255, 255, 0.18);
            }

            .tag-text {
              font-size: 20rpx;
            }
          }

          .banner-slogan {
            font-size: 28rpx;
            opacity: 0.9;
          }

          .banner-main {
            display: flex;
            gap: 10rpx;
            font-size: 36rpx;
            font-weight: 700;

            .main-text {
              color: #fff7ed;
            }

            .main-highlight {
              color: #ffffff;
            }
          }

          .banner-sub {
            font-size: 24rpx;
            opacity: 0.9;
          }
        }

        .banner-image {
          position: absolute;
          right: 32rpx;
          bottom: 12rpx;
          width: 220rpx;
          height: 220rpx;
          opacity: 0.9;
        }
      }
    }

    .mission-card {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 32rpx;
      border-radius: 28rpx;
      background: linear-gradient(135deg, rgba(255, 136, 0, 0.1) 0%, rgba(255, 184, 77, 0.18) 100%);
      box-shadow: 0 16rpx 30rpx rgba(255, 136, 0, 0.12);
      margin: 30rpx 0;

      .mission-text {
        display: flex;
        flex-direction: column;
        gap: 12rpx;
        color: #1f2937;

        .mission-title {
          font-size: 34rpx;
          font-weight: 700;
        }

        .mission-desc {
          font-size: 26rpx;
          color: #6b7280;
        }

        .mission-actions {
          display: flex;
          gap: 18rpx;
        }
      }

      .mission-icon {
        font-size: 64rpx;
      }
    }

    .pill-btn {
      min-width: 156rpx;
      padding: 16rpx 22rpx;
      border-radius: 999rpx;
      background: linear-gradient(135deg, #ff8800 0%, #f7a13d 100%);
      color: #ffffff;
    text-align: center;
    font-size: 26rpx;
      box-shadow: 0 14rpx 26rpx rgba(255, 136, 0, 0.18);
    
      &.ghost {
        background: rgba(255, 255, 255, 0.9);
        color: #ff8800;
        box-shadow: none;
        border: 1rpx solid rgba(255, 136, 0, 0.25);
      }

      .pill-text {
        font-size: 26rpx;
        font-weight: 600;
      }
    }

    .tags-card {
      padding: 28rpx;

      .tags-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20rpx;

        .section-title {
          font-size: 30rpx;
          font-weight: 700;
          color: #111827;
        }
      }

      .tags-list {
        display: flex;
        flex-wrap: wrap;
        gap: 16rpx 14rpx;

        .tag-chip {
          padding: 18rpx 24rpx;
          border-radius: 16rpx;
          background: rgba(255, 255, 255, 0.9);
          color: #1f2937;
          font-size: 24rpx;
          border: 1rpx solid rgba(255, 136, 0, 0.12);
          transition: all 0.2s ease;

          .chip-text {
            font-weight: 600;
          }

          &.active {
            background: linear-gradient(135deg, #ff8800 0%, #ffb84d 100%);
            color: #fff;
            box-shadow: 0 12rpx 22rpx rgba(255, 136, 0, 0.18);

            &.breathing {
              animation: breathing 2.4s ease-in-out infinite;
            }
          }
        }
      }
    }

    @keyframes breathing {
      0% {
        box-shadow: 0 0 0 0 rgba(255, 136, 0, 0.18);
      }
        50% {
          box-shadow: 0 0 0 12rpx rgba(255, 136, 0, 0.08);
        }
        100% {
          box-shadow: 0 0 0 0 rgba(255, 136, 0, 0.18);
        }
        }

    .nav-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 18rpx;
      padding: 22rpx 18rpx 10rpx;

      .nav-item {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12rpx;
        padding: 20rpx 12rpx;
        border-radius: 20rpx;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: inset 0 0 0 1rpx rgba(255, 136, 0, 0.05);

        .nav-icon-wrapper {
          width: 96rpx;
          height: 96rpx;
          border-radius: 24rpx;
          display: grid;
          place-items: center;
          background: linear-gradient(135deg, rgba(255, 136, 0, 0.14) 0%, rgba(255, 184, 77, 0.22) 100%);
          font-size: 44rpx;
        }

        .nav-label {
          font-size: 26rpx;
          color: #1f2937;
          text-align: center;

          &.clamp {
            display: -webkit-box;
            -webkit-line-clamp: 1;
            line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        }

        .nav-dot {
          position: absolute;
          top: 12rpx;
          right: 12rpx;
          width: 10rpx;
          height: 10rpx;
          border-radius: 50%;
          background: #ff8800;
          box-shadow: 0 0 0 8rpx rgba(255, 136, 0, 0.12);
        }
      }
    }
    .hot-card {
      padding: 26rpx 24rpx;

      .hot-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20rpx;

        .hot-more {
          color: #9ca3af;
          font-size: 24rpx;
        }
      }

      .hot-list {
        display: flex;
        flex-direction: column;
        gap: 18rpx;

        .hot-item {
          display: grid;
          grid-template-columns: 60rpx 1fr 100rpx;
          align-items: center;
          padding: 18rpx 16rpx;
          border-radius: 18rpx;
          background: rgba(255, 255, 255, 0.92);
          box-shadow: 0 12rpx 22rpx rgba(17, 24, 39, 0.04);

          .hot-rank {
            font-size: 26rpx;
            font-weight: 700;
            color: #9ca3af;

            &.top {
              color: #ff8800;
            }
          }

          .hot-title {
            font-size: 26rpx;
            color: #1f2937;
            line-height: 1.4;

            &.clamp {
              display: -webkit-box;
              -webkit-line-clamp: 1;
              line-clamp: 1;
              -webkit-box-orient: vertical;
              overflow: hidden;
            }
          }

          .hot-chip {
            justify-self: end;
            font-size: 22rpx;
            color: #ff8800;
            background: rgba(255, 136, 0, 0.12);
            padding: 10rpx 16rpx;
            border-radius: 999rpx;
          }
        }
      }
    }

    .bottom-gap {
      height: 60rpx;
    }
  }
</style>