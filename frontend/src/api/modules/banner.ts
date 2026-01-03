import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name Banner管理模块
 * 对接 /api/v1/banners 接口
 */

export interface BannerItem {
  id: number;
  title: string;
  image_url: string;
  link_url?: string;
  link_type: "none" | "internal" | "external";
  position: "home_top" | "home_middle" | "home_bottom";
  sort_order: number;
  start_time?: string;
  end_time?: string;
  is_enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface BannerParams {
  pageNum: number;
  pageSize: number;
  title?: string;
  position?: string;
  is_enabled?: boolean;
}

// 获取Banner列表
export const getBannerList = (params: BannerParams) => {
  return http.get<ResPage<BannerItem>>(PORT1 + `/banners`, params);
};

// 获取Banner详情
export const getBannerDetail = (id: number) => {
  return http.get<BannerItem>(PORT1 + `/banners/${id}`);
};

// 新增Banner
export const addBanner = (params: {
  title: string;
  image_url: string;
  link_url?: string;
  link_type?: "none" | "internal" | "external";
  position?: "home_top" | "home_middle" | "home_bottom";
  sort_order?: number;
  start_time?: string;
  end_time?: string;
  is_enabled?: boolean;
}) => {
  return http.post(PORT1 + `/banners`, params);
};

// 编辑Banner
export const editBanner = (params: {
  id: number;
  title?: string;
  image_url?: string;
  link_url?: string;
  link_type?: "none" | "internal" | "external";
  position?: "home_top" | "home_middle" | "home_bottom";
  sort_order?: number;
  start_time?: string;
  end_time?: string;
  is_enabled?: boolean;
}) => {
  const { id, ...data } = params;
  return http.put(PORT1 + `/banners/${id}`, data);
};

// 删除Banner
export const deleteBanner = (id: number) => {
  return http.delete(PORT1 + `/banners/${id}`);
};

// 更新Banner状态
export const updateBannerStatus = (params: { id: number; is_enabled: boolean }) => {
  return http.put(PORT1 + `/banners/${params.id}/status`, { is_enabled: params.is_enabled });
};

// 批量更新Banner排序
export const updateBannerSort = (items: Array<{ id: number; sort_order: number }>) => {
  return http.put(PORT1 + `/banners/sort`, { items });
};

