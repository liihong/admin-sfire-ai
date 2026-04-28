<template>
 <!-- <view class="agent-icon" :style="{ width: size + 'rpx', height: size + 'rpx', borderRadius: size * 0.21 + 'rpx', background: getIconGradient(iconName) }"> -->

  <view class="agent-icon">
    <!-- 如果是图片URL，显示图片 -->
    <image v-if="isImageUrl(iconName)" :src="iconName" class="icon-image" mode="aspectFit" />
    <!-- 否则使用 uview 图标 -->
   <u-icon v-else-if="getUviewIconName(iconName)" :name="getUviewIconName(iconName)" color="#ffffff"
      :size="size"></u-icon>
    <!-- 回退显示首字母 -->
    <text v-else class="icon-fallback">{{ getFallbackText(iconName) }}</text>
  </view>
</template>

<script setup lang="ts">
interface Props {
  iconName: string
  size?: number
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  iconName: '',
  size: 20,
  color: '#ffffff'
})

// 解构 props，方便在模板中直接使用
const { iconName, size } = props

/**
 * 判断是否为图片URL
 */
const isImageUrl = (icon: string): boolean => {
  if (!icon) return false
  return (
    icon.startsWith('http://') ||
    icon.startsWith('https://') ||
    icon.startsWith('/') ||
    icon.startsWith('data:image/') ||
    /\.(png|jpg|jpeg|gif|svg|webp|ico)$/i.test(icon)
  )
}

/**
 * Element Plus 图标名称映射到 uview 图标名称
 * 注意：
 * 1. 如果 iconName 在映射表中，使用映射后的名称（用于 Element Plus 图标名称兼容）
 * 2. 如果 iconName 不在映射表中，直接使用 iconName（支持直接使用 uview-plus 的图标名称）
 */
const getUviewIconName = (iconName: string): string => {
  // Element Plus 图标名称到 uview-plus 图标名称的映射表
  const iconMap: Record<string, string> = {
    // AI/智能类 - 使用 message 图标
    ChatDotRound: 'chat',
    ChatLineRound: 'chat',
    ChatLineSquare: 'chat',
    MagicStick: 'star',
    Cpu: 'cpu',
    Connection: 'link',
    DataAnalysis: 'bar-chart',
    Platform: 'grid',

    // 文档类
    Document: 'file-text',
    DocumentCopy: 'file-text',
    Files: 'folder',
    Notebook: 'bookmark',
    Reading: 'list-dot',

    // 工具类 - 注意：Tools 在 uview-plus 中直接支持，所以不映射
    Setting: 'setting',
    Operation: 'setting',
    Management: 'setting',
    Monitor: 'desktop',

    // 用户类
    User: 'account',
    UserFilled: 'account',
    Avatar: 'account-circle',

    // 创意类
    Star: 'star',
    EditPen: 'edit-pen',
    Brush: 'edit-pen',
    Picture: 'image',
    Film: 'share',

    // 业务类
    ShoppingCart: 'shopping-cart',
    Box: 'box',
    Present: 'gift',
    Trophy: 'award',
    Coin: 'currency-circle',

    // 数据类
    DataBoard: 'bar-chart',
    PieChart: 'pie-chart',
    Histogram: 'bar-chart',
    TrendCharts: 'order',
    Odometer: 'speedometer',

    // 云服务类
    Cloudy: 'cloud',
    Upload: 'arrow-up',
    Download: 'arrow-down',
    Folder: 'folder',
    FolderOpened: 'folder-open',

    // 安全类
    Lock: 'lock',
    Unlock: 'unlock',
    Key: 'key',
    Account: 'account',

    // 通信类
    Message: 'chat',
    Phone: 'phone',
    Cellphone: 'phone',
    VideoCamera: 'camera',
    Notification: 'bell',
    Bell: 'bell',

    // 常用类
    House: 'home',
    Search: 'search',
    Filter: 'filter',
    Clock: 'clock',
    Timer: 'clock',
    Calendar: 'calendar',
    Flag: 'flag',
    CollectionTag: 'bookmark',
    Sunny: 'sun',
    Moon: 'moon',
    LinkIcon: 'link',
    Acircle: 'account-circle',
    InfoFilled: 'info-circle',
    WarningFilled: 'warning',
    SuccessFilled: 'checkmark-circle'
  }

  // 如果 iconName 在映射表中，返回映射后的名称
  // 如果不在映射表中，直接返回 iconName（支持直接使用 uview-plus 的图标名称）
  return iconMap[iconName] || iconName
}

