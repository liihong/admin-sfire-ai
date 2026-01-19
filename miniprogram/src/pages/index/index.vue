<template>
  <view class="container">
    <!-- 背景装饰 -->
    <view class="bg-decoration">
      <view class="deco-circle c1"></view>
      <view class="deco-circle c2"></view>
    </view>

    <!-- 顶部标题栏 -->
    <!-- <view class="header">
      <text class="header-title">火源文案智能体</text>
    </view> -->

    <!-- Banner 轮播图 -->
    <view class="banner-wrapper">
      <swiper 
        class="banner-swiper" 
        :indicator-dots="true" 
        :autoplay="true" 
        :interval="4000" 
        :duration="500"
        indicator-color="rgba(255,255,255,0.4)"
        indicator-active-color="#ffffff"
        circular
      >
        <swiper-item v-for="(banner, index) in bannerList" :key="index">
          <view class="banner-item" :style="{ background: banner.bgGradient }">
            <view class="banner-content">
              <view class="banner-tag">
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

    <!-- 金刚区网格导航 -->
    <view class="nav-grid">
      <view 
        class="nav-item" 
        v-for="(item, index) in navList" 
        :key="index"
        @tap="handleNavClick(item)"
      >
        <view class="nav-icon-wrapper" :style="{ background: item.bgColor }">
          <text class="nav-icon">{{ item.icon }}</text>
        </view>
        <text class="nav-label">{{ item.label }}</text>
      </view>
    </view>

    <!-- 功能卡片区 -->
    <!-- <view class="feature-cards">
      <view 
        class="feature-card" 
        v-for="(card, index) in featureCards" 
        :key="index"
        :style="{ background: card.bgGradient }"
        @tap="handleFeatureClick(card)"
      >
        <view class="card-content">
          <text class="card-title">{{ card.title }}</text>
          <text class="card-desc">{{ card.desc }}</text>
        </view>
        <view class="card-icon-wrapper">
          <text class="card-icon">{{ card.icon }}</text>
        </view>
      </view>
    </view> -->

    <!-- 数字人分类区 -->
    <!-- <view class="category-section">
      <view class="category-tabs">
        <view 
          class="category-tab" 
          v-for="(cat, index) in categories" 
          :key="index"
          :class="{ active: activeCategoryIndex === index }"
          @tap="activeCategoryIndex = index"
        >
          <text class="tab-text">{{ cat }}</text>
        </view>
      </view>

     
      <view class="avatar-grid">
        <view 
          class="avatar-card" 
          v-for="(avatar, index) in avatarList" 
          :key="index"
          @tap="handleAvatarClick(avatar)"
        >
          <image class="avatar-image" :src="avatar.image" mode="aspectFill" />
          <view class="avatar-info" v-if="avatar.name">
            <text class="avatar-name">{{ avatar.name }}</text>
          </view>
        </view>
      </view>
    </view> -->

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { getAgentList, type Agent } from '@/api/agent'

const authStore = useAuthStore()
const projectStore = useProjectStore()

// 金刚区导航数据
const navList = ref<Array<{
  icon: string
  label: string
  bgColor: string
  route?: string
  agentId?: string
  isMore?: boolean
}>>([])

// 加载智能体列表
const loadAgentList = async () => {
  try {
    const response = await getAgentList()
    if (response.code === 200 && response.data?.agents) {
      const agents = response.data.agents
      const maxDisplay = 7 // 最多显示7个

      // 生成背景色数组（循环使用，统一为橙色系）
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

      // 添加"更多"按钮（第8个位置）
      const moreItem = {
        icon: '⭐',
        label: '更多',
        bgColor: 'linear-gradient(135deg, rgba(255, 136, 0, 0.15) 0%, rgba(255, 184, 77, 0.2) 100%)',
        route: '/pages/agent/index',
        isMore: true
      }

      navList.value = [...agentNavItems, moreItem]
    } else {
      // 如果接口失败，使用默认数据
      console.warn('获取智能体列表失败，使用默认数据')
      setDefaultNavList()
    }
  } catch (error) {
    console.error('加载智能体列表失败:', error)
    // 接口失败时使用默认数据
    setDefaultNavList()
  }
}

