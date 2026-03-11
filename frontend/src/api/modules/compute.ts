import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 算力明细模块
 * 对接 /api/v1/admin/compute-logs 接口
 */

/** 系统算力统计 */
export interface ComputeStats {
  totalConsume: number;
  totalRecharge: number;
}

/** 用户算力汇总 */
export interface UserComputeSummary {
  userId: string;
  username?: string;
  phone?: string;
  totalConsume: number;
  totalRecharge: number;
}

/** 用户算力汇总查询参数 */
export interface UserComputeSummaryParams {
  pageNum: number;
  pageSize: number;
  username?: string;
  startTime?: string;
  endTime?: string;
}

/** 算力流水记录 */
export interface ComputeLogItem {
  id: string;
  userId: string;
  username?: string;
  type: string;
  typeName: string;
  amount: number;
  /** 充值时的支付金额（元），非充值时为 undefined */
  paymentAmount?: number;
  beforeBalance: number;
  afterBalance: number;
  remark?: string;
  orderId?: string;
  taskId?: string;
  operatorId?: string;
  operatorName?: string;
  source?: string;
  createTime: string;
}

/** 用户流水查询参数 */
export interface UserComputeLogsParams {
  pageNum: number;
  pageSize: number;
  type?: "consume" | "recharge";
}

/** 获取系统算力统计 */
export const getComputeStats = () => {
  return http.get<ComputeStats>(PORT1 + `/compute-logs/stats`);
};

/** 获取用户算力汇总列表 */
export const getComputeUserSummary = (params: UserComputeSummaryParams) => {
  return http.get<ResPage<UserComputeSummary>>(PORT1 + `/compute-logs/users`, params);
};

/** 获取用户算力流水明细 */
export const getUserComputeLogs = (userId: number, params: UserComputeLogsParams) => {
  return http.get<ResPage<ComputeLogItem>>(PORT1 + `/compute-logs/users/${userId}/logs`, params);
};