/**
 * 计算图标大小
 * 根据容器大小动态计算，确保图标大小合适
 */
const getIconSize = (): number => {
  // 图标大小应该是容器大小的 50-60%，确保图标清晰可见
  const calculatedSize = size * 0.55
  // 最小尺寸为 20rpx，最大尺寸为 80rpx
  return Math.max(20, Math.min(80, calculatedSize))
}

/**
 * 获取回退文本（显示图标名称的首字母）
 */
const getFallbackText = (iconName: string): string => {
  if (!iconName) return '?'
  // 取首字母或首字符
  const firstChar = iconName.charAt(0).toUpperCase()
  // 如果是中文，返回中文
  if (/[\u4e00-\u9fa5]/.test(iconName)) {
    return iconName.substring(0, 2)
  }
  return firstChar
}

/**
 * 获取图标渐变背景色
 */
const getIconGradient = (iconName: string): string => {
  if (!iconName) return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

  const gradientMap: Record<string, string> = {
    // AI/智能类 - 紫色、蓝色系
    ChatDotRound: 'linear-gradient(135deg, #A18CD1 0%, #FBC2EB 100%)',
    ChatLineRound: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    ChatLineSquare: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    MagicStick: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Cpu: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    Connection: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    DataAnalysis: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    Platform: 'linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%)',

    // 文档类 - 蓝色系
    Document: 'linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%)',
    DocumentCopy: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    Files: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Notebook: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Reading: 'linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%)',

    // 工具类 - 橙色、深色系
    Tools: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Setting: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
    Operation: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Management: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Monitor: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',

    // 创意类 - 金色、彩色系
    Star: 'linear-gradient(135deg, #FF9966 0%, #FF5E62 100%)',
    EditPen: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Brush: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Picture: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Film: 'linear-gradient(135deg, #F5576C 0%, #F093FB 100%)',

    // 业务类 - 橙色、金色系
    ShoppingCart: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Box: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Present: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    Trophy: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',
    Coin: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',

    // 数据类 - 彩色系
    DataBoard: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    PieChart: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Histogram: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    TrendCharts: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    Odometer: 'linear-gradient(135deg, #434343 0%, #000000 100%)',

    // 云服务类 - 蓝绿色系
    Cloudy: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    Upload: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    Download: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Folder: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    FolderOpened: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',

    // 安全类 - 深色、金色系
    Lock: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
    Unlock: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    Key: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',
    User: 'linear-gradient(135deg, #FA8BFF 0%, #2BD2FF 52%, #2BFF88 100%)',
    UserFilled: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Avatar: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',

    // 通信类 - 彩色系
    Message: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Phone: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    Cellphone: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    VideoCamera: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Notification: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    Bell: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',

    // 常用类 - 各种颜色
    House: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Search: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    Filter: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Clock: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
    Timer: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Calendar: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    Flag: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',
    CollectionTag: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Sunny: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',
    Moon: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
    InfoFilled: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    WarningFilled: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    SuccessFilled: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  }

  return gradientMap[iconName] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
}
</script>

<style scoped lang="scss">
.agent-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .icon-image {
    width: 100%;
    height: 100%;
    border-radius: inherit;
  }

  .icon-fallback {
    font-size: 32rpx;
    font-weight: 600;
    color: #ffffff;
    text-align: center;
  }
}
</style>
