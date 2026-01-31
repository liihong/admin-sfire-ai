/**
 * 导航逻辑 Composable
 * 统一处理页面导航逻辑
 */

export function useNavigation() {
  /**
   * 导航到指定路由
   * @param route 路由路径
   * @param showTip 如果路由为空，是否显示提示
   */
  function navigateTo(route: string, showTip: boolean = true) {
    if (!route) {
      if (showTip) {
        uni.showToast({ title: '功能即将上线', icon: 'none' })
      }
      return
    }
    uni.navigateTo({ url: route })
  }
  
  /**
   * 返回上一页
   */
  function goBack() {
    uni.navigateBack({
      fail: () => {
        uni.switchTab({ url: '/pages/index/index' })
      }
    })
  }
  
  /**
   * 跳转到项目列表
   */
  function goToProjectList() {
    uni.navigateTo({ url: '/pages/project/list' })
  }
  
  /**
   * 跳转到项目仪表盘
   * @param projectId 项目ID（可选）
   * @param editMode 是否编辑模式
   */
  function goToProjectDashboard(projectId?: string | number, editMode: boolean = false) {
    let url = '/pages/project/index'
    const params: string[] = []
    
    if (projectId) {
      params.push(`id=${projectId}`)
    }
    if (editMode) {
      params.push('edit=true')
    }
    
    if (params.length > 0) {
      url += '?' + params.join('&')
    }
    
    uni.navigateTo({ url })
  }
  
  /**
   * 处理分类点击
   * @param category 分类标识
   * @param categoryMap 分类映射表
   */
  function handleCategoryClick(
    category: string,
    categoryMap: Record<string, string> = {
      story: '讲故事',
      opinion: '聊观点',
      process: '晒过程',
      knowledge: '教知识',
      hotspot: '蹭热点'
    }
  ) {
    const categoryName = categoryMap[category] || category
    uni.showToast({ title: `已选择：${categoryName}`, icon: 'none' })
    // 导航到对应的分类页面（功能待实现）
  }
  
  return {
    navigateTo,
    goBack,
    goToProjectList,
    goToProjectDashboard,
    handleCategoryClick
  }
}
