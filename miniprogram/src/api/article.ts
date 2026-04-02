/**
 * 文章API
 * 用于获取小程序首页的文章内容
 * 文章类型 category 为 sys_dict article_category 的 item_value：01-04
 */
import { request } from '@/utils/request'

export type ArticleCategoryCode = '01' | '02' | '03' | '04'

export interface ArticleItem {
  id: number
  category: string
  /** sys_dict article_category 的 item_label */
  category_name: string
  author?: string
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
 * @param category 文章类型：01-商业底牌 02-流量心法 03-实操手册 04-创始人说
 */
export function getArticleList(
  category?: string,
  pageNum: number = 1,
  pageSize: number = 10
) {
  let url = '/api/v1/client/articles'
  const params: {
    pageNum: number
    pageSize: number
    category?: string
  } = {
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
