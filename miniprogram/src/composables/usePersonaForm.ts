/**
 * 人设表单逻辑 Composable
 * 
 * 统一管理创建和编辑两种模式的人设表单逻辑
 * 
 * 使用场景：
 * - 创建模式：IPCollectDialog 组件（多步骤收集）
 * - 编辑模式：PersonaDrawer 组件（单表单编辑）
 * 
 * 数据流转：
 * - 创建流程：formData → formDataToCreateRequest() → createProject() → ProjectModel → store
 * - 编辑流程：ProjectModel → modelToFormData() → formData → formDataToUpdateRequest() → updateProject() → ProjectModel → store
 */

import { ref, reactive, watch, computed, type Ref } from 'vue'
import { useProjectStore, TONE_OPTIONS, INDUSTRY_OPTIONS } from '@/stores/project'
import { createProject, updateProject, getProjectOptions } from '@/api/project'
import type { Project } from '@/types/project'
import type { ProjectFormData } from '@/types/project'
import { modelToFormData, formDataToCreateRequest, formDataToUpdateRequest, getDefaultFormData } from '@/utils/project'
import type { DictOption } from '@/api/project'

export type PersonaFormMode = 'create' | 'edit'

export interface UsePersonaFormOptions {
  mode: PersonaFormMode
  project?: Ref<Project | null>
  autoSync?: boolean // 是否自动同步项目数据到表单（仅编辑模式）
}

/**
 * 人设表单 Composable
 * 
 * @param options 配置选项
 * @returns 表单状态和方法
 */
export function usePersonaForm(options: UsePersonaFormOptions) {
  const { mode, project, autoSync = true } = options
  const projectStore = useProjectStore()
  const isSaving = ref(false)
  const isLoadingOptions = ref(false)
  
  // 统一的表单数据（扁平结构）
  const formData = reactive<ProjectFormData>(getDefaultFormData())
  
  // 选项数据
  const industryOptions = ref<DictOption[]>([])
  const toneOptions = ref<DictOption[]>([])
  
  // 初始化表单数据
  function initFormData() {
    if (mode === 'edit' && project?.value) {
      // 编辑模式：从项目同步数据
      const data = modelToFormData(project.value)
      Object.assign(formData, data)
    } else {
      // 创建模式：使用默认值
      const defaultData = getDefaultFormData()
      Object.assign(formData, defaultData)
    }
  }
  
  // 同步表单数据从项目（编辑模式）
  function syncFormFromProject() {
    if (mode === 'edit' && project?.value) {
      const data = modelToFormData(project.value)
      Object.assign(formData, data)
    }
  }
  
  // 加载选项数据（行业和语气）
  async function loadOptions() {
    if (isLoadingOptions.value) return
    
    isLoadingOptions.value = true
    try {
      const options = await getProjectOptions()
      industryOptions.value = options.industries || []
      toneOptions.value = options.tones || []
    } catch (error) {
      console.error('加载选项失败:', error)
      // 使用 store 中的默认选项
      industryOptions.value = INDUSTRY_OPTIONS.map(v => ({ label: v, value: v }))
      toneOptions.value = TONE_OPTIONS.map(v => ({ label: v, value: v }))
    } finally {
      isLoadingOptions.value = false
    }
  }
  
  // 验证表单数据
  function validateForm(): { valid: boolean; message?: string } {
    if (!formData.name.trim()) {
      return { valid: false, message: '请输入项目名称' }
    }
    if (!formData.industry) {
      return { valid: false, message: '请选择行业赛道' }
    }
    // 可以根据需要添加更多验证规则
    return { valid: true }
  }
  
  // 创建项目
  async function createProjectFromForm(): Promise<Project | null> {
    if (mode !== 'create' || isSaving.value) return null
    
    const validation = validateForm()
    if (!validation.valid) {
      throw new Error(validation.message || '表单验证失败')
    }
    
    isSaving.value = true
    try {
      const requestData = formDataToCreateRequest(formData)
      const result = await createProject(requestData)
      
      // 更新 store 状态
      projectStore.upsertProject(result)
      
      return result
    } catch (error) {
      console.error('创建项目失败:', error)
      throw error
    } finally {
      isSaving.value = false
    }
  }
  
  // 更新项目
  async function updateProjectFromForm(): Promise<Project | null> {
    if (mode !== 'edit' || !project?.value || isSaving.value) return null
    
    const validation = validateForm()
    if (!validation.valid) {
      throw new Error(validation.message || '表单验证失败')
    }
    
    isSaving.value = true
    try {
      const requestData = formDataToUpdateRequest(formData)
      const result = await updateProject(project.value.id, requestData)
      
      // 更新 store 状态
      projectStore.upsertProject(result)
      // 如果更新的是当前激活的项目，更新激活项目状态
      if (project.value.id === result.id) {
        projectStore.setActiveProjectLocal(result)
      }
      
      return result
    } catch (error) {
      console.error('更新项目失败:', error)
      throw error
    } finally {
      isSaving.value = false
    }
  }
  
  // 统一保存方法（根据模式自动选择创建或更新）
  async function saveForm(): Promise<Project | null> {
    if (mode === 'create') {
      return await createProjectFromForm()
    } else {
      return await updateProjectFromForm()
    }
  }
  
  // 重置表单
  function resetForm() {
    const defaultData = getDefaultFormData()
    Object.assign(formData, defaultData)
  }
  
  // 监听项目变化，同步表单（仅编辑模式且启用自动同步）
  if (mode === 'edit' && autoSync && project) {
    watch(project, () => {
      syncFormFromProject()
    }, { immediate: true })
  }
  
  // 初始化
  initFormData()
  loadOptions()
  
  return {
    // 表单数据
    formData,
    
    // 状态
    isSaving,
    isLoadingOptions,
    
    // 选项数据
    industryOptions,
    toneOptions,
    
    // 方法
    syncFormFromProject,
    loadOptions,
    validateForm,
    createProjectFromForm,
    updateProjectFromForm,
    saveForm,
    resetForm,
    initFormData
  }
}
