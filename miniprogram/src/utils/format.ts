/**
 * 格式化工具函数
 */

/**
 * 格式化数字，添加千分位
 * @param num 数字
 * @returns 格式化后的字符串
 */
export function formatNumber(num: number): string {
  if (typeof num !== 'number') return String(num)
  return num.toLocaleString('zh-CN')
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * 格式化手机号（中间4位用*代替）
 */
export function formatPhone(phone: string): string {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 截断文本并添加省略号
 * @param text 文本
 * @param length 最大长度
 * @returns 截断后的文本
 */
export function truncateText(text: string, length: number): string {
  if (!text || text.length <= length) return text
  return text.slice(0, length) + '...'
}
