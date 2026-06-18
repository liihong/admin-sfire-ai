/**
 * 顶妈知识库 v2 管理 API
 */
import { ResPage } from "@/api/interface/index";
import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";

export interface Guardrail {
  contains?: string[];
  excludes?: string[];
  forbidden?: string[];
  writable_tags?: string[];
}

export interface ProcessCopywriting {
  scene_keywords?: string[];
  focus_label?: string;
  aliases?: string[];
  writable_ingredients?: string[];
  writable_actions?: string[];
  forbidden_ingredients?: string[];
  scene_hint?: string;
}

export interface RecipeDetail {
  ingredients?: Array<{ name: string; amount?: string }>;
  steps?: string[];
  notes?: string[];
}

export interface SkuComponentLink {
  component_code: string;
  component_name?: string;
  role?: string;
  process_focus?: boolean;
  display_label?: string;
  sort_order?: number;
}

export interface KnowledgeSkuItem {
  id: number;
  tenant_id: number;
  sku_code: string;
  sku_name: string;
  category_code: string;
  category_name: string;
  aliases?: string[];
  pack_formula?: string;
  guardrail?: Guardrail;
  process_copywriting?: ProcessCopywriting;
  component_links?: SkuComponentLink[];
  source_version?: string;
  status: number;
  sort_order: number;
  created_at: string;
  updated_at?: string;
}

export interface KnowledgeComponentItem {
  id: number;
  tenant_id: number;
  component_code: string;
  component_name: string;
  component_type: string;
  aliases?: string[];
  pack_formula?: string;
  recipe_detail?: RecipeDetail;
  guardrail?: Guardrail;
  process_copywriting?: ProcessCopywriting;
  source_version?: string;
  status: number;
  sort_order: number;
  created_at: string;
  updated_at?: string;
}

export interface SkuCategory {
  category_code: string;
  category_name: string;
  count: number;
}

export interface ComponentOption {
  component_code: string;
  component_name: string;
  component_type: string;
}

const BASE = PORT1 + "/dingma/product-knowledge";

// SKU
export const getKnowledgeSkuListApi = (params: Record<string, unknown>) =>
  http.get<ResPage<KnowledgeSkuItem>>(`${BASE}/skus`, params);

export const getKnowledgeSkuCategoriesApi = () => http.get<SkuCategory[]>(`${BASE}/skus/categories`);

export const getKnowledgeSkuDetailApi = (id: number) => http.get<KnowledgeSkuItem>(`${BASE}/skus/${id}`);

export const createKnowledgeSkuApi = (data: Partial<KnowledgeSkuItem>) =>
  http.post<KnowledgeSkuItem>(`${BASE}/skus`, data);

export const updateKnowledgeSkuApi = (id: number, data: Partial<KnowledgeSkuItem>) =>
  http.put<KnowledgeSkuItem>(`${BASE}/skus/${id}`, data);

export const updateKnowledgeSkuStatusApi = (id: number, status: number) =>
  http.patch<KnowledgeSkuItem>(`${BASE}/skus/${id}/status`, null, { params: { status } });

export const deleteKnowledgeSkuApi = (id: number) => http.delete(`${BASE}/skus/${id}`);

// Component
export const getKnowledgeComponentListApi = (params: Record<string, unknown>) =>
  http.get<ResPage<KnowledgeComponentItem>>(`${BASE}/components`, params);

export const getKnowledgeComponentOptionsApi = () =>
  http.get<ComponentOption[]>(`${BASE}/components/options`);

export const getKnowledgeComponentDetailApi = (id: number) =>
  http.get<KnowledgeComponentItem>(`${BASE}/components/${id}`);

export const createKnowledgeComponentApi = (data: Partial<KnowledgeComponentItem>) =>
  http.post<KnowledgeComponentItem>(`${BASE}/components`, data);

export const updateKnowledgeComponentApi = (id: number, data: Partial<KnowledgeComponentItem>) =>
  http.put<KnowledgeComponentItem>(`${BASE}/components/${id}`, data);

export const updateKnowledgeComponentStatusApi = (id: number, status: number) =>
  http.patch<KnowledgeComponentItem>(`${BASE}/components/${id}/status`, null, { params: { status } });

export const deleteKnowledgeComponentApi = (id: number) => http.delete(`${BASE}/components/${id}`);
