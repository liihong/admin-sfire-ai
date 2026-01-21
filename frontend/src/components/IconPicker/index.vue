<template>
  <div class="icon-picker">
    <el-input v-model="selectedIcon" placeholder="请选择图标" readonly @click="dialogVisible = true">
      <template #suffix>
        <div class="icon-preview" v-if="selectedIcon">
          <el-icon :size="20">
            <component :is="getIconComponent(selectedIcon)" />
          </el-icon>
        </div>
        <el-icon v-else :size="16">
          <ArrowDown />
        </el-icon>
      </template>
    </el-input>

    <el-dialog v-model="dialogVisible" title="选择图标" width="800px" :close-on-click-modal="false">
      <div class="icon-picker-content">
        <!-- 分类标签 -->
        <el-tabs v-model="activeCategory" type="card">
          <el-tab-pane v-for="category in iconCategories" :key="category.name" :label="category.label" :name="category.name">
            <div class="icon-grid">
              <div
                v-for="icon in category.icons"
                :key="icon.name"
                class="icon-item"
                :class="{ active: selectedIcon === icon.name }"
                @click="handleSelectIcon(icon)"
              >
                <div class="icon-wrapper" :style="{ background: icon.gradient }">
                  <el-icon :size="24">
                    <component :is="icon.component" />
                  </el-icon>
                </div>
                <div class="icon-name">{{ icon.label }}</div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import {
  ArrowDown,
  // 通信类
  ChatDotRound,
  ChatLineRound,
  ChatLineSquare,
  Message,
  Phone,
  Cellphone,
  VideoCamera,
  // 文档类
  Document,
  DocumentCopy,
  Files,
  Notebook,
  Reading,
  DataAnalysis,
  // 工具类
  Tools,
  Setting,
  Operation,
  Management,
  Monitor,
  // AI/智能类
  Cpu,
  MagicStick,
  Connection,
  Link,
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
  // 数据类
  DataBoard,
  PieChart,
  Histogram,
  TrendCharts,
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
  // 开发类
  Coin,
  // 搜索类
  Search,
  Filter,
  // 时间类
  Clock,
  Timer,
  Calendar,
  // 标记类
  Flag,
  CollectionTag,
  // 其他常用
  House,
  Link as LinkIcon,
  Notification,
  Bell,
  Platform,
  Sunny,
  Moon,
  Odometer,
  InfoFilled,
  WarningFilled,
  SuccessFilled
} from "@element-plus/icons-vue";

interface IconItem {
  name: string;
  label: string;
  component: any;
  gradient: string;
}

interface Props {
  modelValue: string;
}

interface Emits {
  (e: "update:modelValue", value: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const dialogVisible = ref(false);
const selectedIcon = ref(props.modelValue || "");
const tempIcon = ref<IconItem | null>(null);
const activeCategory = ref("ai");

// 定义渐变色方案
const gradients = {
  purple: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  blue: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  green: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  orange: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  red: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  cyan: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)",
  dark: "linear-gradient(135deg, #434343 0%, #000000 100%)",
  gold: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)"
};

