<template>
  <view class="page-container">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="user-info">
        <view class="avatar-wrapper" @tap="handleAvatarClick">
          <image 
            class="avatar" 
            :src="userInfo.avatar || '/static/default-avatar.png'" 
            mode="aspectFill"
          />
        </view>
        <view class="user-details">
          <text class="phone-number">{{ displayPhone }}</text>
          <view class="tags-row">
            <view class="vip-tag" v-if="userInfo.partnerStatus === 'VIP会员'">
              <text class="vip-text">VIP会员</text>
            </view>
            <view class="expire-tag" v-if="userInfo.expireDate">
              <text class="expire-text">{{ userInfo.expireDate }}过期</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 我的算力卡片 -->
    <view class="stat-card">
      <view class="stat-header">
        <text class="stat-title">我的算力</text>
        <text class="stat-link" @tap="goToDetail('power')">算力明细 ›</text>
      </view>
      <view class="stat-value-row">
        <text class="stat-number">{{ userInfo.power }}</text>
        <text class="stat-unit">算力</text>
      </view>
    </view>

    <!-- 合伙人卡片 -->
    <!-- <view class="partner-card">
      <view class="stat-header">
        <text class="stat-title">合伙人 - {{ userInfo.partnerStatus }}</text>
        <text class="stat-link" @tap="goToDetail('asset')">资产明细 ›</text>
      </view>
      <view class="stat-value-row">
        <text class="stat-number">{{ userInfo.balance }}</text>
        <text class="stat-unit">元</text>
      </view>
      <view class="action-buttons">
        <view class="btn-primary" @tap="handleWithdraw">
          <text class="btn-text-primary">申请提现</text>
        </view>
        <view class="btn-outline" @tap="handleInvite">
          <text class="btn-text-outline">邀请好友</text>
        </view>
      </view>
    </view> -->

    <!-- 功能列表 -->
    <view class="menu-card">
      <view 
        v-for="(item, index) in menuList" 
        :key="index" 
        class="menu-item"
        :class="{ 'menu-item-border': index < menuList.length - 1 }"
        @tap="handleMenuClick(item)"
      >
        <view class="menu-left">
          <view class="menu-icon-wrapper" :style="{ background: item.iconBg }">
            <text class="menu-icon">{{ item.icon }}</text>
          </view>
          <text class="menu-name">{{ item.name }}</text>
        </view>
        <text class="menu-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getUserInfo, updateUserInfo } from '@/api/user'
import { useAuthStore } from '@/stores/auth'

// 用户信息
const userInfo = reactive({
  avatar: '',
  phone: '',
  expireDate: '',
  power: '0',
  balance: '0.00',
  partnerStatus: '普通用户'
})

