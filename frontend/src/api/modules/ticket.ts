import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 工单管理模块
 * 对接 /api/v1/admin/tickets 接口
 */

/** 工单类型 */
export type TicketType = "membership" | "recharge";

/** 工单状态 */
export type TicketStatus = "pending" | "processing" | "completed" | "rejected" | "failed";

/** 会员周期 */
export type PeriodType = "monthly" | "quarterly" | "yearly";

/** 工单列表项 */
export interface TicketItem {
  id: number;
  type: TicketType;
  status: TicketStatus;
  user_id: number;
  user?: { id: string; username: string; phone?: string; nickname?: string };
  creator_id: number;
  creator?: { id: number; username: string };
  handler_id?: number;
  handler?: { id: number; username: string };
  is_paid?: boolean;
  payment_method?: string;
  voucher?: string;
  period_type?: string;
  extra_data?: Record<string, unknown>;
  remark?: string;
  handled_at?: string;
  fail_reason?: string;
  created_at: string;
  updated_at?: string;
}

/** 工单查询参数 */
export interface TicketQueryParams {
  pageNum: number;
  pageSize: number;
  type?: TicketType;
  status?: TicketStatus;
  user_id?: number;
  creator_id?: number;
}

/** 创建会员工单参数 */
export interface TicketMembershipCreate {
  level_code: string;
  vip_expire_date: string;
  is_paid: boolean;
  payment_method?: string;
  voucher?: string;
  period_type: PeriodType;
}

/** 创建充值工单参数 */
export interface TicketRechargeCreate {
  amount: number;
}

/** 创建工单参数 */
export interface TicketCreateParams {
  type: TicketType;
  user_id: number;
  membership?: TicketMembershipCreate;
  recharge?: TicketRechargeCreate;
  remark?: string;
}

// 获取工单列表
export const getTicketList = (params: TicketQueryParams) => {
  return http.get<ResPage<TicketItem>>(PORT1 + `/tickets`, params);
};

// 获取工单详情
export const getTicketDetail = (id: number) => {
  return http.get<TicketItem>(PORT1 + `/tickets/${id}`);
};

// 创建工单
export const createTicket = (params: TicketCreateParams) => {
  return http.post<{ id: number }>(PORT1 + `/tickets`, params);
};

// 处理工单
export const handleTicket = (id: number) => {
  return http.post<TicketItem>(PORT1 + `/tickets/${id}/handle`);
};
