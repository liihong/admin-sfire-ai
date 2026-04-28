<template>
  <view class="agreement-page">
    <SafeAreaTop />
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-title">用户协议</view>
      <view class="header-placeholder"></view>
    </view>

    <!-- 协议内容 -->
    <scroll-view class="agreement-content" scroll-y>
      <view class="agreement-container">
        <!-- 标题 -->
        <view class="agreement-title">火源灵感火花用户服务协议</view>
        
        <!-- 更新日期 -->
        <view class="agreement-date">生效日期：2026年1月1日</view>

        <!-- 协议正文 -->
        <view class="agreement-body">
          <!-- 第一条 -->
          <view class="agreement-section">
            <view class="section-title">第一条 协议的接受</view>
            <view class="section-content">
              <text class="paragraph">欢迎使用火源灵感火花（以下简称"本平台"或"我们"）。本协议是您与火源AI之间关于使用本平台服务的法律协议。</text>
              <text class="paragraph">请您在使用本平台服务前，仔细阅读本协议的全部内容。当您点击"同意"或开始使用本平台服务时，即表示您已充分理解并同意接受本协议的全部内容。如果您不同意本协议的任何内容，请立即停止使用本平台服务。</text>
            </view>
          </view>

          <!-- 第二条 -->
          <view class="agreement-section">
            <view class="section-title">第二条 服务说明</view>
            <view class="section-content">
              <text class="paragraph">2.1 本平台是一个AI驱动的智能创作平台，为用户提供包括但不限于：IP定位、文案生成、灵感收集、智能对话等服务（以下简称"本服务"）。</text>
              <text class="paragraph">2.2 本平台有权根据业务发展需要，调整、变更或终止部分或全部服务内容，并会提前通过合理方式通知用户。</text>
              <text class="paragraph">2.3 本平台保留在任何时候自行决定对服务或其任何部分进行升级、修改、暂停或终止的权利。</text>
            </view>
          </view>

          <!-- 第三条 -->
          <view class="agreement-section">
            <view class="section-title">第三条 账户注册与使用</view>
            <view class="section-content">
              <text class="paragraph">3.1 您在使用本平台服务前，需要通过微信授权登录的方式注册账户。您应当使用真实、准确、完整的信息进行注册。</text>
              <text class="paragraph">3.2 您有责任妥善保管您的账户信息及密码，并对您账户下的所有行为负责。如发现账户被盗用或存在安全漏洞，应立即通知本平台。</text>
              <text class="paragraph">3.3 您不得将账户转让、出售、出租或以其他方式提供给第三方使用。</text>
              <text class="paragraph">3.4 本平台有权对违反本协议的用户账户采取限制、暂停或终止服务的措施。</text>
            </view>
          </view>

          <!-- 第四条 -->
          <view class="agreement-section">
            <view class="section-title">第四条 用户行为规范</view>
            <view class="section-content">
              <text class="paragraph">4.1 您在使用本平台服务时，应当遵守相关法律法规，不得利用本平台从事违法违规活动。</text>
              <text class="paragraph">4.2 您不得发布、传播或存储以下内容：</text>
              <text class="paragraph indent">（1）违反国家法律法规、危害国家安全、破坏社会稳定的内容；</text>
              <text class="paragraph indent">（2）侵犯他人知识产权、肖像权、隐私权等合法权益的内容；</text>
              <text class="paragraph indent">（3）含有色情、暴力、赌博、恐怖主义等不良信息的内容；</text>
              <text class="paragraph indent">（4）虚假、误导性信息或商业广告；</text>
              <text class="paragraph indent">（5）其他违反公序良俗的内容。</text>
              <text class="paragraph">4.3 您不得利用本平台服务进行以下行为：</text>
              <text class="paragraph indent">（1）干扰、破坏本平台的正常运行；</text>
              <text class="paragraph indent">（2）未经授权访问、修改、删除本平台的数据；</text>
              <text class="paragraph indent">（3）使用自动化工具批量操作或恶意刷量；</text>
              <text class="paragraph indent">（4）其他损害本平台或其他用户合法权益的行为。</text>
            </view>
          </view>

          <!-- 第五条 -->
          <view class="agreement-section">
            <view class="section-title">第五条 知识产权</view>
            <view class="section-content">
              <text class="paragraph">5.1 本平台的所有知识产权，包括但不限于商标、专利、著作权、商业秘密等，均归本平台所有。</text>
              <text class="paragraph">5.2 您通过本平台生成的内容，其知识产权归您所有。但您授予本平台在全球范围内、免费、非独占的使用许可，用于提供和改进本服务。</text>
              <text class="paragraph">5.3 您不得未经授权使用本平台的商标、标识、域名等知识产权。</text>
              <text class="paragraph">5.4 如您认为本平台的内容侵犯了您的知识产权，请及时联系我们，我们将依法处理。</text>
            </view>
          </view>

          <!-- 第六条 -->
          <view class="agreement-section">
            <view class="section-title">第六条 费用与支付</view>
            <view class="section-content">
              <text class="paragraph">6.1 本平台的部分服务可能需要付费使用，具体收费标准以平台公示为准。</text>
              <text class="paragraph">6.2 您可以通过微信支付等方式购买算力包、会员服务等。支付成功后，费用不予退还，除非法律法规另有规定。</text>
              <text class="paragraph">6.3 本平台有权根据业务需要调整收费标准，调整后的收费标准将在平台公示后生效。</text>
              <text class="paragraph">6.4 您应当确保支付账户有足够的余额或信用额度，因支付失败导致的损失由您自行承担。</text>
            </view>
          </view>

          <!-- 第七条 -->
          <view class="agreement-section">
            <view class="section-title">第七条 隐私保护</view>
            <view class="section-content">
              <text class="paragraph">7.1 本平台高度重视用户隐私保护，我们将按照《隐私政策》的规定收集、使用、存储和保护您的个人信息。</text>
              <text class="paragraph">7.2 您在使用本平台服务时，我们可能会收集您的设备信息、使用记录、位置信息等，用于提供和改进服务。</text>
              <text class="paragraph">7.3 未经您同意，我们不会向第三方披露您的个人信息，法律法规另有规定的除外。</text>
              <text class="paragraph">7.4 您有权查询、更正、删除您的个人信息，具体操作方式请参考《隐私政策》。</text>
            </view>
          </view>

          <!-- 第八条 -->
          <view class="agreement-section">
            <view class="section-title">第八条 免责声明</view>
            <view class="section-content">
              <text class="paragraph">8.1 本平台提供的服务基于现有技术和条件，我们努力确保服务的稳定性和安全性，但不保证服务不会中断或出错。</text>
              <text class="paragraph">8.2 对于因不可抗力、网络故障、系统维护等原因导致的服务中断或数据丢失，本平台不承担责任。</text>
              <text class="paragraph">8.3 本平台不对您使用本服务产生的任何直接、间接、偶然、特殊或后果性损失承担责任。</text>
              <text class="paragraph">8.4 本平台生成的内容仅供参考，不构成任何法律、财务、医疗等专业建议。您应当自行判断内容的准确性。</text>
            </view>
          </view>

          <!-- 第九条 -->
          <view class="agreement-section">
            <view class="section-title">第九条 服务变更与终止</view>
            <view class="section-content">
              <text class="paragraph">9.1 本平台有权根据业务发展需要，随时变更、中断或终止部分或全部服务，无需事先通知用户。</text>
              <text class="paragraph">9.2 如您违反本协议，本平台有权立即终止向您提供服务，并保留追究法律责任的权利。</text>
              <text class="paragraph">9.3 服务终止后，本平台有权删除您的账户信息及相关数据，法律法规另有规定的除外。</text>
            </view>
          </view>

          <!-- 第十条 -->
          <view class="agreement-section">
            <view class="section-title">第十条 协议修改</view>
            <view class="section-content">
              <text class="paragraph">10.1 本平台有权根据法律法规变化和业务发展需要，随时修改本协议。</text>
              <text class="paragraph">10.2 协议修改后，我们将在平台显著位置公示修改内容。如您继续使用本服务，视为您已接受修改后的协议。</text>
              <text class="paragraph">10.3 如您不同意修改后的协议，应当停止使用本平台服务。</text>
            </view>
          </view>

          <!-- 第十一条 -->
          <view class="agreement-section">
            <view class="section-title">第十一条 法律适用与争议解决</view>
            <view class="section-content">
              <text class="paragraph">11.1 本协议的订立、生效、解释、履行和争议解决均适用中华人民共和国大陆地区法律法规。</text>
              <text class="paragraph">11.2 如因本协议产生任何争议，双方应友好协商解决；协商不成的，任何一方均可向本平台所在地有管辖权的人民法院提起诉讼。</text>
            </view>
          </view>

          <!-- 第十二条 -->
          <view class="agreement-section">
            <view class="section-title">第十二条 其他</view>
            <view class="section-content">
              <text class="paragraph">12.1 如本协议的任何条款被认定为无效或不可执行，不影响其他条款的效力。</text>
              <text class="paragraph">12.2 本协议构成您与本平台之间关于使用本服务的完整协议，取代您与本平台之间此前就同一事项达成的任何口头或书面协议。</text>
              <text class="paragraph">12.3 本平台保留对本协议的最终解释权。</text>
            </view>
          </view>

          <!-- 联系方式 -->
          <view class="contact-section">
            <view class="contact-title">联系我们</view>
            <view class="contact-content">
              <text class="paragraph">如您对本协议有任何疑问、意见或建议，欢迎通过以下方式联系我们：</text>
              <text class="paragraph">客服邮箱：support@sfire.ai</text>
              <text class="paragraph">客服电话：400-XXX-XXXX</text>
              <text class="paragraph">服务时间：工作日 9:00-18:00</text>
            </view>
          </view>

          <!-- 底部占位 -->
          <view class="bottom-spacer"></view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import SafeAreaTop from '@/components/common/SafeAreaTop.vue'

