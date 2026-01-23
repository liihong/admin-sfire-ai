/**
 * 日期工具函数
 */

/**
 * 格式化日期为相对时间或绝对时间
 * @param dateStr 日期字符串或 Date 对象
 * @returns 格式化后的日期字符串
 */
export function formatDate(dateStr: string | Date): string {
  if (!dateStr) return ''
  
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  // 超过7天，返回月/日格式
  return `${date.getMonth() + 1}/${date.getDate()}`
}

/**
 * 格式化日期为指定格式
 * @param dateStr 日期字符串或 Date 对象
 * @param format 格式字符串，如 'YYYY-MM-DD'
 * @returns 格式化后的日期字符串
 */
export function formatDateCustom(dateStr: string | Date, format: string = 'YYYY-MM-DD'): string {
  if (!dateStr) return ''
  
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 获取时间戳（秒）
 */
export function getTimestamp(date?: Date): number {
  return Math.floor((date || new Date()).getTime() / 1000)
}
