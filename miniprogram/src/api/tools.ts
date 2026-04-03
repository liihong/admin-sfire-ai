/**
 * 便捷工具 API（与 C 端 /api/v1/client/tools 一致）
 */
import { request } from '@/utils/request'

export interface DouyinCaptionExtractData {
  text: string
  aweme_id: string
  title?: string | null
}

/** 抖音链接提取口播文案（需登录） */
export function extractDouyinCaption(params: { url: string }) {
  return request<DouyinCaptionExtractData>({
    url: '/api/v1/client/tools/douyin-caption/extract',
    method: 'POST',
    data: params,
    showLoading: true,
    loadingText: '识别中，请稍候…'
  })
}
