/**
 * 首页内容API
 * 聚合首页所需的所有数据（Banner + 文章）
 * 独立于文章管理接口，专门为首页优化
 */
import { request } from '@/utils/request'

export interface ArticleItem {
  id: number
  category: 'founder_story' | 'operation_article' | 'customer_case' | 'announcement'
  title: string
  content: string
  summary?: string
  cover_image?: string
  tags?: string[]
  sort_order: number
  publish_time?: string
  view_count: number
  created_at: string
}

export interface BannerItem {
  id: number
  title: string
  image_url: string
  link_url?: string
  link_type: 'none' | 'internal' | 'external'
  position: 'home_top' | 'home_middle' | 'home_bottom'
  sort_order: number
}

export interface FeaturedModuleItem {
  icon: string
  label: string
  route?: string
  iconSize?: number
}

export interface HomeContentResponse {
  banners: {
    home_top: BannerItem[]
    home_middle: BannerItem[]
    home_bottom: BannerItem[]
  }
  founder_stories: ArticleItem[]
  operation_articles: ArticleItem[]
  announcements: ArticleItem[]
  customer_cases: ArticleItem[]
  featured_modules: FeaturedModuleItem[]
}

export interface HomeContentApiResponse {
  code: number
  data: HomeContentResponse
  msg: string
}

/**
 * 获取首页内容（聚合接口）
 * 返回首页所需的所有数据：
 * - banners: Banner列表（按位置分组）
 * - founder_stories: 创始人故事列表
 * - operation_articles: 运营干货列表
 * - announcements: 公告列表
 * - customer_cases: 客户案例列表
 * - featured_modules: 推荐模块列表（功能入口）
 */
export function getHomeContent() {
  return request<HomeContentResponse>({
    url: '/api/v1/client/home',
    method: 'GET',
    showLoading: false
  })
}

