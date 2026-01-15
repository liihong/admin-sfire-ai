/**
 * Coin API - 算力/币种相关接口
 */
import { request } from '@/utils/request'

/**
 * 获取算力交易记录请求参数类型
 */
export interface CoinTransactionsRequest {
  pageNum: number
  pageSize: number
}

/**
 * 获取算力交易记录
 */
export function getCoinTransactions(params: CoinTransactionsRequest) {
  const queryString = `pageNum=${params.pageNum}&pageSize=${params.pageSize}`
  return request<any>({
    url: `/api/v1/client/coin/transactions?${queryString}`,
    method: 'GET',
    showLoading: false
  })
}

