/**
 * Recharge API - 充值相关接口
 */
import { request } from '@/utils/request'

/**
 * 套餐信息类型
 */
export interface Package {
  id: number
  name: string
  price: number
  power_amount: number
  unit_price?: string
  tag?: string[]
  description?: string
  article_count?: number
  sort_order: number
  status: number
  is_popular: boolean
}

/**
 * 创建订单请求参数
 */
export interface CreateOrderRequest {
  package_id: number
}

/**
 * 订单响应类型
 */
export interface OrderResponse {
  order_id: string
  package_id: number
  package_name: string
  price: number
  power_amount: number
  payment_status: string
  payment_params: {
    timeStamp: string
    nonceStr: string
    package: string
    signType: string
    paySign: string
  }
  created_at: string
}

/**
 * 订单状态响应类型
 */
export interface OrderStatusResponse {
  order_id: string
  payment_status: string
  payment_time?: string
  wechat_transaction_id?: string
}

/**
 * 获取套餐列表
 */
export function getPackages(): Promise<{ code: number; data: Package[]; msg: string }> {
  return request<{ code: number; data: Package[]; msg: string }>({
    url: '/api/v1/client/coin/packages',
    method: 'GET',
    showLoading: false
  })
}

/**
 * 创建充值订单
 */
export function createRechargeOrder(
  params: CreateOrderRequest
): Promise<{ code: number; data: OrderResponse; msg: string }> {
  return request<{ code: number; data: OrderResponse; msg: string }>({
    url: '/api/v1/client/coin/recharge/order',
    method: 'POST',
    data: params,
    showLoading: true
  })
}

/**
 * 查询订单状态
 */
export function queryOrderStatus(
  orderId: string
): Promise<{ code: number; data: OrderStatusResponse; msg: string }> {
  return request<{ code: number; data: OrderStatusResponse; msg: string }>({
    url: `/api/v1/client/coin/recharge/order/${orderId}`,
    method: 'GET',
    showLoading: false
  })
}

