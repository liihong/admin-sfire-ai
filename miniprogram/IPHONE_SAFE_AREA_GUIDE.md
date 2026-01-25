# iPhone 灵动岛适配使用说明

## 📱 概述

本项目已全局适配 iPhone 灵动岛（安全区域），确保所有页面在 iPhone 设备上都能正确显示，避免内容被灵动岛遮挡。

## ✅ 已实现的功能

### 1. 全局工具类

在 `App.vue` 中已添加全局安全区工具类，所有页面可直接使用：

- `.safe-area-top` - 顶部安全区占位（用于自定义导航栏）
- `.safe-area-bottom` - 底部安全区占位（用于底部固定元素）

### 2. SCSS Mixin

在 `styles/_mixins.scss` 中已添加安全区 Mixin，方便在样式中使用：

- `@include safe-area-top-padding` - 顶部安全区内边距
- `@include safe-area-bottom-padding` - 底部安全区内边距

## 🎯 使用方式

### 方式一：使用全局工具类（推荐）

**适用于：自定义导航栏页面**

在自定义导航栏容器的最顶部添加 `<view class="safe-area-top"></view>`：

```vue
<template>
  <view class="page-container">
    <!-- 自定义导航栏 -->
    <view class="custom-nav-bar">
      <!-- ✅ 添加这一行即可适配灵动岛 -->
      <view class="safe-area-top"></view>
      
      <!-- 导航栏内容 -->
      <view class="nav-content">
        <view class="back-btn" @tap="goBack">←</view>
        <text class="nav-title">页面标题</text>
      </view>
    </view>
    
    <!-- 页面内容 -->
    <view class="page-content">
      <!-- 内容 -->
    </view>
  </view>
</template>
```

### 方式二：使用 SCSS Mixin

**适用于：需要在样式中直接添加安全区内边距**

```scss
<style lang="scss" scoped>
@import '@/styles/_mixins.scss';

.custom-nav-bar {
  // ✅ 使用 mixin 自动添加顶部安全区内边距
  @include safe-area-top-padding;
  
  background: #fff;
  padding-bottom: 20rpx;
}

.bottom-fixed-bar {
  // ✅ 使用 mixin 自动添加底部安全区内边距
  @include safe-area-bottom-padding;
  
  position: fixed;
  bottom: 0;
  background: #fff;
}
</style>
```

### 方式三：直接使用 CSS 环境变量

**适用于：需要精确控制安全区域的情况**

```scss
.custom-element {
  // ✅ 直接使用 CSS 环境变量
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
```

## 📋 已适配的页面

以下页面已自动适配 iPhone 灵动岛：

1. ✅ `pages/copywriting/index.vue` - AI 文案生成页
2. ✅ `pages/project/dashboard.vue` - 项目控制台页
3. ✅ `pages/project/components/TopBar.vue` - 顶部导航栏组件
4. ✅ `pages/mine/power-detail.vue` - 算力明细页
5. ✅ `pages/project/create.vue` - 创建项目页

## 🆕 新增页面适配指南

### 对于使用系统导航栏的页面

**无需任何操作**，微信小程序会自动处理安全区域。

### 对于使用自定义导航栏的页面

**只需要在导航栏容器顶部添加一行代码**：

```vue
<view class="nav-bar">
  <!-- ✅ 添加这一行 -->
  <view class="safe-area-top"></view>
  
  <!-- 导航栏内容 -->
  ...
</view>
```

## 🔍 技术原理

1. **CSS 环境变量**：使用 `env(safe-area-inset-top)` 等 CSS 环境变量获取设备安全区域
2. **自动适配**：在非 iPhone 设备上，`env(safe-area-inset-top)` 会自动返回 `0`，无需额外判断
3. **零侵入**：不影响现有页面，只在需要的地方使用

## ⚠️ 注意事项

