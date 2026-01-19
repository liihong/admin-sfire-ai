export type LayoutType = "vertical" | "classic" | "transverse" | "columns";

export type AssemblySizeType = "large" | "default" | "small";

export type LanguageType = "zh" | "en" | null;

/* GlobalState */
export interface GlobalState {
  layout: LayoutType;
  assemblySize: AssemblySizeType;
  language: LanguageType;
  maximize: boolean;
  primary: string;
  isDark: boolean;
  isGrey: boolean;
  isWeak: boolean;
  asideInverted: boolean;
  headerInverted: boolean;
  isCollapse: boolean;
  accordion: boolean;
  watermark: boolean;
  breadcrumb: boolean;
  breadcrumbIcon: boolean;
  tabs: boolean;
  tabsIcon: boolean;
  footer: boolean;
}

/* 用户等级类型 */
export type UserLevelType = "free" | "v1" | "v2" | "v3";

/* 用户等级配置映射 */
export const UserLevelConfig: Record<UserLevelType, { name: string; discount: number; dailyLimit: number }> = {
  free: { name: "免费用户", discount: 1, dailyLimit: 100 },
  v1: { name: "普通会员", discount: 0.95, dailyLimit: 1000 },
  v2: { name: "高级会员", discount: 0.85, dailyLimit: 5000 },
  v3: { name: "尊享会员", discount: 0.7, dailyLimit: -1 } // -1 表示无限制
};

/* UserInfo - 用户信息 */
export interface UserInfo {
  id: string;
  username: string;
  avatar?: string;
  email?: string;
  phone?: string;
  level: UserLevelType;
  computePower: number; // 剩余算力
  totalUsed: number; // 累计消耗
  createTime?: string;
  lastLoginTime?: string;
}

/* UserState */
export interface UserState {
  token: string;
  refreshToken: string;
  tokenExpiresAt: number; // token过期时间戳（毫秒）
  userInfo: UserInfo;
  roles: string[];
}

/* tabsMenuProps */
export interface TabsMenuProps {
  icon: string;
  title: string;
  path: string;
  name: string;
  close: boolean;
  isKeepAlive: boolean;
}

/* TabsState */
export interface TabsState {
  tabsMenuList: TabsMenuProps[];
}

/* AuthState */
export interface AuthState {
  routeName: string;
  authButtonList: {
    [key: string]: string[];
  };
  authMenuList: Menu.MenuOptions[];
}

/* KeepAliveState */
export interface KeepAliveState {
  keepAliveName: string[];
}

/* ComputeState - 算力状态 */
export interface ComputeState {
  // 算力余额
  balance: {
    total: number;
    used: number;
    remaining: number;
    expireTime?: string;
  };
  // 用户等级
  userLevel: {
    level: number;
    levelName: string;
    discount: number;
    dailyLimit: number;
    features: string[];
  };
  // 今日已使用
  todayUsed: number;
  // 是否正在加载
  loading: boolean;
}
