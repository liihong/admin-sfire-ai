<template>
  <view class="agent-icon" :style="{ background: getIconGradient(iconName) }">
    <!-- 如果是图片URL，显示图片 -->
    <image v-if="isImageUrl(iconName)" :src="iconName" class="icon-image" mode="aspectFit" />
    <!-- 否则使用 uview 图标 -->
    <u-icon v-else :name="getUviewIconName(iconName)" color="#ffffff" :size="48"></u-icon>
  </view>
</template>

<script setup lang="ts">
interface Props {
  iconName: string
  size?: number
}

const props = withDefaults(defineProps<Props>(), {
  iconName: '',
  size: 56
})

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
 */
const getUviewIconName = (iconName: string): string => {
  const iconMap: Record<string, string> = {
    // AI/智能类
    ChatDotRound: 'chat',
    ChatLineRound: 'chat',
    ChatLineSquare: 'chat',
    MagicStick: 'star',
    Cpu: 'cpu',
    Connection: 'link',
    DataAnalysis: 'chart',
    Platform: 'grid',

    // 文档类
    Document: 'file-text',
    DocumentCopy: 'file-text',
    Files: 'folder',
    Notebook: 'bookmark',
    Reading: 'book-open',

    // 工具类
    Tools: 'setting',
    Setting: 'setting',
    Operation: 'gear',
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
    Film: 'film',

    // 业务类
    ShoppingCart: 'shopping-cart',
    Box: 'box',
    Present: 'gift',
    Trophy: 'award',
    Coin: 'currency-circle',

    // 数据类
    DataBoard: 'chart',
    PieChart: 'pie-chart',
    Histogram: 'bar-chart',
    TrendCharts: 'chart',
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
    Message: 'message',
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

  return iconMap[iconName] || 'chat'
}

/**
 * 获取图标渐变背景色
 */
const getIconGradient = (iconName: string): string => {
  if (!iconName) return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

  const gradientMap: Record<string, string> = {
    // AI/智能类 - 紫色、蓝色系
    ChatDotRound: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    ChatLineRound: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    ChatLineSquare: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    MagicStick: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Cpu: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    Connection: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    DataAnalysis: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    Platform: 'linear-gradient(135deg, #434343 0%, #000000 100%)',

    // 文档类 - 蓝色系
    Document: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    DocumentCopy: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
    Files: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Notebook: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Reading: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',

    // 工具类 - 橙色、深色系
    Tools: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Setting: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
    Operation: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Management: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Monitor: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',

    // 创意类 - 金色、彩色系
    Star: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',
    EditPen: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    Brush: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    Picture: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    Film: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',

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
    TrendCharts: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
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
    User: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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
  width: 112rpx;
  height: 112rpx;
  border-radius: 24rpx;
  color: white;
  flex-shrink: 0;

  .icon-image {
    width: 100%;
    height: 100%;
    border-radius: 24rpx;
  }
}
</style>
