<template>
  <view class="package-card" :class="{ 'is-popular': package.is_popular }" @tap="handleClick">
    <!-- 主推标签 -->
    <view class="popular-badge" v-if="package.is_popular">
      <text class="popular-text">🏆 爆款推荐</text>
    </view>
    
    <!-- 套餐内容 -->
    <view class="package-content">
      <view class="package-header">
        <text class="package-name">{{ package.name }}</text>
        <view class="package-tags" v-if="package.tag && package.tag.length > 0">
          <view 
            class="tag-item" 
            v-for="(tag, index) in package.tag" 
            :key="index"
            :class="{ 'tag-popular': tag.includes('最划算') || tag.includes('80%') }"
          >
            {{ tag }}
          </view>
        </view>
      </view>
      
      <view class="package-price-row">
        <text class="price-symbol">¥</text>
        <text class="price-value">{{ package.price }}</text>
      </view>
      
      <view class="package-power-row">
        <text class="power-value">{{ formatPower(package.power_amount) }}</text>
        <text class="power-unit">算力</text>
      </view>
      
      <view class="package-unit-price" v-if="package.unit_price">
        实际单价：{{ package.unit_price }}
      </view>
      
      <view class="package-article-count" v-if="package.article_count">
        约可生成 {{ package.article_count }} 篇高质量爆款文案
      </view>
      
      <view class="package-description" v-if="package.description">
        {{ package.description }}
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { Package } from '@/api/recharge'

const props = defineProps<{
  package: Package
}>()

const emit = defineEmits<{
  click: [package: Package]
}>()

// 格式化算力数量（添加千分位）
function formatPower(power: number): string {
  return power.toLocaleString('zh-CN')
}

// 点击处理
function handleClick() {
  emit('click', props.package)
}
</script>

<style lang="scss" scoped>
.package-card {
  position: relative;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  border: 2rpx solid transparent;
  transition: all 0.3s;

  &.is-popular {
    border-color: #f97316;
    background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%);
    box-shadow: 0 4rpx 20rpx rgba(249, 115, 22, 0.15);
  }

  &:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
}

.popular-badge {
  position: absolute;
  top: -12rpx;
  right: 32rpx;
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.3);
}

.popular-text {
  font-size: 22rpx;
  color: #ffffff;
  font-weight: 600;
}

.package-content {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.package-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.package-name {
  font-size: 36rpx;
  font-weight: 700;
  color: #1f2937;
}

.package-tags {
  display: flex;
  gap: 8rpx;
  flex-wrap: wrap;
}

.tag-item {
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
  background: #f3f4f6;
  color: #6b7280;

  &.tag-popular {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    color: #f59e0b;
    font-weight: 600;
  }
}

.package-price-row {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
  margin-top: 8rpx;
}

.price-symbol {
  font-size: 28rpx;
  font-weight: 600;
  color: #f59e0b;
}

.price-value {
  font-size: 48rpx;
  font-weight: 700;
  color: #f59e0b;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.package-power-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  margin-top: 4rpx;
}

.power-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #3b82f6;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.power-unit {
  font-size: 24rpx;
  color: #6b7280;
  font-weight: 500;
}

.package-unit-price {
  font-size: 24rpx;
  color: #9ca3af;
  margin-top: 4rpx;
}

.package-article-count {
  font-size: 24rpx;
  color: #6b7280;
  margin-top: 8rpx;
  padding: 12rpx;
  background: #f9fafb;
  border-radius: 12rpx;
}

.package-description {
  font-size: 24rpx;
  color: #9ca3af;
  margin-top: 8rpx;
  line-height: 1.5;
}
</style>