// 格式化手机号（隐藏中间4位）
const formatPhone = (phone: string): string => {
  if (!phone) return ''
  // 如果手机号长度不是11位，直接返回
  if (phone.length !== 11) return phone
  // 将中间4位替换为****
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

// 格式化后的手机号（计算属性）
const displayPhone = computed(() => formatPhone(userInfo.phone))

// 功能菜单列表
const menuList = ref([
  {
    id: 'contact',
    name: '联系客服',
    icon: '💬',
    iconBg: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
    path: '/pages/contact/index'
  }
])

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await getUserInfo()
    // 后端返回格式: {code: 200, data: {...}, msg: "..."}
    if (response.code === 200 && response.data) {
      const data = response.data
      
      userInfo.avatar = data.avatar || ''
      userInfo.phone = data.phone || ''
      userInfo.expireDate = data.expireDate || ''
      userInfo.power = data.power || '0'
      userInfo.balance = data.partnerBalance || '0.00'
      userInfo.partnerStatus = data.partnerStatus || '普通用户'
    } else {
      console.error('获取用户信息失败:', (response as any).msg)
      uni.showToast({
        title: (response as any).msg || '获取用户信息失败',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('获取用户信息异常:', error)
    uni.showToast({
      title: '获取用户信息失败',
      icon: 'none'
    })
  }
}

// 头像点击 - 获取微信头像和昵称
const handleAvatarClick = () => {
  // #ifdef MP-WEIXIN
  // 微信小程序环境，使用 getUserProfile 获取用户信息
  uni.getUserProfile({
    desc: '用于完善用户资料',
    success: async (res) => {
      console.log('获取用户信息成功:', res.userInfo)
      const { avatarUrl, nickName } = res.userInfo
      
      // 调用接口更新用户信息
      try {
        const updateResponse = await updateUserInfo({
          avatar: avatarUrl,
          nickname: nickName
        })
        
        // 后端返回格式: {code: 200, data: {...}, msg: "..."}
        if (updateResponse.code === 200) {
          uni.showToast({
            title: '更新成功',
            icon: 'success'
          })
          // 刷新用户信息
          await fetchUserInfo()
        } else {
          uni.showToast({
            title: (updateResponse as any).msg || '更新失败',
            icon: 'none'
          })
        }
      } catch (error) {
        console.error('更新用户信息异常:', error)
        uni.showToast({
          title: '更新失败',
          icon: 'none'
        })
      }
    },
    fail: (err) => {
      console.error('获取用户信息失败:', err)
      if (err.errMsg && err.errMsg.includes('deny')) {
        uni.showToast({
          title: '需要授权才能使用此功能',
          icon: 'none'
        })
      } else {
        uni.showToast({
          title: '获取用户信息失败',
          icon: 'none'
        })
      }
    }
  })
  // #endif
  
  // #ifndef MP-WEIXIN
  // 非微信小程序环境，提示用户手动输入
  uni.showToast({
    title: '请在小程序中打开',
    icon: 'none'
  })
  // #endif
}

// 跳转到明细页面
const goToDetail = (type: string) => {
  if (type === 'power') {
    uni.navigateTo({
      url: '/pages/mine/power-detail'
    })
  } else {
    uni.showToast({
      title: '查看资产明细',
      icon: 'none'
    })
  }
}

// 申请提现
const handleWithdraw = () => {
  uni.showToast({
    title: '申请提现功能开发中',
    icon: 'none'
  })
}

// 邀请好友
const handleInvite = () => {
  uni.showToast({
    title: '邀请好友功能开发中',
    icon: 'none'
  })
}

// 菜单点击
const handleMenuClick = (item: any) => {
  if (item.path) {
    uni.navigateTo({
      url: item.path
    })
  } else {
    uni.showToast({
      title: `进入${item.name}`,
      icon: 'none'
    })
  }
}

// 页面显示时获取用户信息
onShow(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f5ff 0%, #f5f7fa 100%);
  padding: 24rpx;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

/* 用户信息卡片 */
.user-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.avatar-wrapper {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.phone-number {
  font-size: 40rpx;
  font-weight: 700;
  color: #1f2937;
}

.tags-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.vip-tag {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
}

.vip-text {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 600;
}

.expire-tag {
  border: 2rpx solid #3b82f6;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  background: rgba(59, 130, 246, 0.05);
}

.expire-text {
  font-size: 24rpx;
  color: #3b82f6;
  font-weight: 500;
}

/* 统计卡片通用样式 */
.stat-card,
.partner-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.stat-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2937;
}

.stat-link {
  font-size: 26rpx;
  color: #3b82f6;
  font-weight: 500;
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.stat-number {
  font-size: 64rpx;
  font-weight: 700;
  color: #f59e0b;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

.stat-unit {
  font-size: 28rpx;
  color: #6b7280;
  font-weight: 500;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 24rpx;
  margin-top: 32rpx;
}

.btn-primary {
  flex: 1;
  height: 88rpx;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(59, 130, 246, 0.35);
}

.btn-text-primary {
  font-size: 30rpx;
  color: #ffffff;
  font-weight: 600;
}

.btn-outline {
  flex: 1;
  height: 88rpx;
  background: #ffffff;
  border: 2rpx solid #3b82f6;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-text-outline {
  font-size: 30rpx;
  color: #3b82f6;
  font-weight: 600;
}

/* 功能菜单卡片 */
.menu-card {
  background: #ffffff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 24rpx rgba(99, 102, 241, 0.08);
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
}

.menu-item-border {
  border-bottom: 1rpx solid #f3f4f6;
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.menu-icon-wrapper {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-icon {
  font-size: 36rpx;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #1f2937;
}

.menu-arrow {
  font-size: 36rpx;
  color: #9ca3af;
  font-weight: 300;
}

/* 按钮点击效果 */
.btn-primary:active {
  opacity: 0.9;
  transform: scale(0.98);
}

.btn-outline:active {
  background: rgba(59, 130, 246, 0.05);
}

.menu-item:active {
  background: #f9fafb;
}
</style>

