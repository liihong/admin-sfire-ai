<template>
  <view class="founder-message">
    <swiper
      class="founder-swiper"
      :indicator-dots="true"
      :autoplay="true"
      :interval="4200"
      :duration="500"
      indicator-color="rgba(255,255,255,0.3)"
      indicator-active-color="#ffffff"
      circular
    >
      <swiper-item v-for="(item, index) in messageList" :key="index">
        <view class="message-card">
          <view class="message-tag">FOUNDER'S MESSAGE</view>
          <view class="message-title">{{ item.title }}</view>
          <view class="message-desc">{{ item.desc }}</view>
          <view class="message-btn" @tap="handleViewStory">
            <text class="btn-text">查看故事</text>
          </view>
        </view>
      </swiper-item>
    </swiper>
  </view>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const messageList = reactive([
  {
    title: '武峥:火源AI创始人',
    desc: '10年北京代码生涯,回乡做AI,只想帮你每天多省出一杯茶的时间。'
  }
])

const handleViewStory = () => {
  console.log('查看故事')
}
</script>

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.founder-message {
  margin-bottom: $spacing-md;
  padding: 0 $spacing-md;

  .founder-swiper {
    height: 400rpx;
  }

  .message-card {
    position: relative;
    width: 100%;
    height: 100%;
    background: #1A1A2E;
    border-radius: $radius-lg;
    padding: 48rpx 36rpx;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;

    .message-tag {
      font-size: 20rpx;
      color: rgba(255, 255, 255, 0.6);
      letter-spacing: 2rpx;
      text-transform: uppercase;
      margin-bottom: 24rpx;
      font-weight: 400;
    }

    .message-title {
      font-size: 44rpx;
      font-weight: 700;
      color: $white;
      line-height: 1.4;
      margin-bottom: 16rpx;
    }

    .message-desc {
      font-size: 28rpx;
      color: rgba(255, 255, 255, 0.9);
      line-height: 1.6;
      margin-bottom: 32rpx;
    }

    .message-btn {
      align-self: flex-start;
      padding: 10rpx 20rpx;
      background: $white;
      border-radius: 100rpx;
      border: 2rpx solid $white;

      .btn-text {
        font-size: 28rpx;
        font-weight: 600;
        color: #1A1A2E;
      }
    }
  }
}
</style>
