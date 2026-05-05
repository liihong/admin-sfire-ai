/**
 * Coin API - 算力/币种相关接口
 */
import { request } from '@/utils/request'

/**
 * 算力余额响应类型
 */
export interface CoinBalanceResponse {
  balance: number
  frozen_balance: number
  available_balance: number
}

/**
 * 获取算力交易记录请求参数类型
 */
export interface CoinTransactionsRequest {
  pageNum: number
  pageSize: number
}

/**
 * 获取算力余额
 */
export function getBalance(): Promise<{ code: number; data: CoinBalanceResponse; msg: string }> {
  return request<{ code: number; data: CoinBalanceResponse; msg: string }>({
    url: '/api/v1/client/coin/balance',
    method: 'GET',
    showLoading: false
  })
}

/**
 * 算力交易记录项
 */
export interface CoinTransactionItem {
  id: number
  type: string
  amount: number
  balance: number
  description?: string
  created_at: string
}

/**
 * 算力交易记录响应
 */
export interface CoinTransactionsResponse {
  list: CoinTransactionItem[]
  total: number
  pageNum: number
  pageSize: number
}

/**
 * 算力/使用统计（与 /coin/statistics 一致）
 */
export interface CoinStatisticsData {
  balance: number
  frozenBalance: number
  availableBalance: number
  totalRecharge: number
  totalConsume: number
  totalRefund: number
  totalReward: number
  totalCommission: number
  totalAdjustment: number
  monthConsumption: number
  /** 累计 AI 助手消息数，用作「调用 AI」参考 */
  totalContent: number
  withDay: number
}

/**
 * 用户算力与使用汇总统计
 */
export function getCoinStatistics() {
  return request<{ code: number; data: CoinStatisticsData; msg: string }>({
    url: '/api/v1/client/coin/statistics',
    method: 'GET',
    showLoading: false
  })
}

/**
 * 获取算力交易记录
 */
export function getCoinTransactions(params: CoinTransactionsRequest) {
  const queryString = `pageNum=${params.pageNum}&pageSize=${params.pageSize}`
  return request<CoinTransactionsResponse>({
    url: `/api/v1/client/coin/transactions?${queryString}`,
    method: 'GET',
    showLoading: false
  })
}