// 设置默认导航列表（作为fallback）
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

// 分类数据
const categories = reactive(['公共数字人', '商务', '休闲', '运动', '知性', '气质'])
const activeCategoryIndex = ref(0)

// 数字人列表数据
const avatarList = reactive([
  { id: 1, name: '', image: '/static/default-avatar.png', category: '公共数字人' },
  { id: 2, name: '', image: '/static/default-avatar.png', category: '公共数字人' },
  { id: 3, name: '', image: '/static/default-avatar.png', category: '商务' },
  { id: 4, name: '', image: '/static/default-avatar.png', category: '休闲' }
])

// 事件处理
const handleNavClick = async (item: any) => {
  // 登录检查
  // const loggedIn = await authStore.requireLogin()
  // if (!loggedIn) return
  
  console.log('导航点击:', item.label)

  // 如果是"更多"按钮，跳转到智能体列表页面
  if (item.isMore) {
    uni.navigateTo({ url: '/pages/agent/index' })
    return
  }

  // 其他智能体点击，跳转到对应页面
  if (item.route) {
    uni.navigateTo({ url: item.route })
  }
}

const handleFeatureClick = async (card: any) => {
  // 登录检查
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return
  
  console.log('功能卡片点击:', card.title)
  // uni.navigateTo({ url: card.route })
}

const handleAvatarClick = async (avatar: any) => {
  // 登录检查
  const loggedIn = await authStore.requireLogin()
  if (!loggedIn) return
  
  console.log('数字人点击:', avatar.id)
}
</script>

<style lang="scss" scoped>
// CSS变量 - 品牌色（与 ProjectDashboard 保持一致）
$brand-orange: #FF8800;
$brand-orange-alt: #F37021;
$brand-orange-light: rgba(255, 136, 0, 0.1);
$bg-light: #F5F7FA;
.container {
  min-height: 100vh;
  background: $bg-light;
  padding-bottom: 120rpx;
  position: relative;
    overflow: hidden;
  }
  
  // 背景装饰（与 ProjectDashboard 风格一致）
  .bg-decoration {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 500rpx;
    pointer-events: none;
    overflow: hidden;
    z-index: 0;
  
    .deco-circle {
      position: absolute;
      border-radius: 50%;
  
      &.c1 {
        width: 400rpx;
        height: 400rpx;
        background: radial-gradient(circle, rgba(255, 136, 0, 0.08) 0%, transparent 70%);
        top: -150rpx;
        right: -100rpx;
      }
  
      &.c2 {
        width: 300rpx;
        height: 300rpx;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.06) 0%, transparent 70%);
        top: 100rpx;
        left: -80rpx;
      }
    }
}

/* 顶部标题栏 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: #ffffff;
  
  .header-title {
    font-size: 36rpx;
    font-weight: 600;
    color: $brand-orange;
    letter-spacing: 2rpx;
  }
  
  .project-entry {
    display: flex;
    align-items: center;
    gap: 12rpx;
    padding: 12rpx 20rpx;
    background: linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%);
    border-radius: 32rpx;
    
    &:active {
      opacity: 0.8;
    }
    
    .project-avatar {
      width: 40rpx;
      height: 40rpx;
      border-radius: 12rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .avatar-letter {
        font-size: 22rpx;
        font-weight: 600;
        color: #fff;
      }
    }
    
    .project-name {
      font-size: 24rpx;
      font-weight: 500;
      color: $brand-orange;
      max-width: 120rpx;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .project-hint {
      font-size: 24rpx;
      color: #999;
    }
    
    .entry-arrow {
      font-size: 28rpx;
      color: #999;
    }
  }
}

/* Banner 轮播图 */
.banner-wrapper {
  position: relative;
    z-index: 10;
  padding: 24rpx;
  
  .banner-swiper {
    height: 320rpx;
    border-radius: 24rpx;
    overflow: hidden;
    box-shadow: 0 8rpx 32rpx rgba(255, 136, 0, 0.25);
  }
  
  .banner-item {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 32rpx;
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -20%;
      width: 300rpx;
      height: 300rpx;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
    }
  }
  
  .banner-content {
    flex: 1;
    z-index: 1;
  }
  
  .banner-tag {
    margin-bottom: 8rpx;
    
    .tag-text {
      font-size: 20rpx;
      color: rgba(255, 255, 255, 0.85);
      font-weight: 500;
      letter-spacing: 1rpx;
    }
  }
  
  .banner-slogan {
    font-size: 28rpx;
    color: rgba(255, 255, 255, 0.9);
    font-style: italic;
    font-family: 'Georgia', serif;
    margin-bottom: 16rpx;
  }
  
  .banner-main {
    display: flex;
    align-items: center;
    margin-bottom: 12rpx;
    
    .main-text {
      font-size: 40rpx;
      font-weight: 700;
      color: #ffffff;
    }
    
    .main-highlight {
      font-size: 40rpx;
      font-weight: 700;
      color: #ffd700;
      text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.2);
    }
  }
  
  .banner-sub {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .banner-image {
    width: 200rpx;
    height: 240rpx;
    border-radius: 16rpx;
    object-fit: cover;
    z-index: 1;
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.2);
  }
}

