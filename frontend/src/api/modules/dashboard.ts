import http from "@/api";
import { PORT1 } from "@/api/config/servicePort";

/**
 * @name Dashboard 统计模块
 * 首页数据统计接口
 */

// 统计数据接口类型
export namespace Dashboard {
  // 核心指标数据
  export interface StatsData {
    todayNewUsers: number; // 今日新增用户
    apiBalance: number; // API 余额
    todayComputeUsage: number; // 今日算力消耗
    todayOrderAmount: number; // 今日订单额
    // 对比数据（较昨日）
    userGrowthRate: number; // 用户增长率
    computeGrowthRate: number; // 算力消耗增长率
    orderGrowthRate: number; // 订单增长率
  }

  // 用户增长趋势数据
  export interface UserTrendItem {
    date: string;
    newUsers: number;
    activeUsers: number;
  }

  // 智能体调用排行
  export interface AgentRankItem {
    id: string;
    name: string;
    icon: string;
    callCount: number;
  }

  // 系统预警配置
  export interface AlertConfig {
    apiBalanceThreshold: number; // API 余额预警阈值
    computeThreshold: number; // 算力消耗预警阈值
  }
}

// 获取核心统计数据
export const getStatsData = () => {
  return http.get<Dashboard.StatsData>(PORT1 + `/dashboard/stats`);
};

// 获取用户增长趋势（7天）
export const getUserTrend = (days: number = 7) => {
  return http.get<Dashboard.UserTrendItem[]>(PORT1 + `/dashboard/user-trend`, { days });
};

// 获取智能体调用排行（Top 5）
export const getAgentRank = (limit: number = 5) => {
  return http.get<Dashboard.AgentRankItem[]>(PORT1 + `/dashboard/agent-rank`, { limit });
};

// 获取预警配置
export const getAlertConfig = () => {
  return http.get<Dashboard.AlertConfig>(PORT1 + `/dashboard/alert-config`);
};
