/**
 * 文章API
 * 用于获取小程序首页的文章内容
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
  is_published: boolean
  is_enabled: boolean
  created_at: string
  updated_at?: string
}

export interface ArticleListResponse {
  list: ArticleItem[]
  total: number
  pageNum: number
  pageSize: number
}

export interface ArticleListApiResponse {
  code: number
  data: ArticleListResponse
  msg: string
}

/**
 * 获取文章列表
 * @param category 文章类型：founder_story-创始人故事, operation_article-运营干货, customer_case-客户案例, announcement-公告
 * @param pageNum 页码，默认1
 * @param pageSize 每页数量，默认10
 */
export function getArticleList(
  category?: 'founder_story' | 'operation_article' | 'customer_case' | 'announcement',
  pageNum: number = 1,
  pageSize: number = 10
) {
  let url = '/api/v1/client/articles'
  const params: any = {
    pageNum,
    pageSize
  }
  if (category) {
    params.category = category
  }
  return request<ArticleListApiResponse>({
    url,
    method: 'GET',
    data: params,
    showLoading: false
  })
}

/**
 * 获取文章详情
 * @param id 文章ID
 */
export interface ArticleDetailApiResponse {
  code: number
  data: ArticleItem
  msg: string
}

export function getArticleDetail(id: number) {
  return request<ArticleDetailApiResponse>({
    url: `/api/v1/client/articles/${id}`,
    method: 'GET',
    showLoading: false
  })
}

