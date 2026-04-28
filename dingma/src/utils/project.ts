import type { ProjectModel, PersonaSettingsModel, ProjectFormData } from '@/types/project'
import type {
  ProjectCreateRequest,
  ProjectUpdateRequest,
  IPCollectFormData,
  IPReportRequest
} from '@/api/project'

const DEFAULT_PERSONA: PersonaSettingsModel = {
  ip_name: '',
  ip_age: '',
  ip_city: '',
  ip_industry: '',
  ip_identityTag: '',
  ip_experience: '',
  cl_mainProducts: '',
  cl_targetPopulation: '',
  cl_painPoints: '',
  cl_advantages: '',
  cl_feedback: '',
  style_tones: '专业亲和',
  style_mantra: '',
  keywords: []
}

function mergePersona(base: PersonaSettingsModel, name: string, industry: string): PersonaSettingsModel {
  return {
    ...DEFAULT_PERSONA,
    ...base,
    ip_name: base.ip_name || name || '',
    ip_industry: base.ip_industry || industry || '通用',
    keywords: Array.isArray(base.keywords) ? [...base.keywords] : []
  }
}

export function modelToFormData(project: ProjectModel | null): ProjectFormData {
  if (!project) return getDefaultFormData()
  const p = mergePersona(project.persona_settings || DEFAULT_PERSONA, project.name, project.industry)
  return {
    name: project.name || '',
    industry: project.industry || '通用',
    ...p
  }
}

function buildPersonaFromForm(formData: ProjectFormData): PersonaSettingsModel {
  const name = formData.name.trim()
  return {
    ip_name: (formData.ip_name && formData.ip_name.trim()) ? formData.ip_name.trim() : name,
    ip_age: formData.ip_age?.trim() || '',
    ip_city: formData.ip_city?.trim() || '',
    ip_industry: formData.industry || '通用',
    ip_identityTag: formData.ip_identityTag?.trim() || '',
    ip_experience: formData.ip_experience?.trim() || '',
    cl_mainProducts: formData.cl_mainProducts?.trim() || '',
    cl_targetPopulation: formData.cl_targetPopulation?.trim() || '',
    cl_painPoints: formData.cl_painPoints?.trim() || '',
    cl_advantages: formData.cl_advantages?.trim() || '',
    cl_feedback: formData.cl_feedback?.trim() || '',
    style_tones: formData.style_tones?.trim() || '专业亲和',
    style_mantra: formData.style_mantra?.trim() || '',
    keywords: (formData.keywords || []).filter(k => k && k.trim())
  }
}

export function formDataToCreateRequest(formData: ProjectFormData): ProjectCreateRequest {
  const persona = buildPersonaFromForm(formData)
  return {
    name: formData.name.trim(),
    industry: formData.industry || undefined,
    persona_settings: persona
  }
}

export function formDataToUpdateRequest(formData: ProjectFormData): ProjectUpdateRequest {
  const persona = buildPersonaFromForm(formData)
  return {
    name: formData.name.trim(),
    industry: formData.industry,
    persona_settings: persona
  }
}

export function getDefaultFormData(): ProjectFormData {
  return {
    name: '',
    industry: '通用',
    ...DEFAULT_PERSONA,
    ip_industry: '通用'
  }
}

export function formDataToIPCollectFormData(formData: ProjectFormData): IPCollectFormData {
  return {
    name: formData.name,
    industry: formData.industry,
    ip_age: formData.ip_age || '',
    ip_city: formData.ip_city || '',
    ip_identityTag: formData.ip_identityTag || '',
    cl_mainProducts: formData.cl_mainProducts || '',
    cl_advantages: formData.cl_advantages || '',
    cl_feedback: formData.cl_feedback || '',
    style_tones: formData.style_tones || '',
    style_mantra: formData.style_mantra || '',
    cl_targetPopulation: formData.cl_targetPopulation || '',
    cl_painPoints: formData.cl_painPoints || '',
    ip_experience: formData.ip_experience || '',
    keywords: formData.keywords || []
  }
}

export function ipCollectFormDataToProjectFormData(
  collected: IPCollectFormData,
  defaults?: Partial<ProjectFormData>
): ProjectFormData {
  const d = defaults || {}
  return {
    name: collected.name?.trim() || d.name || '未命名项目',
    industry: collected.industry?.trim() || d.industry || '通用',
    ip_name: d.ip_name || collected.name?.trim() || '',
    ip_age: collected.ip_age ?? d.ip_age ?? '',
    ip_city: collected.ip_city ?? d.ip_city ?? '',
    ip_industry: collected.industry?.trim() || d.industry || '通用',
    ip_identityTag: collected.ip_identityTag ?? d.ip_identityTag ?? '',
    ip_experience: collected.ip_experience || d.ip_experience || '',
    cl_mainProducts: collected.cl_mainProducts ?? d.cl_mainProducts ?? '',
    cl_targetPopulation: collected.cl_targetPopulation || d.cl_targetPopulation || '',
    cl_painPoints: collected.cl_painPoints || d.cl_painPoints || '',
    cl_advantages: collected.cl_advantages || d.cl_advantages || '',
    cl_feedback: collected.cl_feedback || d.cl_feedback || '',
    style_tones: collected.style_tones || d.style_tones || '专业亲和',
    style_mantra: collected.style_mantra || d.style_mantra || '',
    keywords: collected.keywords || d.keywords || []
  }
}

/** 报告里的人格标签一般 3 条，写入 persona_settings.keywords */
export const CREATIVE_KEYWORDS_FROM_REPORT_MAX = 3

export function personaTagsToCreativeKeywords(tags: string[] | undefined | null): string[] {
  if (!tags?.length) return []
  return tags.map(t => String(t).trim()).filter(Boolean).slice(0, CREATIVE_KEYWORDS_FROM_REPORT_MAX)
}

/** 与报告页一致：从采集表单拼「生成 IP 报告」请求体 */
export function buildIPReportRequestFromCollectForm(
  form: Pick<
    ProjectFormData,
    | 'name'
    | 'industry'
    | 'ip_experience'
    | 'style_tones'
    | 'cl_targetPopulation'
    | 'cl_painPoints'
    | 'keywords'
    | 'cl_advantages'
    | 'cl_feedback'
    | 'style_mantra'
  >
): IPReportRequest {
  return {
    name: (form.name ?? '').trim(),
    industry: (form.industry ?? '').trim(),
    ip_experience: form.ip_experience || '',
    style_tones: form.style_tones || '',
    cl_targetPopulation: form.cl_targetPopulation || '',
    cl_painPoints: form.cl_painPoints || '',
    keywords: form.keywords || [],
    cl_advantages: form.cl_advantages || '',
    cl_feedback: form.cl_feedback || '',
    style_mantra: form.style_mantra || ''
  }
}
