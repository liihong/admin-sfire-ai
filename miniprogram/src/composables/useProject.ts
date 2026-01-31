/**
 * 项目相关逻辑 Composable
 * 提取项目初始化、加载、切换等通用逻辑
 */

import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { fetchProjects } from '@/api/project'
import type { Project } from '@/api/project'

export function useProject(options?: {
  autoLoad?: boolean
  projectId?: string | number
}) {
  const projectStore = useProjectStore()
  const isLoading = ref(false)
  const activeProject = computed(() => projectStore.activeProject)
  const projectList = computed(() => projectStore.projectList)
  
  // 加载项目列表
  async function loadProjects() {
    isLoading.value = true
    try {
      const response = await fetchProjects()
      projectStore.setProjectList(response.projects, response.active_project_id)
      return response
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  // 初始化项目（从 URL 参数或 store）
  async function initProject(projectId?: string | number) {
    const pages = getCurrentPages()
    interface PageInstance {
      options?: Record<string, string>
    }
    const currentPage = pages[pages.length - 1] as PageInstance | undefined
    const urlParams = currentPage?.options || {}
    const urlProjectId = projectId || urlParams.id
    
    // 如果需要加载特定项目或没有激活项目，先加载项目列表
    if (urlProjectId || !activeProject.value) {
      try {
        const response = await loadProjects()
        
        // 如果 URL 中指定了项目 ID，设置为激活项目
        if (urlProjectId) {
          const targetProject = response.projects.find(p => String(p.id) === String(urlProjectId))
          if (targetProject) {
            projectStore.setActiveProjectLocal(targetProject)
          } else {
            uni.showToast({ title: '项目不存在', icon: 'none' })
            uni.navigateBack()
            return false
          }
        } else if (!projectStore.hasActiveProject) {
          // 如果没有指定项目 ID 且没有激活项目
          if (projectStore.projectCount === 0) {
            uni.redirectTo({ url: '/pages/project/list' })
            return false
          }
          if (projectStore.projectCount > 0) {
            const firstProject = projectStore.projectList[0]
            projectStore.setActiveProjectLocal(firstProject)
          }
        }
      } catch (error) {
        console.error('Failed to init project:', error)
        if (projectStore.projectCount === 0) {
          uni.redirectTo({ url: '/pages/project/list' })
          return false
        }
      }
    }
    
    return true
  }
  
  // 切换项目
  function switchProject(project: Project) {
    projectStore.setActiveProjectLocal(project)
    uni.showToast({
      title: `已切换到：${project.name}`,
      icon: 'success'
    })
  }
  
  // 自动初始化（如果启用）
  if (options?.autoLoad !== false) {
    onMounted(() => {
      initProject(options?.projectId)
    })
  }
  
  return {
    activeProject,
    projectList,
    isLoading,
    loadProjects,
    initProject,
    switchProject
  }
}