/**
 * 返回上一页
 */
const goBack = () => {
  uni.navigateBack({
    delta: 1
  })
}
</script>

<style lang="scss" scoped>
@import '@/styles/_variables.scss';
@import '@/styles/_mixins.scss';

.agreement-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  @include flex-column;
}

// 顶部导航栏
.page-header {
  height: 88rpx;
  background: #ffffff;
  border-bottom: 1rpx solid #e5e7eb;
  @include flex-center-vertical;
  justify-content: space-between;
  padding: 0 32rpx;
  z-index: 100;
  padding-top: var(--safe-area-inset-top, 0);
}

.header-back {
  width: 60rpx;
  height: 60rpx;
  @include flex-center;
  cursor: pointer;
}

.back-icon {
  font-size: 40rpx;
  color: $text-primary;
  font-weight: 500;
}

.header-title {
  flex: 1;
  text-align: center;
  font-size: $font-size-lg;
  font-weight: 600;
  color: $text-primary;
}

.header-placeholder {
  width: 60rpx;
}

// 协议内容区域
.agreement-content {
  flex: 1;
  padding-top: 40rpx;
}

.agreement-container {
  max-width: 100%;
  padding: 0 32rpx 40rpx;
}

// 标题
.agreement-title {
  font-size: 48rpx;
  font-weight: 700;
  color: $text-primary;
  text-align: center;
  margin-bottom: 24rpx;
  line-height: 1.4;
}

// 日期
.agreement-date {
  font-size: $font-size-sm;
  color: $text-muted;
  text-align: center;
  margin-bottom: 48rpx;
}

// 协议正文
.agreement-body {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 48rpx 32rpx;
  box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.04);
}

// 章节
.agreement-section {
  margin-bottom: 48rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 24rpx;
  line-height: 1.5;
}

.section-content {
  @include flex-column;
  gap: 16rpx;
}

.paragraph {
  font-size: $font-size-md;
  color: $text-secondary;
  line-height: 1.8;
  display: block;
  text-align: justify;
}

.paragraph.indent {
  padding-left: 32rpx;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 16rpx;
    top: 12rpx;
    width: 6rpx;
    height: 6rpx;
    background: $text-secondary;
    border-radius: 50%;
  }
}

// 联系方式
.contact-section {
  margin-top: 48rpx;
  padding-top: 48rpx;
  border-top: 1rpx solid #e5e7eb;
}

.contact-title {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 24rpx;
}

.contact-content {
  @include flex-column;
  gap: 16rpx;
}

// 底部占位
.bottom-spacer {
  height: 80rpx;
}
</style>

