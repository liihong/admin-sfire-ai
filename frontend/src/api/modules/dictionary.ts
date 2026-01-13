import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 数据字典管理模块
 * 字典类型和字典项的 CRUD 接口
 */

// ============== 类型定义 ==============

export namespace Dictionary {
  // 字典类型
  export interface DictType {
    id: number;
    dict_code: string;
    dict_name: string;
    description?: string;
    is_enabled: boolean;
    sort_order: number;
    created_at: string;
    updated_at?: string;
  }

  // 字典项
  export interface DictItem {
    id: number;
    dict_id: number;
    item_value: string;
    item_label: string;
    description?: string;
    is_enabled: boolean;
    sort_order: number;
    created_at: string;
    updated_at?: string;
  }

  // 简单字典项（用于下拉选项）
  export interface DictItemSimple {
    label: string;
    value: string;
  }

  // 字典类型查询参数
  export interface ReqDictParams {
    pageNum?: number;
    pageSize?: number;
    dict_code?: string;
    dict_name?: string;
    is_enabled?: boolean;
  }

  // 字典项查询参数
  export interface ReqDictItemParams {
    pageNum?: number;
    pageSize?: number;
    dict_id?: number;
    dict_code?: string;
    item_value?: string;
    item_label?: string;
    is_enabled?: boolean;
  }

  // 创建字典类型请求
  export interface ReqDictCreate {
    dict_code: string;
    dict_name: string;
    description?: string;
    is_enabled?: boolean;
    sort_order?: number;
  }

  // 更新字典类型请求
  export interface ReqDictUpdate {
    dict_code?: string;
    dict_name?: string;
    description?: string;
    is_enabled?: boolean;
    sort_order?: number;
  }

  // 创建字典项请求
  export interface ReqDictItemCreate {
    dict_id: number;
    item_value: string;
    item_label: string;
    description?: string;
    is_enabled?: boolean;
    sort_order?: number;
  }

  // 更新字典项请求
  export interface ReqDictItemUpdate {
    item_value?: string;
    item_label?: string;
    description?: string;
    is_enabled?: boolean;
    sort_order?: number;
  }
}

// ============== 字典类型接口 ==============

/**
 * 获取字典类型列表（分页）
 */
export const getDictList = (params?: Dictionary.ReqDictParams) => {
  return http.get<ResPage<Dictionary.DictType>>(PORT1 + `/dictionary`, params);
};

/**
 * 获取所有字典类型（不分页，用于下拉选择）
 */
export const getAllDicts = (is_enabled?: boolean) => {
  return http.get<Dictionary.DictType[]>(PORT1 + `/dictionary/all`, { is_enabled });
};

/**
 * 获取字典类型详情
 */
export const getDictDetail = (id: number, with_items: boolean = false) => {
  return http.get<Dictionary.DictType>(PORT1 + `/dictionary/${id}`, { with_items });
};

/**
 * 创建字典类型
 */
export const createDict = (params: Dictionary.ReqDictCreate) => {
  return http.post<Dictionary.DictType>(PORT1 + `/dictionary`, params);
};

/**
 * 更新字典类型
 */
export const updateDict = (id: number, params: Dictionary.ReqDictUpdate) => {
  return http.put<Dictionary.DictType>(PORT1 + `/dictionary/${id}`, params);
};

/**
 * 删除字典类型
 */
export const deleteDict = (id: number) => {
  return http.delete(PORT1 + `/dictionary/${id}`);
};

// ============== 字典项接口 ==============

/**
 * 获取字典项列表（分页）
 */
export const getDictItemList = (params?: Dictionary.ReqDictItemParams) => {
  return http.get<ResPage<Dictionary.DictItem>>(PORT1 + `/dictionary/items/list`, params);
};

/**
 * 根据字典编码获取字典项（用于下拉选项）
 */
export const getDictItemsByCode = (dict_code: string, enabled_only: boolean = true) => {
  return http.get<Dictionary.DictItemSimple[]>(PORT1 + `/dictionary/items/by-code/${dict_code}`, { enabled_only });
};

/**
 * 获取字典项详情
 */
export const getDictItemDetail = (id: number) => {
  return http.get<Dictionary.DictItem>(PORT1 + `/dictionary/items/${id}`);
};

/**
 * 创建字典项
 */
export const createDictItem = (params: Dictionary.ReqDictItemCreate) => {
  return http.post<Dictionary.DictItem>(PORT1 + `/dictionary/items`, params);
};

/**
 * 更新字典项
 */
export const updateDictItem = (id: number, params: Dictionary.ReqDictItemUpdate) => {
  return http.put<Dictionary.DictItem>(PORT1 + `/dictionary/items/${id}`, params);
};

/**
 * 删除字典项
 */
export const deleteDictItem = (id: number) => {
  return http.delete(PORT1 + `/dictionary/items/${id}`);
};








