/**
 * Copywriting Library API - 文案库相关接口（小程序端）
 *
 * 说明：
 * - 文案库是独立业务线，不依赖 inspirations / AI对话
 * - 每个用户的每个IP(Project)有独立文案库，调用时必须携带 project_id
 */

import { request } from '@/utils/request'

export type CopywritingEntryStatus = 'draft' | 'todo' | 'published' | 'archived'

export interface CopywritingEntry {
  id: number
  user_id: number
  project_id: number
  project_name?: string

  content: string
  tags: string[]
  status: CopywritingEntryStatus

  views?: number | null
  likes?: number | null
  comments?: number | null
  shares?: number | null
  published_at?: string | null

  created_at: string
  updated_at?: string | null
}

export interface PageResponse<T> {
  code: number
  data: {
    list: T[]
    pageNum: number
    pageSize: number
    total: number
  }
  msg: string
}

export interface CreateCopywritingEntryRequest {
  project_id: number
  content: string
  tags?: string[]
  status?: CopywritingEntryStatus
}

export interface UpdateCopywritingEntryRequest {
  content?: string
  tags?: string[]
  status?: CopywritingEntryStatus
}

export interface GetCopywritingEntryListParams {
  pageNum?: number
  pageSize?: number
  project_id: number
  status?: CopywritingEntryStatus
  tag?: string
  keyword?: string
  sort_by?: 'created_at' | 'updated_at'
  sort_order?: 'asc' | 'desc'
}

export interface PublishDataUpdateRequest {
  views?: number
  likes?: number
  comments?: number
  shares?: number
  published_at?: string
}

export async function createCopywritingEntry(data: CreateCopywritingEntryRequest): Promise<CopywritingEntry> {
  const response = await request<{ code: number; data: CopywritingEntry; msg: string }>({
    url: '/api/v1/client/copywriting-library',
    method: 'POST',
    data,
  })

  if (response.code === 200 && response.data) {
    return response.data
  }
  throw new Error(response.msg || '保存失败')
}

export async function getCopywritingEntryList(
  params: GetCopywritingEntryListParams
): Promise<PageResponse<CopywritingEntry>> {
  const response = await request<PageResponse<CopywritingEntry>>({
    url: '/api/v1/client/copywriting-library',
    method: 'GET',
    data: params,
    showLoading: false,
  })

  if (response.code === 200) {
    return response
  }
  throw new Error(response.msg || '获取列表失败')
}

export async function getCopywritingEntryDetail(entryId: number): Promise<CopywritingEntry> {
  const response = await request<{ code: number; data: CopywritingEntry; msg: string }>({
    url: `/api/v1/client/copywriting-library/${entryId}`,
    method: 'GET',
    showLoading: true,
    loadingText: '加载中...',
  })

  if (response.code === 200 && response.data) {
    return response.data
  }
  throw new Error(response.msg || '获取详情失败')
}

export async function updateCopywritingEntry(
  entryId: number,
  data: UpdateCopywritingEntryRequest
): Promise<CopywritingEntry> {
  const response = await request<{ code: number; data: CopywritingEntry; msg: string }>({
    url: `/api/v1/client/copywriting-library/${entryId}`,
    method: 'PUT',
    data,
  })

  if (response.code === 200 && response.data) {
    return response.data
  }
  throw new Error(response.msg || '更新失败')
}

export async function deleteCopywritingEntry(entryId: number): Promise<void> {
  const response = await request<{ code: number; msg: string }>({
    url: `/api/v1/client/copywriting-library/${entryId}`,
    method: 'DELETE',
  })

  if (response.code === 200) return
  throw new Error(response.msg || '删除失败')
}

export async function updateCopywritingPublishData(
  entryId: number,
  data: PublishDataUpdateRequest
): Promise<CopywritingEntry> {
  const response = await request<{ code: number; data: CopywritingEntry; msg: string }>({
    url: `/api/v1/client/copywriting-library/${entryId}/publish-data`,
    method: 'POST',
    data,
  })

  if (response.code === 200 && response.data) {
    return response.data
  }
  throw new Error(response.msg || '保存失败')
}

