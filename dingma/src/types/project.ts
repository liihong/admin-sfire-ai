/**
 * 项目与人设类型（与后端 persona_settings JSON 一致）
 */

export interface PersonaSettingsModel {
  ip_name: string
  ip_age: string
  ip_city: string
  ip_industry: string
  ip_identityTag: string
  ip_experience: string
  cl_mainProducts: string
  cl_targetPopulation: string
  cl_painPoints: string
  cl_advantages: string
  cl_feedback: string
  style_tones: string
  style_mantra: string
  keywords: string[]
}

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

export interface ProjectFormData {
  name: string
  industry: string
  ip_name: string
  ip_age: string
  ip_city: string
  ip_industry: string
  ip_identityTag: string
  ip_experience: string
  cl_mainProducts: string
  cl_targetPopulation: string
  cl_painPoints: string
  cl_advantages: string
  cl_feedback: string
  style_tones: string
  style_mantra: string
  keywords: string[]
}

export type IPCollectFormData = Pick<
  ProjectFormData,
  | 'name'
  | 'industry'
  | 'ip_age'
  | 'ip_city'
  | 'ip_identityTag'
  | 'cl_mainProducts'
  | 'cl_advantages'
  | 'cl_feedback'
  | 'style_tones'
  | 'style_mantra'
  | 'cl_targetPopulation'
  | 'cl_painPoints'
  | 'ip_experience'
  | 'keywords'
>

export type PersonaSettings = PersonaSettingsModel
export type Project = ProjectModel
