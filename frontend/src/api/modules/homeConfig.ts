import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 首页配置模块
 * 对接 /api/v1/home-configs 接口
 */

export interface HomeConfigItem {
  id: number;
  config_key: string;
  config_value?: string;
  config_type: "string" | "json" | "array";
  description?: string;
  is_enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface HomeConfigList {
  list: HomeConfigItem[];
  total: number;
}

// 获取所有配置
export const getAllConfigs = () => {
  return http.get<HomeConfigList>(PORT1 + `/home-configs`);
};

// 获取指定配置
export const getConfigByKey = (configKey: string, useCache: boolean = true) => {
  return http.get<HomeConfigItem>(PORT1 + `/home-configs/${configKey}`, { use_cache: useCache });
};

// 更新配置
export const updateConfig = (params: {
  config_key: string;
  config_value?: string;
  config_type?: "string" | "json" | "array";
  description?: string;
  is_enabled?: boolean;
}) => {
  const { config_key, ...data } = params;
  return http.put(PORT1 + `/home-configs/${config_key}`, data);
};

// 批量更新配置
export const batchUpdateConfigs = (configs: Array<{
  config_key: string;
  config_value?: string;
  config_type?: "string" | "json" | "array";
  description?: string;
  is_enabled?: boolean;
}>) => {
  return http.post(PORT1 + `/home-configs/batch`, { configs });
};

