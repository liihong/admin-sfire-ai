import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

/**
 * 顶妈产品知识库（配方）管理
 * 对接 /api/v1/admin/dingma/product-knowledge
 */

export interface RecipeDetail {
  ingredients?: Array<{ name: string; amount?: string }>;
  steps?: string[];
  notes?: string[];
  base_recipe_ref?: string;
}

export interface ProductKnowledgeItem {
  id: number;
  tenant_id: number;
  category_code: string;
  category_name: string;
  product_code: string;
  product_name: string;
  aliases?: string[];
  pack_formula?: string;
  recipe_detail?: RecipeDetail;
  copywriting_facts?: string;
  source_version?: string;
  status: number;
  sort_order: number;
  created_at: string;
  updated_at?: string;
}

export interface ProductKnowledgeParams {
  pageNum?: number;
  pageSize?: number;
  category_code?: string;
  product_name?: string;
  product_code?: string;
  status?: number;
  keyword?: string;
}

export interface ProductKnowledgeCreate {
  category_code: string;
  category_name: string;
  product_code: string;
  product_name: string;
  aliases?: string[];
  pack_formula?: string;
  recipe_detail?: RecipeDetail;
  copywriting_facts?: string;
  source_version?: string;
  status?: number;
  sort_order?: number;
}

export type ProductKnowledgeUpdate = Partial<Omit<ProductKnowledgeCreate, "product_code">>;

export interface ProductKnowledgeCategory {
  category_code: string;
  category_name: string;
  count: number;
}

const BASE = PORT1 + "/dingma/product-knowledge";

export const getProductKnowledgeListApi = (params: ProductKnowledgeParams) => {
  return http.get<ResPage<ProductKnowledgeItem>>(BASE, params);
};

export const getProductKnowledgeCategoriesApi = () => {
  return http.get<ProductKnowledgeCategory[]>(BASE + "/categories");
};

export const getProductKnowledgeDetailApi = (id: number) => {
  return http.get<ProductKnowledgeItem>(`${BASE}/${id}`);
};

export const createProductKnowledgeApi = (data: ProductKnowledgeCreate) => {
  return http.post<ProductKnowledgeItem>(BASE, data);
};

export const updateProductKnowledgeApi = (id: number, data: ProductKnowledgeUpdate) => {
  return http.put<ProductKnowledgeItem>(`${BASE}/${id}`, data);
};

export const updateProductKnowledgeStatusApi = (id: number, status: number) => {
  return http.patch<ProductKnowledgeItem>(`${BASE}/${id}/status`, null, { params: { status } });
};

export const deleteProductKnowledgeApi = (id: number) => {
  return http.delete(`${BASE}/${id}`);
};
