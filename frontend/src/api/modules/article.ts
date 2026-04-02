import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * @name 文章管理模块
 * 对接 /api/v1/admin/articles 接口
 * 文章类型为 sys_dict dict_code=article_category 的 item_value（01-04）
 */

export type ArticleCategoryCode = "01" | "02" | "03" | "04";

export interface ArticleItem {
  id: number;
  category: ArticleCategoryCode | string;
  /** sys_dict article_category 的 item_label */
  category_name: string;
  author: string;
  title: string;
  content: string;
  summary?: string;
  cover_image?: string;
  tags?: string[];
  sort_order: number;
  publish_time?: string;
  view_count: number;
  is_published: boolean;
  is_enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ArticleParams {
  pageNum: number;
  pageSize: number;
  category?: string;
  title?: string;
  tag?: string;
  is_published?: boolean;
  is_enabled?: boolean;
}

// 获取文章列表
export const getArticleList = (params: ArticleParams) => {
  return http.get<ResPage<ArticleItem>>(PORT1 + `/articles`, params);
};

// 获取文章详情
export const getArticleDetail = (id: number) => {
  return http.get<ArticleItem>(PORT1 + `/articles/${id}`);
};

// 新增文章
export const addArticle = (params: {
  category: ArticleCategoryCode;
  author?: string;
  title: string;
  content: string;
  summary?: string;
  cover_image?: string;
  tags?: string[];
  sort_order?: number;
  publish_time?: string;
  is_published?: boolean;
  is_enabled?: boolean;
}) => {
  return http.post(PORT1 + `/articles`, params);
};

// 编辑文章
export const editArticle = (params: {
  id: number;
  category?: ArticleCategoryCode;
  author?: string;
  title?: string;
  content?: string;
  summary?: string;
  cover_image?: string;
  tags?: string[];
  sort_order?: number;
  publish_time?: string;
  is_published?: boolean;
  is_enabled?: boolean;
}) => {
  const { id, ...data } = params;
  return http.put(PORT1 + `/articles/${id}`, data);
};

// 删除文章
export const deleteArticle = (id: number) => {
  return http.delete(PORT1 + `/articles/${id}`);
};

// 更新文章状态
export const updateArticleStatus = (params: {
  id: number;
  is_published?: boolean;
  is_enabled?: boolean;
}) => {
  const { id, ...data } = params;
  return http.put(PORT1 + `/articles/${id}/status`, data);
};
