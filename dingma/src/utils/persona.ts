import type { PersonaSettings, Project } from '@/types/project'

/** 人设档案是否已填写核心字段（与「我的」页校验一致） */
export function isPersonaProfileComplete(project: Project | null | undefined): boolean {
  if (!project) return false
  const ps = project.persona_settings
  if (!ps) return false
  return !!(
    project.name?.trim() &&
    ps.ip_city?.trim() &&
    ps.ip_identityTag?.trim() &&
    ps.ip_experience?.trim() &&
    ps.cl_mainProducts?.trim()
  )
}

/** 对话页顶部展示：IP 实时关联：地区 · 姓名 */
export function buildPersonaContextLabel(project: Project | null | undefined): string {
  if (!project) return ''
  const ps = project.persona_settings
  const city = ps?.ip_city?.trim() || ''
  const name = project.name?.trim() || ps?.ip_name?.trim() || ''
  if (city && name) return `${city} · ${name}`
  return city || name
}

/** 解析对话请求使用的 project_id */
export function resolveChatProjectId(project: Project | null | undefined): number | undefined {
  if (!project?.id) return undefined
  const id = parseInt(String(project.id), 10)
  return Number.isNaN(id) ? undefined : id
}

/** 前端侧人设上下文摘要（project_id 未就绪时的兜底，正常走后端 project_id 注入） */
export function buildPersonaPromptFromSettings(
  project: Project | null | undefined,
  settings?: PersonaSettings
): string {
  if (!project && !settings) return ''
  const ps = settings || project?.persona_settings
  if (!ps) return ''
  const parts: string[] = []
  const name = project?.name?.trim() || ps.ip_name?.trim()
  if (name) parts.push(`IP名称：${name}`)
  if (ps.ip_city?.trim()) parts.push(`所在地区：${ps.ip_city.trim()}`)
  if (ps.ip_identityTag?.trim()) parts.push(`身份标签：${ps.ip_identityTag.trim()}`)
  if (ps.ip_experience?.trim()) parts.push(`经历介绍：${ps.ip_experience.trim()}`)
  if (ps.cl_mainProducts?.trim()) parts.push(`主要产品：${ps.cl_mainProducts.trim()}`)
  if (ps.style_tones?.trim()) parts.push(`语气风格：${ps.style_tones.trim()}`)
  if (ps.cl_targetPopulation?.trim()) parts.push(`目标人群：${ps.cl_targetPopulation.trim()}`)
  if (ps.keywords?.length) parts.push(`关键词：${ps.keywords.join('、')}`)
  return parts.join('\n')
}
