/**
 * 远程文档（PDF 等）在小程序内预览
 * 使用 downloadFile + openDocument，关闭预览后可返回小程序页面
 */

function isPdfUrl(url: string): boolean {
  const trimmed = url.trim()
  if (!trimmed) return false
  try {
    const path = new URL(trimmed).pathname.toLowerCase()
    return path.endsWith('.pdf')
  } catch {
    return /\.pdf(\?|#|$)/i.test(trimmed)
  }
}

export { isPdfUrl }

export function openRemotePdf(
  url: string,
  options?: { loadingTitle?: string; failToast?: string }
): void {
  const loadingTitle = options?.loadingTitle ?? '加载中…'
  const failToast = options?.failToast ?? '文档打开失败，请稍后重试'

  uni.showLoading({ title: loadingTitle, mask: true })

  uni.downloadFile({
    url: url.trim(),
    success(res) {
      if (res.statusCode !== 200 || !res.tempFilePath) {
        uni.hideLoading()
        uni.showToast({ title: failToast, icon: 'none' })
        return
      }
      uni.openDocument({
        filePath: res.tempFilePath,
        fileType: 'pdf',
        showMenu: true,
        success() {
          uni.hideLoading()
        },
        fail() {
          uni.hideLoading()
          uni.showToast({ title: failToast, icon: 'none' })
        }
      })
    },
    fail() {
      uni.hideLoading()
      uni.showToast({ title: failToast, icon: 'none' })
    }
  })
}
