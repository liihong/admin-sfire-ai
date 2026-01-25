/**
 * Pinia Store 导出入口
 */

export { useSettingsStore, MODEL_LIST } from './settings'
export type { ModelType, ModelConfig } from './settings'

export { useAuthStore } from './auth'
export type { UserInfo } from './auth'

export { useProjectStore, INDUSTRY_OPTIONS, TONE_OPTIONS, DEFAULT_PERSONA_SETTINGS, DEFAULT_INDUSTRY } from './project'
export type { Project, PersonaSettings, ProjectCreateRequest, ProjectUpdateRequest } from './project'

