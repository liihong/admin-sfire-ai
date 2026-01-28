<template>
  <view class="page-container">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="user-info">
        <view class="avatar-container">
          <view class="avatar-wrapper" @tap="handleAvatarClick">
            <image 
              class="avatar" 
              :src="userInfo.avatar || '/static/default-avatar.png'" 
              mode="aspectFill"
            />
            <!-- 皇冠图标 -->
            <view class="crown-badge" v-if="userInfo.partnerStatus && userInfo.partnerStatus !== '普通用户'">
             <text class="crown-text">V</text>
            </view>
          </view>
          <text class="phone-number">{{ displayPhone }}</text>
          <view class="tags-row">
            <text class="vip-tag" v-if="userInfo.partnerStatus && userInfo.partnerStatus !== '普通用户'">
              {{ userInfo.partnerStatus === 'VIP会员' ? 'VIP' : 'PRO' }} 用户
            </text>
            <text class="expire-tag" v-if="userInfo.expireDate">
              {{ userInfo.expireDate }} 过期
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 会员升级卡片 -->
    <view class="upgrade-card" v-if="userInfo.partnerStatus === '普通用户' || !userInfo.partnerStatus">
      <view class="upgrade-content">
        <view class="upgrade-text">
          <text class="upgrade-subtitle">UPGRADE PRIORITY</text>
          <text class="upgrade-title">开通 更高等级会员</text>
         <text class="upgrade-desc">解锁更多IP席位和无限智能体</text>
        </view>
        <view class="upgrade-btn" @tap="goToMembership">
          <text class="upgrade-btn-text">立即开通</text>
        </view>
      </view>
    </view>

    <!-- 我的算力卡片 -->
    <view class="stat-card">
      <view class="stat-header">
        <view class="stat-title-wrapper">
          <SvgIcon name="suanli" size="32" color="#F37021" />
          <text class="stat-title">我的算力</text>
        </view>
        <text class="stat-link" @tap="goToPowerDetail">算力明细 ›</text>
      </view>
      <view class="stat-content">
        <view class="stat-value-row">
          <text class="stat-number">{{ formatNumber(userInfo.power) }}</text>
          <text class="stat-unit">算力点</text>
        </view>
        <view class="stat-action">
          <view class="recharge-btn" @tap="goToRecharge">
            <text class="recharge-btn-text">充值</text>
          </view>
        </view>
      </view>
    </view>

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
            <SvgIcon :name="item.icon" size="30" color="#FFFFFF" />
          </view>
          <view class="menu-text-wrapper">
            <text class="menu-name">{{ item.name }}</text>
            <text class="menu-desc" v-if="item.desc">{{ item.desc }}</text>
          </view>
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
import SvgIcon from '@/components/base/SvgIcon.vue'

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

// 格式化数字（添加千分位）
const formatNumber = (num: string | number): string => {
  const numStr = String(num || '0')
  return numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 功能菜单列表
const menuList = ref([
  {
    id: 'inspiration',
    name: '我的灵感',
    desc: '保存的草稿与Prompt',
    icon: 'linggan',
    iconBg: '#F37021', // 橙色背景
    path: '/pages/inspiration/index'
  },
  {
    id: 'contact',
    name: '联系客服',
    desc: '反馈建议或寻求帮助',
    icon: 'service',
    iconBg: '#10B981', // 绿色背景
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

// 跳转到算力明细列表
const goToPowerDetail = () => {
  uni.navigateTo({
    url: '/pages/mine/power/detail'
  })
}

// 跳转到充值页面
const goToRecharge = () => {
  uni.navigateTo({
    url: '/pages/mine/power/recharge'
  })
}

// 跳转到开通会员页面
const goToMembership = () => {
  uni.navigateTo({
    url: '/pages/mine/membership'
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

<style scoped lang="scss">
@import '@/styles/_variables.scss';

.page-container {
  min-height: 100vh;
  background: $white;
  padding: 0;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

/* 用户信息卡片 */
.user-card {
  // background: #1a1a2ea1;
    background-color: rgba(255, 247, 237, 0.5);
  padding: 48rpx 32rpx 40rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.avatar-wrapper {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: #F2F3F5;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  margin-bottom: 32rpx;
  border: 2rpx solid #E5E7EB;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.crown-badge {
  position: absolute;
  bottom: -4rpx;
  right: -4rpx;
  width: 48rpx;
  height: 48rpx;
  background: $primary-orange;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx solid $white;
  box-shadow: 0 2rpx 8rpx rgba(243, 112, 33, 0.3);
}

.crown-text {
  font-size: 24rpx;
  color: $white;
  font-weight: 700;
  line-height: 1;
}

.phone-number {
  font-size: 48rpx;
  font-weight: 700;
  color: #1D2129;
  margin-bottom: 16rpx;
  line-height: 1.2;
}

.tags-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  justify-content: center;
}

.vip-tag {
  font-size: 24rpx;
  color: $primary-orange;
  font-weight: 600;
}

.expire-tag {
  font-size: 24rpx;
  color: #86909C;
  font-weight: 500;
}

/* 会员升级卡片 */
.upgrade-card {
  background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
  border-radius: 24rpx;
  padding: 32rpx;
  margin: 0 24rpx 24rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.1);
}

.upgrade-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.upgrade-text {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
}

.upgrade-subtitle {
  font-size: 20rpx;
  color: $primary-orange;
  font-weight: 700;
  letter-spacing: 1rpx;
  text-transform: uppercase;
}

.upgrade-title {
  font-size: 40rpx;
  color: $white;
  font-weight: 700;
  line-height: 1.3;
  margin: 8rpx 0;
}

.upgrade-desc {
  font-size: 24rpx;
  color: #86909C;
  line-height: 1.4;
}

.upgrade-btn {
  padding: 0 32rpx;
  height: 64rpx;
  background: $primary-orange;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upgrade-btn-text {
  font-size: 28rpx;
  color: $white;
  font-weight: 600;
}

.upgrade-btn:active {
  opacity: 0.9;
  transform: scale(0.98);
}

/* 算力卡片 */
.stat-card {
  background: $white;
  border-radius: 24rpx;
  padding: 32rpx;
  margin: 0 24rpx 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.stat-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.stat-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1D2129;
}

.stat-link {
  font-size: 26rpx;
  color: #86909C;
  font-weight: 500;
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24rpx;
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  flex: 1;
}

.stat-number {
  font-size: 64rpx;
  font-weight: 700;
  color: #1D2129;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
  line-height: 1;
  letter-spacing: -1rpx;
}

.stat-unit {
  font-size: 28rpx;
  color: #1D2129;
  font-weight: 500;
}

.stat-action {
  flex-shrink: 0;
}

.recharge-btn {
  height: 64rpx;
  padding: 0 32rpx;
  background: $primary-orange;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.recharge-btn-text {
  font-size: 28rpx;
  color: $white;
  font-weight: 600;
}

.recharge-btn:active {
  opacity: 0.9;
  transform: scale(0.98);
}

/* 功能菜单卡片 */
.menu-card {
  background: $white;
  border-radius: 24rpx;
  overflow: hidden;
  margin: 0 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
}

.menu-item-border {
  border-bottom: 1rpx solid #F2F3F5;
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
}

.menu-icon-wrapper {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-text-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #1D2129;
  line-height: 1.4;
}

.menu-desc {
  font-size: 24rpx;
  color: #86909C;
  line-height: 1.4;
}

.menu-arrow {
  font-size: 32rpx;
  color: #C9CDD4;
  font-weight: 300;
  flex-shrink: 0;
}

.menu-item:active {
  background: #F7F8FA;
}
</style>

