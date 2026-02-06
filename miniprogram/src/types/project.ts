/**
 * 项目相关类型定义
 * 
 * 三层类型体系：
 * 1. Database Model - 数据库模型类型（对应后端数据结构）
 * 2. Form Data - 表单数据类型（用于前端表单）
 * 3. API Types - API 请求/响应类型（在 api/project.ts 中定义）
 */

// ============== 数据库模型类型 ==============

/**
 * 人设配置的完整模型（对应数据库 persona_settings JSON 字段）
 * 包含所有字段，包括新增的扩展字段
 */
export interface PersonaSettingsModel {
  // 基础字段
  tone: string
  catchphrase: string
  target_audience: string
  introduction: string
  keywords: string[]
  
  // 扩展字段（新增）
  industry_understanding: string
  unique_views: string
  target_pains: string
  
  // 其他已有字段
  benchmark_accounts: string[]
  content_style: string
  taboos: string[]
}

/**
 * 数据库项目表的完整结构
 * 对应后端 Project 模型的所有字段
 */
export interface ProjectModel {
  id: string
  user_id: string
  name: string
  industry: string
  avatar_letter: string
  avatar_color: string
  persona_settings: PersonaSettingsModel
  created_at: string
  updated_at: string
  is_active: boolean
}

// ============== 表单数据类型 ==============

/**
 * 统一的表单数据结构
 * 用于创建和编辑，包含所有可编辑字段
 * 对应前端表单的所有输入项（扁平化结构，方便表单使用）
 */
export interface ProjectFormData {
  // 项目基本信息
  name: string
  industry: string
  
  // 人设配置（扁平化，方便表单使用）
  // 基础字段
  tone: string
  catchphrase: string
  target_audience: string
  introduction: string
  keywords: string[]
  
  // 扩展字段
  industry_understanding: string
  unique_views: string
  target_pains: string
  
  // 其他字段
  benchmark_accounts: string[]
  content_style: string
  taboos: string[]
}

/**
 * IP收集表单数据（用于多步骤收集）
 * 继承自 ProjectFormData，但只包含收集步骤中涉及的字段
 * 用于 IPCollectDialog 组件
 */
export type IPCollectFormData = Pick<ProjectFormData, 
  'name' | 
  'industry' | 
  'industry_understanding' | 
  'unique_views' | 
  'target_audience' | 
  'target_pains' | 
  'tone' | 
  'introduction' | 
  'catchphrase' | 
  'keywords'
>

// ============== 向后兼容的类型别名 ==============

/**
 * 向后兼容：PersonaSettings 类型别名
 * 保持与旧代码的兼容性
 */
export type PersonaSettings = PersonaSettingsModel

/**
 * 向后兼容：Project 类型别名
 * 保持与旧代码的兼容性
 */
export type Project = ProjectModel








