<template>
  <div class="agent-icon" :style="iconStyle">
    <!-- 如果是图片URL，显示图片 -->
    <img v-if="isImageUrl(icon)" :src="icon" class="icon-img" alt="agent icon" />
    <!-- 否则显示图标组件 -->
    <el-icon v-else :size="iconSize">
      <component :is="getIconComponent(icon)" />
    </el-icon>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  ChatDotRound,
  ChatLineRound,
  ChatLineSquare,
  MagicStick,
  Cpu,
  Connection,
  DataAnalysis,
  Platform,
  Document,
  DocumentCopy,
  Files,
  Notebook,
  Reading,
  Tools,
  Setting,
  Operation,
  Management,
  Monitor,
  User,
  UserFilled,
  Avatar,
  Star,
  EditPen,
  Brush,
  Picture,
  Film,
  ShoppingCart,
  Box,
  Present,
  Trophy,
  Coin,
  DataBoard,
  PieChart,
  Histogram,
  TrendCharts,
  Odometer,
  Cloudy,
  Upload,
  Download,
  Folder,
  FolderOpened,
  Lock,
  Unlock,
  Key,
  Message,
  Phone,
  Cellphone,
  VideoCamera,
  Notification,
  Bell,
  House,
  Search,
  Filter,
  Clock,
  Timer,
  Calendar,
  Flag,
  CollectionTag,
  Sunny,
  Moon,
  InfoFilled,
  WarningFilled,
  SuccessFilled
} from "@element-plus/icons-vue";

interface Props {
  /** 图标名称或图片URL */
  icon?: string;
  /** 图标大小（像素） */
  size?: number;
  /** 是否显示渐变背景 */
  showGradient?: boolean;
  /** 自定义样式 */
  customStyle?: Record<string, any>;
}

const props = withDefaults(defineProps<Props>(), {
  icon: "",
  size: 32,
  showGradient: true,
  customStyle: () => ({})
});

/**
 * 判断是否为图片URL
 * 支持 http/https 链接和相对路径
 */
const isImageUrl = (icon: string): boolean => {
  if (!icon) return false;
  // 检查是否为 URL（http/https/相对路径）或图片格式
  return (
    icon.startsWith("http://") ||
    icon.startsWith("https://") ||
    icon.startsWith("/") ||
    icon.startsWith("data:image/") ||
    /\.(png|jpg|jpeg|gif|svg|webp|ico)$/i.test(icon)
  );
};

/**
 * 获取图标组件
 * 根据图标标识返回对应的 Element Plus 图标组件
 */
const getIconComponent = (iconName: string) => {
  // 如果没有图标名称，使用默认图标
  if (!iconName) {
    return ChatDotRound;
  }

  // Element Plus 图标映射表 - 支持更多图标
  const iconMap: Record<string, any> = {
    // AI/智能类
    ChatDotRound,
    ChatLineRound,
    ChatLineSquare,
    MagicStick,
    Cpu,
    Connection,
    DataAnalysis,
    Platform,
    // 文档类
    Document,
    DocumentCopy,
    Files,
    Notebook,
    Reading,
    // 工具类
    Tools,
    Setting,
    Operation,
    Management,
    Monitor,
    // 用户类
    User,
    UserFilled,
    Avatar,
    // 创意类
    Star,
    EditPen,
    Brush,
    Picture,
    Film,
    // 业务类
    ShoppingCart,
    Box,
    Present,
    Trophy,
    Coin,
    // 数据类
    DataBoard,
    PieChart,
    Histogram,
    TrendCharts,
    Odometer,
    // 云服务类
    Cloudy,
    Upload,
    Download,
    Folder,
    FolderOpened,
    // 安全类
    Lock,
    Unlock,
    Key,
    // 通信类
    Message,
    Phone,
    Cellphone,
    VideoCamera,
    Notification,
    Bell,
    // 常用类
    House,
    Search,
    Filter,
    Clock,
    Timer,
    Calendar,
    Flag,
    CollectionTag,
    Sunny,
    Moon,
    Link: ChatDotRound,
    InfoFilled,
    WarningFilled,
    SuccessFilled,
    // 自定义标识映射（兼容旧数据）
    viral_copy_default: Document, // 文案类
    script_default: ChatDotRound, // 脚本类
    marketing_default: ChatDotRound, // 营销类
    chat: ChatDotRound, // 聊天类
    document: Document, // 文档类
    cpu: Cpu // 计算类
  };

  // 如果在映射表中找到，返回对应图标
  if (iconMap[iconName]) {
    return iconMap[iconName];
  }

  // 默认返回 ChatDotRound
  return ChatDotRound;
};

/**
 * 获取图标渐变背景色
 * 根据图标名称返回对应的渐变色
 */
const getIconGradient = (iconName: string): string => {
  if (!iconName) return "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";

  const gradientMap: Record<string, string> = {
    // AI/智能类 - 紫色、蓝色系
    ChatDotRound: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    ChatLineRound: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    ChatLineSquare: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    MagicStick: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Cpu: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Connection: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    DataAnalysis: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Platform: "linear-gradient(135deg, #434343 0%, #000000 100%)",

    // 文档类 - 蓝色系
    Document: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    DocumentCopy: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Files: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Notebook: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Reading: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",

    // 工具类 - 橙色、深色系
    Tools: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Setting: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    Operation: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Management: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Monitor: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",

    // 创意类 - 金色、彩色系
    Star: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    EditPen: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Brush: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Picture: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Film: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",

    // 业务类 - 橙色、金色系
    ShoppingCart: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Box: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Present: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    Trophy: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    Coin: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",

    // 数据类 - 彩色系
    DataBoard: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    PieChart: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Histogram: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    TrendCharts: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Odometer: "linear-gradient(135deg, #434343 0%, #000000 100%)",

    // 云服务类 - 蓝绿色系
    Cloudy: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Upload: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Download: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Folder: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    FolderOpened: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",

    // 安全类 - 深色、金色系
    Lock: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    Unlock: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Key: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    User: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    UserFilled: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Avatar: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",

    // 通信类 - 彩色系
    Message: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Phone: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    Cellphone: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    VideoCamera: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    Notification: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    Bell: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",

    // 常用类 - 各种颜色
    House: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Search: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    Filter: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    Clock: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    Timer: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Calendar: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    Flag: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    CollectionTag: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    Sunny: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
    Moon: "linear-gradient(135deg, #434343 0%, #000000 100%)",
    InfoFilled: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
    WarningFilled: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    SuccessFilled: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
  };

  return gradientMap[iconName] || "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";
};

// 计算图标大小
const iconSize = computed(() => props.size);

// 计算图标样式
const iconStyle = computed(() => {
  const baseStyle: Record<string, any> = {
    width: `${props.size}px`,
    height: `${props.size}px`,
    ...props.customStyle
  };

  // 如果是图片URL，不设置背景；否则根据 showGradient 设置渐变背景
  if (!isImageUrl(props.icon) && props.showGradient) {
    baseStyle.background = getIconGradient(props.icon);
  } else if (isImageUrl(props.icon)) {
    baseStyle.background = "none";
  }

  return baseStyle;
});
</script>

<style scoped lang="scss">
.agent-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: white;
  padding: 10px;

  .icon-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 12px;
  }
}
</style>

