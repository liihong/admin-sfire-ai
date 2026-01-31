/**
 * 通用工具函数
 */

/**
 * 防抖函数（优化版，支持立即执行）
 * @param func 要防抖的函数
 * @param wait 等待时间（毫秒）
 * @param immediate 是否立即执行（默认 false）
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null
  
  return function (this: unknown, ...args: Parameters<T>) {
    const context = this
    const callNow = immediate && !timeout
    
    if (timeout) {
      clearTimeout(timeout)
    }
    
    timeout = setTimeout(() => {
      timeout = null
      if (!immediate) {
        func.apply(context, args)
      }
    }, wait)
    
    if (callNow) {
      func.apply(context, args)
    }
  }
}

/**
 * 节流函数（优化版）
 * @param func 要节流的函数
 * @param wait 等待时间（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null
  let previous = 0
  
  return function (this: unknown, ...args: Parameters<T>) {
    const context = this
    const now = Date.now()
    const remaining = wait - (now - previous)
    
    if (remaining <= 0 || remaining > wait) {
      if (timeout) {
        clearTimeout(timeout)
        timeout = null
      }
      previous = now
      func.apply(context, args)
    } else if (!timeout) {
      timeout = setTimeout(() => {
        previous = Date.now()
        timeout = null
        func.apply(context, args)
      }, remaining)
    }
  }
}

/**
 * 深拷贝（优化版，使用结构化克隆或 JSON 方法）
 * @param obj 要拷贝的对象
 * @returns 拷贝后的对象
 */
export function deepClone<T>(obj: T): T {
  // 处理 null 和 undefined
  if (obj === null || obj === undefined) {
    return obj
  }
  
  // 处理基本类型
  if (typeof obj !== 'object') {
    return obj
  }
  
  // 使用结构化克隆（如果支持）
  if (typeof structuredClone !== 'undefined') {
    try {
      return structuredClone(obj)
    } catch {
      // 降级到 JSON 方法
    }
  }
  
  // 处理 Date
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T
  }
  
  // 处理 Array
  if (Array.isArray(obj)) {
    return obj.map(item => deepClone(item)) as unknown as T
  }
  
  // 处理普通对象（使用 JSON 方法，性能更好）
  try {
    return JSON.parse(JSON.stringify(obj)) as T
  } catch {
    // JSON 方法失败时，使用递归方法
    const clonedObj = {} as T
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
}

/**
 * 判断是否为空值（优化类型）
 * @param value 要判断的值
 * @returns 是否为空
 */
export function isEmpty<T>(value: T | null | undefined): value is null | undefined {
  if (value === null || value === undefined) return true
  if (typeof value === 'string' && value.trim() === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  if (typeof value === 'object' && Object.keys(value).length === 0) return true
  return false
}

/**
 * 生成唯一ID（优化版，使用更安全的算法）
 * @returns 唯一ID字符串
 */
export function generateId(): string {
  // 使用 crypto API（如果可用）
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  
  // 降级方案：改进的算法
  const timestamp = Date.now().toString(36)
  const randomPart = Math.random().toString(36).substring(2, 11)
  const counter = (typeof performance !== 'undefined' && performance.now 
    ? performance.now() 
    : Math.random()).toString(36).substring(2, 6)
  return `${timestamp}-${randomPart}-${counter}`
}
