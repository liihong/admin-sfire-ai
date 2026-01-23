/**
 * 人设表单逻辑 Composable
 * 提取人设表单的通用逻辑
 */

import { ref, reactive, watch, type Ref } from 'vue'
import { useProjectStore, DEFAULT_PERSONA_SETTINGS, TONE_OPTIONS, INDUSTRY_OPTIONS, type PersonaSettings } from '@/stores/project'
import { updateProject } from '@/api/project'
import type { Project } from '@/api/project'

export function usePersonaForm(project: Ref<Project | null>) {
  const projectStore = useProjectStore()
  const isSaving = ref(false)
  
  // 编辑表单
  const editForm = reactive({
    name: '',
    industry: '通用',
    persona: {
      tone: '专业亲和',
      catchphrase: '',
      target_audience: '',
      benchmark_accounts: [] as string[],
      content_style: '',
      taboos: [] as string[],
      keywords: [] as string[],
      introduction: ''
    } as PersonaSettings
  })
  
  // 同步表单数据从项目
  function syncFormFromProject() {
    if (project.value) {
      editForm.name = project.value.name || ''
      editForm.industry = project.value.industry || '通用'
      const personaSettings = project.value.persona_settings || {}
      editForm.persona = {
        tone: personaSettings.tone || DEFAULT_PERSONA_SETTINGS.tone,
        catchphrase: personaSettings.catchphrase || DEFAULT_PERSONA_SETTINGS.catchphrase,
        target_audience: personaSettings.target_audience || DEFAULT_PERSONA_SETTINGS.target_audience,
        benchmark_accounts: personaSettings.benchmark_accounts || [...DEFAULT_PERSONA_SETTINGS.benchmark_accounts],
        content_style: personaSettings.content_style || DEFAULT_PERSONA_SETTINGS.content_style,
        taboos: personaSettings.taboos || [...DEFAULT_PERSONA_SETTINGS.taboos],
        keywords: personaSettings.keywords || [...DEFAULT_PERSONA_SETTINGS.keywords],
        introduction: personaSettings.introduction || DEFAULT_PERSONA_SETTINGS.introduction
      }
    }
  }
  
  // 保存人设设置
  async function savePersonaSettings(): Promise<boolean> {
    if (!project.value || isSaving.value) return false
    
    isSaving.value = true
    try {
      const result = await updateProject(project.value.id, {
        name: editForm.name,
        industry: editForm.industry,
        persona_settings: editForm.persona
      })
      
      // 更新 store 状态
      projectStore.upsertProject(result)
      // 如果更新的是当前激活的项目，更新激活项目状态
      if (project.value.id === result.id) {
        projectStore.setActiveProjectLocal(result)
      }
      
      return true
    } catch (error) {
      console.error('Failed to update project:', error)
      return false
    } finally {
      isSaving.value = false
    }
  }
  
  // 监听项目变化，同步表单
  watch(project, () => {
    syncFormFromProject()
  }, { immediate: true })
  
  return {
    editForm,
    isSaving,
    syncFormFromProject,
    savePersonaSettings,
    toneOptions: TONE_OPTIONS,
    industryOptions: INDUSTRY_OPTIONS
  }
}
