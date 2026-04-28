<template>
  <view class="privacy-page">
    <SafeAreaTop />
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-title">隐私政策</view>
      <view class="header-placeholder"></view>
    </view>

    <!-- 隐私政策内容 -->
    <scroll-view class="privacy-content" scroll-y>
      <view class="privacy-container">
        <!-- 标题 -->
        <view class="privacy-title">火源灵感火花隐私政策</view>
        
        <!-- 更新日期 -->
        <view class="privacy-date">生效日期：2026年1月1日</view>

        <!-- 政策正文 -->
        <view class="privacy-body">
          <!-- 引言 -->
          <view class="privacy-section">
            <view class="section-content">
              <text class="paragraph">火源灵感火花（以下简称"本平台"或"我们"）深知个人信息对您的重要性，我们将严格遵守相关法律法规，采取相应的安全保护措施，保护您的个人信息安全可控。</text>
              <text class="paragraph">本隐私政策将帮助您了解我们如何收集、使用、存储、传输、共享、转让、公开披露您的个人信息，以及我们为您提供的访问、更新、删除和保护这些信息的方式。</text>
              <text class="paragraph">请您在使用本平台服务前，仔细阅读并充分理解本隐私政策。如您对本隐私政策有任何疑问、意见或建议，可通过本隐私政策提供的联系方式与我们联系。</text>
            </view>
          </view>

          <!-- 第一条 -->
          <view class="privacy-section">
            <view class="section-title">第一条 我们收集的信息</view>
            <view class="section-content">
              <text class="paragraph">为了向您提供更好的服务，我们可能会收集、使用和储存下列与您有关的信息。如果您不提供相关信息，可能无法享受我们提供的某些服务，或者无法达到相关服务拟达到的效果。</text>
              
              <text class="sub-title">1.1 您主动提供的信息</text>
              <text class="paragraph indent">（1）账户信息：当您通过微信授权登录时，我们会收集您的微信昵称、头像、openid等信息；</text>
              <text class="paragraph indent">（2）个人资料：当您完善个人资料时，我们会收集您填写的昵称、头像、个人简介等信息；</text>
              <text class="paragraph indent">（3）联系方式：当您联系客服时，我们会收集您提供的手机号码、邮箱地址等信息；</text>
              <text class="paragraph indent">（4）内容信息：您在使用本平台服务时生成、上传、发布的内容，包括但不限于文本、图片、视频等。</text>

              <text class="sub-title">1.2 我们自动收集的信息</text>
              <text class="paragraph indent">（1）设备信息：包括设备型号、操作系统版本、设备标识符（如IMEI、IDFA等）、设备MAC地址、软件版本号等；</text>
              <text class="paragraph indent">（2）日志信息：包括您使用本平台服务的时间、访问的页面、点击的链接、搜索查询词、IP地址、浏览器类型、语言设置等；</text>
              <text class="paragraph indent">（3）位置信息：当您使用基于位置的服务时，我们可能会收集和处理有关您实际位置的信息（如GPS信号、Wi-Fi接入点、基站信息等）；</text>
              <text class="paragraph indent">（4）使用信息：包括您使用本平台服务的频率、时长、功能偏好、操作记录等。</text>

              <text class="sub-title">1.3 第三方提供的信息</text>
              <text class="paragraph indent">（1）微信平台：当您使用微信登录时，我们会从微信平台获取您的微信账号信息；</text>
              <text class="paragraph indent">（2）支付服务商：当您使用支付功能时，我们会从支付服务商获取交易信息；</text>
              <text class="paragraph indent">（3）其他合作伙伴：我们可能会从合作伙伴处获取您的相关信息。</text>
            </view>
          </view>

          <!-- 第二条 -->
          <view class="privacy-section">
            <view class="section-title">第二条 我们如何使用信息</view>
            <view class="section-content">
              <text class="paragraph">我们严格遵守法律法规的规定及与用户的约定，将收集的信息用于以下用途：</text>
              <text class="paragraph indent">（1）向您提供服务：包括账户注册、身份验证、内容生成、数据存储、客户服务等；</text>
              <text class="paragraph indent">（2）改善和优化服务：分析用户使用习惯，优化产品功能，提升用户体验；</text>
              <text class="paragraph indent">（3）安全保障：检测、预防、调查欺诈、滥用、安全风险和技术问题；</text>
              <text class="paragraph indent">（4）个性化推荐：根据您的使用偏好，向您推荐相关内容和功能；</text>
              <text class="paragraph indent">（5）营销推广：在获得您同意的情况下，向您发送营销信息、促销活动通知等；</text>
              <text class="paragraph indent">（6）履行法定义务：遵守法律法规、法院命令或其他法律程序的要求；</text>
              <text class="paragraph indent">（7）其他用途：在收集信息时已告知您的其他用途，或获得您授权的其他用途。</text>
            </view>
          </view>

          <!-- 第三条 -->
          <view class="privacy-section">
            <view class="section-title">第三条 信息的存储</view>
            <view class="section-content">
              <text class="paragraph">3.1 存储地点：您的个人信息将被存储在中华人民共和国境内。如需跨境传输，我们将严格按照法律法规要求执行。</text>
              <text class="paragraph">3.2 存储期限：我们仅在为实现本隐私政策所述目的所必需的期间内保留您的个人信息，除非法律法规另有规定。当您的个人信息超出保留期限后，我们将删除或匿名化处理您的个人信息。</text>
              <text class="paragraph">3.3 存储安全：我们采用行业标准的安全防护措施，包括但不限于数据加密、访问控制、安全审计等，以防止您的个人信息遭到未经授权的访问、使用、修改、泄露或破坏。</text>
            </view>
          </view>

          <!-- 第四条 -->
          <view class="privacy-section">
            <view class="section-title">第四条 信息的共享、转让、公开披露</view>
            <view class="section-content">
              <text class="sub-title">4.1 共享</text>
              <text class="paragraph">我们不会向第三方共享您的个人信息，除非：</text>
              <text class="paragraph indent">（1）获得您的明确同意；</text>
              <text class="paragraph indent">（2）法律法规规定或司法机关、行政机关依法要求提供的；</text>
              <text class="paragraph indent">（3）与我们的关联公司共享：我们可能会与我们的关联公司共享您的个人信息，但我们只会共享必要的个人信息，且受本隐私政策约束；</text>
              <text class="paragraph indent">（4）与授权合作伙伴共享：我们可能会与授权合作伙伴共享您的信息，以提供更好的服务和体验。我们仅会出于合法、正当、必要、特定、明确的目的共享您的个人信息，并且只会共享提供服务所必要的个人信息。</text>

              <text class="sub-title">4.2 转让</text>
              <text class="paragraph">我们不会将您的个人信息转让给任何公司、组织和个人，除非：</text>
              <text class="paragraph indent">（1）获得您的明确同意；</text>
              <text class="paragraph indent">（2）在涉及合并、收购或破产清算时，如涉及到个人信息转让，我们会要求新的持有您个人信息的公司、组织继续受本隐私政策的约束，否则我们将要求该公司、组织重新向您征求授权同意。</text>

              <text class="sub-title">4.3 公开披露</text>
              <text class="paragraph">我们仅会在以下情况下，公开披露您的个人信息：</text>
              <text class="paragraph indent">（1）获得您的明确同意；</text>
              <text class="paragraph indent">（2）基于法律的披露：在法律、法律程序、诉讼或政府主管部门强制性要求的情况下，我们可能会公开披露您的个人信息。</text>
            </view>
          </view>

          <!-- 第五条 -->
          <view class="privacy-section">
            <view class="section-title">第五条 Cookie和同类技术</view>
            <view class="section-content">
              <text class="paragraph">5.1 我们使用Cookie和同类技术来改善您的用户体验、分析服务使用情况、优化广告效果。</text>
              <text class="paragraph">5.2 Cookie是网站或应用程序存储在您设备上的小型文本文件。我们使用Cookie来记住您的偏好设置、登录状态等。</text>
              <text class="paragraph">5.3 您可以通过浏览器设置拒绝或管理Cookie，但这可能会影响您使用本平台的部分功能。</text>
            </view>
          </view>

          <!-- 第六条 -->
          <view class="privacy-section">
            <view class="section-title">第六条 您的权利</view>
            <view class="section-content">
              <text class="paragraph">按照中国相关的法律、法规、标准，以及其他国家、地区的通行做法，我们保障您对自己的个人信息行使以下权利：</text>
              <text class="paragraph indent">（1）访问权：您有权访问您的个人信息，法律法规规定的例外情况除外；</text>
              <text class="paragraph indent">（2）更正权：当您发现我们处理的关于您的个人信息有错误时，您有权要求我们做出更正；</text>
              <text class="paragraph indent">（3）删除权：在以下情形中，您可以向我们提出删除个人信息的请求：</text>
              <text class="paragraph indent-double">• 我们处理个人信息的行为违反法律法规；</text>
              <text class="paragraph indent-double">• 我们收集、使用您的个人信息，却未征得您的同意；</text>
              <text class="paragraph indent-double">• 我们处理个人信息的行为违反了与您的约定；</text>
              <text class="paragraph indent-double">• 您不再使用我们的产品或服务，或您注销了账号；</text>
              <text class="paragraph indent-double">• 我们不再为您提供产品或服务。</text>
              <text class="paragraph indent">（4）撤回同意权：您可以随时撤回您此前给予我们的授权同意；</text>
              <text class="paragraph indent">（5）注销权：您可以随时注销您的账户，注销后我们将删除您的个人信息，法律法规另有规定的除外；</text>
              <text class="paragraph indent">（6）获取副本权：您有权获取您的个人信息副本；</text>
              <text class="paragraph indent">（7）拒绝权：您可以拒绝我们基于个性化推荐目的处理您的个人信息。</text>
              <text class="paragraph">您可以通过本隐私政策提供的联系方式向我们提出上述权利请求，我们将在15个工作日内回复您的请求。</text>
            </view>
          </view>

          <!-- 第七条 -->
          <view class="privacy-section">
            <view class="section-title">第七条 未成年人保护</view>
            <view class="section-content">
              <text class="paragraph">7.1 我们非常重视对未成年人个人信息的保护。如果您是18周岁以下的未成年人，建议您请您的父母或监护人仔细阅读本隐私政策，并在征得您的父母或监护人同意的前提下使用我们的服务或向我们提供信息。</text>
              <text class="paragraph">7.2 对于经父母或监护人同意使用我们的产品或服务而收集未成年人个人信息的情况，我们只会在法律法规允许、父母或监护人明确同意或者保护未成年人所必要的情况下使用、共享、转让或披露此信息。</text>
              <text class="paragraph">7.3 如果我们发现自己在未事先获得可证实的父母或监护人同意的情况下收集了未成年人的个人信息，我们会设法尽快删除相关数据。</text>
            </view>
          </view>

          <!-- 第八条 -->
          <view class="privacy-section">
            <view class="section-title">第八条 信息安全</view>
            <view class="section-content">
              <text class="paragraph">8.1 我们采用行业标准的安全技术和程序，建立完善的管理制度来保护您的个人信息，防止您的个人信息遭到未经授权的访问、使用、修改、泄露或破坏。</text>
              <text class="paragraph">8.2 我们采取的安全措施包括但不限于：</text>
              <text class="paragraph indent">（1）数据加密传输：我们使用HTTPS等加密技术确保数据传输安全；</text>
              <text class="paragraph indent">（2）数据加密存储：我们对敏感信息进行加密存储；</text>
              <text class="paragraph indent">（3）访问控制：我们严格限制访问个人信息的人员范围，要求他们遵守保密义务；</text>
              <text class="paragraph indent">（4）安全审计：我们定期进行安全审计，及时发现和修复安全漏洞；</text>
              <text class="paragraph indent">（5）安全事件响应：我们建立了安全事件应急响应机制，及时处理安全事件。</text>
              <text class="paragraph">8.3 尽管我们已经采取了合理有效的安全措施，并遵守了相关法律法规要求的标准，但请您理解，由于技术的限制以及可能存在的各种恶意手段，在互联网行业，即便竭尽所能加强安全措施，也不可能始终保证信息百分之百的安全。</text>
              <text class="paragraph">8.4 如发生个人信息安全事件，我们将按照法律法规的要求，及时向您告知：安全事件的基本情况和可能的影响、我们已采取或将要采取的处置措施、您可自主防范和降低风险的建议、对您的补救措施等。我们将及时以邮件、信函、电话、推送通知等方式告知您相关情况，难以逐一告知个人信息主体时，我们会采取合理、有效的方式发布公告。</text>
            </view>
          </view>

          <!-- 第九条 -->
          <view class="privacy-section">
            <view class="section-title">第九条 第三方服务</view>
            <view class="section-content">
              <text class="paragraph">9.1 我们的服务可能包含或链接至第三方提供的社交媒体或其他服务（包括网站）。例如：</text>
              <text class="paragraph indent">（1）您利用"分享"键将某些内容分享到微信等第三方服务；</text>
              <text class="paragraph indent">（2）我们通过广告或我们服务的其他方式向您提供链接，使您可以接入第三方的服务或网站。</text>
              <text class="paragraph">9.2 这些第三方社交媒体或其他服务由相关的第三方负责运营。您使用这些第三方服务（包括您向这些第三方提供的任何个人信息），须受第三方自己的服务条款及隐私政策（而非本隐私政策）约束，您需要仔细阅读其条款。本隐私政策仅适用于我们所收集的信息，并不适用于任何第三方提供的服务或第三方的信息使用规则，我们对任何第三方使用由您提供的信息不承担任何责任。</text>
            </view>
          </view>

          <!-- 第十条 -->
          <view class="privacy-section">
            <view class="section-title">第十条 隐私政策的更新</view>
            <view class="section-content">
              <text class="paragraph">10.1 我们的隐私政策可能变更。未经您明确同意，我们不会削减您按照本隐私政策所应享有的权利。</text>
              <text class="paragraph">10.2 我们会在本页面上发布对本隐私政策所做的任何变更。对于重大变更，我们还会提供更为显著的通知（包括对于某些服务，我们会通过电子邮件发送通知，说明隐私政策的具体变更内容）。</text>
              <text class="paragraph">10.3 本隐私政策所指的重大变更包括但不限于：</text>
              <text class="paragraph indent">（1）我们的服务模式发生重大变化。如处理个人信息的目的、处理的个人信息类型、个人信息的使用方式等；</text>
              <text class="paragraph indent">（2）我们在所有权结构、组织架构等方面发生重大变化。如业务调整、破产并购等引起的所有者变更等；</text>
              <text class="paragraph indent">（3）个人信息共享、转让或公开披露的主要对象发生变化；</text>
              <text class="paragraph indent">（4）您参与个人信息处理方面的权利及其行使方式发生重大变化；</text>
              <text class="paragraph indent">（5）我们负责处理个人信息安全的责任部门、联络方式及投诉渠道发生变化时；</text>
              <text class="paragraph indent">（6）个人信息安全影响评估报告表明存在高风险时。</text>
              <text class="paragraph">10.4 我们还会将本隐私政策的旧版本存档，供您查阅。</text>
            </view>
          </view>

          <!-- 第十一条 -->
          <view class="privacy-section">
            <view class="section-title">第十一条 适用范围</view>
            <view class="section-content">
              <text class="paragraph">11.1 本隐私政策适用于火源灵感火花小程序及其相关服务。</text>
              <text class="paragraph">11.2 本隐私政策不适用于：</text>
              <text class="paragraph indent">（1）通过我们的服务而接入的第三方服务（包括任何第三方网站）收集的信息；</text>
              <text class="paragraph indent">（2）为我们的服务进行广告宣传的其他公司或机构所收集的信息。</text>
            </view>
          </view>

          <!-- 第十二条 -->
          <view class="privacy-section">
            <view class="section-title">第十二条 联系我们</view>
            <view class="section-content">
              <text class="paragraph">如果您对本隐私政策有任何疑问、意见或建议，或需要行使您的权利，您可以通过以下方式与我们联系：</text>
              <text class="paragraph">客服邮箱：privacy@sfire.ai</text>
              <text class="paragraph">客服电话：400-XXX-XXXX</text>
              <text class="paragraph">服务时间：工作日 9:00-18:00</text>
              <text class="paragraph">我们将在15个工作日内回复您的请求。</text>
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

.privacy-page {
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

// 隐私政策内容区域
.privacy-content {
  flex: 1;
  padding-top: 40rpx;
}

.privacy-container {
  max-width: 100%;
  padding: 0 32rpx 40rpx;
}

// 标题
.privacy-title {
  font-size: 48rpx;
  font-weight: 700;
  color: $text-primary;
  text-align: center;
  margin-bottom: 24rpx;
  line-height: 1.4;
}

// 日期
.privacy-date {
  font-size: $font-size-sm;
  color: $text-muted;
  text-align: center;
  margin-bottom: 48rpx;
}

// 隐私政策正文
.privacy-body {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 48rpx 32rpx;
  box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.04);
}

// 章节
.privacy-section {
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

.sub-title {
  font-size: $font-size-md;
  font-weight: 600;
  color: $text-primary;
  margin-top: 8rpx;
  margin-bottom: 8rpx;
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

.paragraph.indent-double {
  padding-left: 64rpx;
  position: relative;

  &::before {
    content: '•';
    position: absolute;
    left: 48rpx;
    top: 0;
    color: $text-secondary;
  }
}

// 底部占位
.bottom-spacer {
  height: 80rpx;
}
</style>