// 图标分类
const iconCategories = ref([
  {
    name: "ai",
    label: "AI/智能",
    icons: [
      { name: "ChatDotRound", label: "对话", component: ChatDotRound, gradient: gradients.purple },
      { name: "ChatLineRound", label: "聊天", component: ChatLineRound, gradient: gradients.blue },
      { name: "MagicStick", label: "魔法", component: MagicStick, gradient: gradients.purple },
      { name: "Cpu", label: "处理器", component: Cpu, gradient: gradients.cyan },
      { name: "Connection", label: "连接", component: Connection, gradient: gradients.blue },
      { name: "DataAnalysis", label: "分析", component: DataAnalysis, gradient: gradients.green },
      { name: "Platform", label: "平台", component: Platform, gradient: gradients.dark }
    ] as IconItem[]
  },
  {
    name: "document",
    label: "文档/办公",
    icons: [
      { name: "Document", label: "文档", component: Document, gradient: gradients.blue },
      { name: "DocumentCopy", label: "复制", component: DocumentCopy, gradient: gradients.cyan },
      { name: "Files", label: "文件", component: Files, gradient: gradients.blue },
      { name: "Notebook", label: "笔记本", component: Notebook, gradient: gradients.purple },
      { name: "Reading", label: "阅读", component: Reading, gradient: gradients.orange }
    ] as IconItem[]
  },
  {
    name: "tool",
    label: "工具/设置",
    icons: [
      { name: "Tools", label: "工具", component: Tools, gradient: gradients.orange },
      { name: "Setting", label: "设置", component: Setting, gradient: gradients.dark },
      { name: "Operation", label: "操作", component: Operation, gradient: gradients.blue },
      { name: "Management", label: "管理", component: Management, gradient: gradients.purple },
      { name: "Monitor", label: "监控", component: Monitor, gradient: gradients.cyan }
    ] as IconItem[]
  },
  {
    name: "creative",
    label: "创意/媒体",
    icons: [
      { name: "Star", label: "星星", component: Star, gradient: gradients.gold },
      { name: "EditPen", label: "编辑", component: EditPen, gradient: gradients.blue },
      { name: "Brush", label: "画笔", component: Brush, gradient: gradients.purple },
      { name: "Picture", label: "图片", component: Picture, gradient: gradients.orange },
      { name: "Film", label: "视频", component: Film, gradient: gradients.red }
    ] as IconItem[]
  },
  {
    name: "business",
    label: "业务/电商",
    icons: [
      { name: "ShoppingCart", label: "购物车", component: ShoppingCart, gradient: gradients.orange },
      { name: "Box", label: "盒子", component: Box, gradient: gradients.blue },
      { name: "Present", label: "礼物", component: Present, gradient: gradients.red },
      { name: "Trophy", label: "奖杯", component: Trophy, gradient: gradients.gold },
      { name: "Coin", label: "金币", component: Coin, gradient: gradients.orange }
    ] as IconItem[]
  },
  {
    name: "data",
    label: "数据/图表",
    icons: [
      { name: "DataBoard", label: "数据板", component: DataBoard, gradient: gradients.blue },
      { name: "PieChart", label: "饼图", component: PieChart, gradient: gradients.purple },
      { name: "Histogram", label: "柱状图", component: Histogram, gradient: gradients.cyan },
      { name: "TrendCharts", label: "趋势图", component: TrendCharts, gradient: gradients.green },
      { name: "Odometer", label: "仪表盘", component: Odometer, gradient: gradients.dark }
    ] as IconItem[]
  },
  {
    name: "cloud",
    label: "云端/文件",
    icons: [
      { name: "Cloudy", label: "云", component: Cloudy, gradient: gradients.cyan },
      { name: "Upload", label: "上传", component: Upload, gradient: gradients.green },
      { name: "Download", label: "下载", component: Download, gradient: gradients.blue },
      { name: "Folder", label: "文件夹", component: Folder, gradient: gradients.orange },
      { name: "FolderOpened", label: "打开文件夹", component: FolderOpened, gradient: gradients.blue }
    ] as IconItem[]
  },
  {
    name: "security",
    label: "安全/权限",
    icons: [
      { name: "Lock", label: "锁定", component: Lock, gradient: gradients.dark },
      { name: "Unlock", label: "解锁", component: Unlock, gradient: gradients.green },
      { name: "Key", label: "密钥", component: Key, gradient: gradients.gold },
      { name: "User", label: "用户", component: User, gradient: gradients.purple }
    ] as IconItem[]
  },
  {
    name: "communication",
    label: "通信/消息",
    icons: [
      { name: "Message", label: "消息", component: Message, gradient: gradients.blue },
      { name: "Phone", label: "电话", component: Phone, gradient: gradients.green },
      { name: "Cellphone", label: "手机", component: Cellphone, gradient: gradients.cyan },
      { name: "VideoCamera", label: "视频", component: VideoCamera, gradient: gradients.purple },
      { name: "ChatLineSquare", label: "聊天框", component: ChatLineSquare, gradient: gradients.blue },
      { name: "Notification", label: "通知", component: Notification, gradient: gradients.red },
      { name: "Bell", label: "铃铛", component: Bell, gradient: gradients.gold }
    ] as IconItem[]
  },
  {
    name: "common",
    label: "常用图标",
    icons: [
      { name: "House", label: "主页", component: House, gradient: gradients.blue },
      { name: "Search", label: "搜索", component: Search, gradient: gradients.cyan },
      { name: "Filter", label: "筛选", component: Filter, gradient: gradients.blue },
      { name: "Clock", label: "时钟", component: Clock, gradient: gradients.dark },
      { name: "Timer", label: "计时器", component: Timer, gradient: gradients.orange },
      { name: "Calendar", label: "日历", component: Calendar, gradient: gradients.red },
      { name: "Flag", label: "旗帜", component: Flag, gradient: gradients.gold },
      { name: "CollectionTag", label: "收藏", component: CollectionTag, gradient: gradients.orange },
      { name: "Sunny", label: "晴天", component: Sunny, gradient: gradients.gold },
      { name: "Moon", label: "月亮", component: Moon, gradient: gradients.dark },
      { name: "LinkIcon", label: "链接", component: LinkIcon, gradient: gradients.blue },
      { name: "Avatar", label: "头像", component: Avatar, gradient: gradients.purple },
      { name: "UserFilled", label: "用户填充", component: UserFilled, gradient: gradients.blue },
      { name: "InfoFilled", label: "信息", component: InfoFilled, gradient: gradients.cyan },
      { name: "WarningFilled", label: "警告", component: WarningFilled, gradient: gradients.orange },
      { name: "SuccessFilled", label: "成功", component: SuccessFilled, gradient: gradients.green }
    ] as IconItem[]
  }
]);

// 获取图标组件
const getIconComponent = (iconName: string) => {
  for (const category of iconCategories.value) {
    const icon = category.icons.find(i => i.name === iconName);
    if (icon) return icon.component;
  }
  return ChatDotRound;
};

// 选择图标
const handleSelectIcon = (icon: IconItem) => {
  tempIcon.value = icon;
  selectedIcon.value = icon.name;
};

// 确认选择
const handleConfirm = () => {
  if (selectedIcon.value) {
    emit("update:modelValue", selectedIcon.value);
  }
  dialogVisible.value = false;
};

// 监听外部值变化
watch(
  () => props.modelValue,
  newVal => {
    selectedIcon.value = newVal || "";
  }
);
</script>

<style scoped lang="scss">
.icon-picker {
  width: 100%;

  :deep(.el-input__wrapper) {
    cursor: pointer;

    .el-input__inner {
      cursor: pointer;
    }
  }

  .icon-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 6px;
    color: white;
  }
}

.icon-picker-content {
  .icon-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 16px;
    padding: 16px 0;
    max-height: 400px;
    overflow-y: auto;

    .icon-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 12px;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s;
      border: 2px solid transparent;

      &:hover {
        background: var(--el-fill-color-light);
        transform: translateY(-2px);
      }

      &.active {
        border-color: var(--el-color-primary);
        background: var(--el-color-primary-light-9);
      }

      .icon-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .icon-name {
        font-size: 12px;
        color: var(--el-text-color-regular);
        text-align: center;
      }
    }
  }
}
</style>
