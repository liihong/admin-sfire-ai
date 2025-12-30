// ? 全局默认配置项

// 首页地址（默认）
export const HOME_URL: string = "/home/index";

// 登录页地址（默认）
export const LOGIN_URL: string = "/login";

// 默认主题颜色 - SFire 爱马仕橙
export const DEFAULT_PRIMARY: string = "#FF7700";

// 路由白名单地址（本地存在的路由 staticRouter.ts 中）
export const ROUTER_WHITE_LIST: string[] = ["/500"];

// 高德地图 key
export const AMAP_MAP_KEY: string = "";

// 百度地图 key
export const BAIDU_MAP_KEY: string = "";

// ================== SFire AI 业务配置 ==================

// 用户等级配置
export const USER_LEVEL_CONFIG = {
  0: { label: "普通用户", color: "#909399", discount: 1 },
  1: { label: "会员", color: "#FF7700", discount: 0.9 },
  2: { label: "合伙人", color: "#E6A23C", discount: 0.7 }
} as const;

// 算力相关配置
export const COMPUTE_CONFIG = {
  // 算力不足警告阈值
  LOW_BALANCE_THRESHOLD: 100,
  // 默认充值金额选项
  RECHARGE_OPTIONS: [100, 500, 1000, 5000],
  // 算力单位名称
  UNIT_NAME: "算力点"
} as const;

// 权限码常量
export const AUTH_CODES = {
  // 财务相关
  FINANCE_APPROVE: "FINANCE_APPROVE", // 提现审核
  FINANCE_RECHARGE: "FINANCE_RECHARGE", // 充值操作
  // 用户相关
  USER_MANAGE: "USER_MANAGE", // 用户管理
  USER_LEVEL_EDIT: "USER_LEVEL_EDIT", // 修改用户等级
  // 系统相关
  SYSTEM_CONFIG: "SYSTEM_CONFIG" // 系统配置
} as const;