/* 金刚区网格导航 */
.nav-grid {
  position: relative;
    z-index: 10;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24rpx 16rpx;
  padding: 32rpx 24rpx;
  background: rgba(255, 255, 255, 0.85);
  margin: 0 24rpx;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
    border: 1rpx solid rgba(255, 255, 255, 0.8);
  
  .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12rpx;
    
    &:active {
      transform: scale(0.95);
      opacity: 0.8;
    }
  }
  
  .nav-icon-wrapper {
    width: 96rpx;
    height: 96rpx;
    border-radius: 24rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
  }
  
  .nav-icon {
    font-size: 44rpx;
  }
  
  .nav-label {
    font-size: 22rpx;
    color: #333333;
    text-align: center;
    font-weight: 500;
    line-height: 1.3;
  }
}

/* 功能卡片区 */
.feature-cards {
  position: relative;
    z-index: 10;
  display: flex;
  gap: 20rpx;
  padding: 32rpx 24rpx;
  
  .feature-card {
    flex: 1;
    height: 160rpx;
    border-radius: 20rpx;
    padding: 24rpx;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.12);
    position: relative;
    overflow: hidden;
    
    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }
    
    &::before {
      content: '';
      position: absolute;
      top: -30%;
      right: -15%;
      width: 150rpx;
      height: 150rpx;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 50%;
    }
  }
  
  .card-content {
    display: flex;
    flex-direction: column;
    gap: 8rpx;
    z-index: 1;
  }
  
  .card-title {
    font-size: 32rpx;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 1rpx;
  }
  
  .card-desc {
    font-size: 22rpx;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .card-icon-wrapper {
    width: 80rpx;
    height: 80rpx;
    background: rgba(255, 255, 255, 0.25);
    border-radius: 16rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
  }
  
  .card-icon {
    font-size: 40rpx;
  }
}

/* 数字人分类区 */
.category-section {
  position: relative;
    z-index: 10;
  padding: 0 24rpx;
  
  .category-tabs {
    display: flex;
    gap: 32rpx;
    padding: 24rpx 0;
    border-bottom: 1rpx solid #f0f0f0;
    overflow-x: auto;
    white-space: nowrap;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }
  
  .category-tab {
    position: relative;
    padding-bottom: 12rpx;
    
    .tab-text {
      font-size: 28rpx;
      color: #999999;
      font-weight: 500;
      transition: all 0.3s ease;
    }
    
    &.active {
      .tab-text {
        color: $brand-orange;
        font-weight: 600;
      }
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 40rpx;
        height: 6rpx;
        background: linear-gradient(90deg, $brand-orange 0%, $brand-orange-alt 100%);
        border-radius: 3rpx;
      }
    }
  }
}

/* 数字人列表 */
.avatar-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
  padding: 24rpx 0;
  
  .avatar-card {
    border-radius: 24rpx;
    overflow: hidden;
    background: #fff;
      box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
    aspect-ratio: 1;
    position: relative;
    
    &:active {
      transform: scale(0.98);
    }
  }
  
  .avatar-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .avatar-info {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16rpx;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));
    
    .avatar-name {
      font-size: 24rpx;
      color: #ffffff;
      font-weight: 500;
    }
  }
}
</style>
