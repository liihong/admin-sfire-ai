/**
 * dingma 租户小程序：公开接口租户标识（与后端 tenants.code / tenants.wechat_app_id 一致）
 */
export const DINGMA_TENANT_CODE = 'dingma'

/** 小程序首页全屏展示图 */
export const DINGMA_SPLASH_IMAGE_URL = 'https://oss.sourcefire.cn/dingma/dingmavi.jpg'

/** 创富工具 Tab 顶部横幅（可替换为与设计稿一致的主题图） */
export const DINGMA_HOME_BANNER_URL = 'https://oss.sourcefire.cn/dingma/dingmavi.jpg'

/** 仅首次进入小程序时播放首页轻微放大动画，标记后不再播放 */
export const STORAGE_DINGMA_SPLASH_ZOOM_PLAYED = 'dingma_splash_zoom_played'

/** 对话页智能体（顶顶妈分身）默认头像 */
export const DINGMA_AGENT_DEFAULT_AVATAR_URL = 'https://oss.sourcefire.cn/dingma/dingmalogo.jpg'

/** 「我的」页未登录 / 无头像时的默认展示（顶妈品牌） */
export const DINGMA_DEFAULT_PROFILE_AVATAR_URL = DINGMA_AGENT_DEFAULT_AVATAR_URL

/** 微信小程序 AppID（与 manifest mp-weixin.appid 一致，勿带首尾空格） */
export const DINGMA_WECHAT_APP_ID = 'wx22d311d2ee7c7ae6'

/** 附加到 /api/v1/client 请求的 Query/Body 与 Header */
export const DINGMA_PUBLIC_TENANT_SCOPE = {
  /** Query 参数名 tenant_id：传租户代码 dingma（后端按 Tenant.code 解析） */
  tenant_id: DINGMA_TENANT_CODE,
  /** Query 参数名 appid：微信小程序 AppID */
  appid: DINGMA_WECHAT_APP_ID,
} as const
