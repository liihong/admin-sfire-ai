# 小程序图标系统 - uview-plus 集成说明

## ✅ 已完成的工作

### 1. 安装依赖
```bash
npm install uview-plus
```

### 2. 配置文件修改

#### main.ts
- 导入并注册 uview-plus

#### pages.json
- 添加 easycom 配置，自动引入 uview 组件

#### App.vue
- 导入 uview-plus 样式

### 3. AgentIcon 组件
使用 uview-plus 的 `<u-icon>` 组件显示图标

## 📝 图标映射

### 映射表
Element Plus 图标名称 → uview 图标名称

示例：
- `ChatDotRound` → `chat` 💬
- `Document` → `file-text` 📄
- `Setting` → `setting` ⚙️
- `User` → `account` 👤

### 完整映射表
位于 `AgentIcon.vue` 的 `getUviewIconName` 函数中

## 🎨 渐变背景

每个图标都有对应的渐变背景色，与管理端保持一致

## 🔄 使用方式

```vue
<template>
  <AgentIcon iconName="ChatDotRound" />
  <AgentIcon iconName="Document" />
  <AgentIcon iconName="https://example.com/icon.png" />
</template>
```

## 📌 注意事项

1. **uview-plus 图标库**
   - 包含 600+ 图标
   - 按需引入，自动加载
   - 支持自定义颜色和大小

2. **兼容性**
   - 支持图片 URL
   - 自动识别图标类型
   - 向下兼容旧数据

3. **扩展性**
   - 需要新图标时，在 `iconMap` 中添加映射即可
   - 保持 Element Plus 图标名称不变

## 🚀 优势

1. **代码量少**：只需维护一个映射对象
2. **体积小**：按需加载，不用的图标不会打包
3. **维护简单**：uview-plus 持续维护，不需要自己管理图标
4. **效果统一**：与管理端图标风格保持一致
