/**
 * 统一的 Storage 操作工具
 * 封装 uni.storage 操作，提供类型安全和错误处理
 */

/**
 * Storage 工具类
 */
class StorageUtil {
  /**
   * 获取存储的值
   * @param key 存储键名
   * @param defaultValue 默认值（当键不存在时返回）
   * @returns 存储的值或默认值
   */
  get<T>(key: string, defaultValue: T | null = null): T | null {
    try {
      const stored = uni.getStorageSync(key)
      if (stored === null || stored === undefined || stored === '') {
        return defaultValue
      }
      
      // 如果存储的值已经是对象/数组/数字/布尔值，直接返回
      if (typeof stored !== 'string') {
        return stored as T
      }
      
      // 如果是字符串，尝试 JSON.parse
      // 如果解析失败，说明是纯字符串，直接返回
      try {
        return JSON.parse(stored) as T
      } catch {
        // JSON.parse 失败，说明是纯字符串，直接返回
        return stored as T
      }
    } catch (error) {
      // 静默失败，不输出日志（根据要求清理所有日志）
      return defaultValue
    }
  }

  /**
   * 设置存储的值
   * @param key 存储键名
   * @param value 要存储的值
   * @returns 是否设置成功
   */
  set<T>(key: string, value: T): boolean {
    try {
      uni.setStorageSync(key, JSON.stringify(value))
      return true
    } catch (error) {
      // 静默失败，不输出日志
      return false
    }
  }

  /**
   * 移除存储的值
   * @param key 存储键名
   * @returns 是否移除成功
   */
  remove(key: string): boolean {
    try {
      uni.removeStorageSync(key)
      return true
    } catch (error) {
      // 静默失败，不输出日志
      return false
    }
  }

  /**
   * 检查键是否存在
   * @param key 存储键名
   * @returns 是否存在
   */
  has(key: string): boolean {
    try {
      const value = uni.getStorageSync(key)
      return value !== null && value !== undefined && value !== ''
    } catch {
      return false
    }
  }

  /**
   * 清空所有存储（谨慎使用）
   */
  clear(): void {
    try {
      uni.clearStorageSync()
    } catch {
      // 静默失败
    }
  }
}

export const storage = new StorageUtil()