1. **不要重复添加**：如果导航栏容器已经使用了 `@include safe-area-top-padding`，就不需要再添加 `<view class="safe-area-top"></view>`
2. **固定定位元素**：对于 `position: fixed` 的顶部元素，必须添加安全区适配
3. **底部元素**：底部固定元素（如输入栏、TabBar）也需要适配底部安全区
4. **开发工具中高度为 0**：在微信开发者工具中，`env(safe-area-inset-top)` 可能返回 0，这是正常的。实际 iPhone 设备上会自动获取正确的值

## 🔧 开发工具中高度为 0 的解决方案

### 问题说明

在微信开发者工具中测试时，`.safe-area-top` 的高度可能显示为 0，这是因为：
- 开发工具可能不完全支持 `env()` CSS 环境变量
- 非 iPhone 设备上安全区域本身就是 0

### 解决方案

#### 方案一：使用动态组件（推荐用于开发调试）

如果需要在开发工具中看到效果，可以使用 `SafeAreaTop` 组件：

```vue
<template>
  <view class="nav-bar">
    <!-- 使用动态组件（开发调试用） -->
    <SafeAreaTop />
    
    <!-- 导航栏内容 -->
    ...
  </view>
</template>

<script setup lang="ts">
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'
</script>
```

#### 方案二：添加临时最小高度（仅开发用）

在开发阶段，可以临时添加最小高度用于调试：

```scss
.safe-area-top {
  height: env(safe-area-inset-top);
  min-height: env(safe-area-inset-top);
  /* 开发调试：临时添加最小高度（实际设备上会自动覆盖） */
  min-height: 44px; /* 约等于 iPhone 状态栏高度 */
}
```

**注意**：发布前记得移除临时高度，让实际设备自动适配。

#### 方案三：使用 JS 动态设置（高级用法）

```vue
<template>
  <view class="nav-bar">
    <view 
      class="safe-area-top" 
      :style="{ height: safeAreaTop + 'px' }"
    ></view>
    ...
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const safeAreaTop = ref(0)

onMounted(() => {
  const systemInfo = uni.getSystemInfoSync()
  const safeAreaInsets = systemInfo.safeAreaInsets || {}
  const statusBarHeight = systemInfo.statusBarHeight || 0
  
  // 优先使用安全区域，否则使用状态栏高度
  safeAreaTop.value = safeAreaInsets.top || statusBarHeight || 0
})
</script>
```

### 实际设备测试

**重要**：CSS `env()` 方案在实际 iPhone 设备上会自动生效，无需担心。开发工具中的 0 高度不影响实际使用。

## 📝 示例代码

### 完整示例：自定义导航栏页面

```vue
<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <!-- iPhone 灵动岛安全区适配 -->
      <view class="safe-area-top"></view>
      
      <view class="nav-content">
        <view class="back-btn" @tap="goBack">←</view>
        <text class="nav-title">页面标题</text>
      </view>
    </view>
    
    <!-- 页面内容 -->
    <scroll-view class="content" scroll-y>
      <!-- 内容 -->
    </scroll-view>
    
    <!-- 底部固定输入栏 -->
    <view class="input-bar">
      <!-- 输入框 -->
      <input class="input" placeholder="输入内容" />
      
      <!-- iPhone 底部安全区适配 -->
      <view class="safe-area-bottom"></view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #fff;
  
  .nav-content {
    display: flex;
    align-items: center;
    padding: 20rpx 32rpx;
  }
}

.content {
  height: 100vh;
  padding-top: calc(env(safe-area-inset-top) + 88rpx); // 导航栏高度 + 安全区
}

.input-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 20rpx 32rpx;
}
</style>
```

## 🎉 总结

- ✅ **零侵入**：不影响现有页面
- ✅ **使用简单**：只需添加一行代码
- ✅ **自动适配**：非 iPhone 设备自动兼容
- ✅ **统一管理**：全局工具类统一管理

新增页面时，只需要记住：**自定义导航栏页面添加 `<view class="safe-area-top"></view>` 即可**！

