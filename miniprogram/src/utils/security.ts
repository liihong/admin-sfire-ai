/**
 * 微信内容安全检测工具
 * 使用微信官方的 msgSecCheck 接口检测文本内容是否违规
 */

import { request } from './request'

/**
 * 安全检测结果
 */
export interface SecurityCheckResult {
  /** 是否通过检测（true: 通过，false: 违规） */
  pass: boolean
  /** 错误信息（如果违规） */
  message?: string
  /** 错误代码 */
  errCode?: number
}

/**
 * 微信内容安全检测
 * 
 * @param content 需要检测的文本内容
 * @param options 可选配置
 * @returns 检测结果
 * 
 * @example
 * ```typescript
 * const result = await msgSecCheck('用户输入的提示词')
 * if (!result.pass) {
 *   uni.showToast({ title: result.message, icon: 'none' })
 *   return
 * }
 * // 继续后续流程
 * ```
 */
export async function msgSecCheck(
  content: string,
  options?: {
    /** 是否显示 loading（默认 false） */
    showLoading?: boolean
    /** loading 提示文字 */
    loadingText?: string
  }
): Promise<SecurityCheckResult> {
  // 空内容直接通过
  if (!content || !content.trim()) {
    return { pass: true }
  }

  try {
    // 调用后端 API 进行安全检测
    // 后端需要调用微信的 msgSecCheck 接口
    const response = await request<{
      pass: boolean
      message?: string
      errCode?: number
    }>({
      url: '/api/v1/client/security/msg-sec-check',
      method: 'POST',
      data: {
        content: content.trim()
      },
      showLoading: options?.showLoading || false,
      loadingText: options?.loadingText || '内容检测中...'
    })

    // 如果请求成功
    if (response.code === 200 && response.data) {
      const { pass, message, errCode } = response.data
      
      if (pass) {
        return { pass: true }
      } else {
        return {
          pass: false,
          message: message || '内容包含违规信息，请修改后重试',
          errCode
        }
      }
    }

    // 如果后端返回错误，默认通过（避免因检测服务异常影响正常使用）
    // 也可以根据实际需求改为返回失败
    console.warn('安全检测服务异常，默认通过:', response.msg)
    return {
      pass: true,
      message: '安全检测服务暂时不可用，已跳过检测'
    }
  } catch (error: any) {
    // 网络错误或其他异常，默认通过（避免因检测服务异常影响正常使用）
    console.error('安全检测失败:', error)
    return {
      pass: true,
      message: '安全检测服务暂时不可用，已跳过检测'
    }
  }
}

/**
 * 批量检测多条内容
 * 
 * @param contents 需要检测的文本内容数组
 * @param options 可选配置
 * @returns 检测结果（如果任何一条违规，返回失败）
 */
export async function msgSecCheckBatch(
  contents: string[],
  options?: {
    showLoading?: boolean
    loadingText?: string
  }
): Promise<SecurityCheckResult> {
  if (!contents || contents.length === 0) {
    return { pass: true }
  }

  // 过滤空内容
  const validContents = contents.filter(c => c && c.trim())
  if (validContents.length === 0) {
    return { pass: true }
  }

  // 合并所有内容进行检测（微信接口支持）
  const combinedContent = validContents.join('\n')
  return await msgSecCheck(combinedContent, options)
}

/**
 * 检测消息列表中的用户输入
 * 只检测 role 为 'user' 的消息内容
 * 
 * @param messages 消息列表
 * @param options 可选配置
 * @returns 检测结果
 */
export async function checkUserMessages(
  messages: Array<{ role: string; content: string }>,
  options?: {
    showLoading?: boolean
    loadingText?: string
  }
): Promise<SecurityCheckResult> {
  if (!messages || messages.length === 0) {
    return { pass: true }
  }

  // 提取所有用户消息
  const userContents = messages
    .filter(msg => msg.role === 'user' && msg.content && msg.content.trim())
    .map(msg => msg.content.trim())

  if (userContents.length === 0) {
    return { pass: true }
  }

  return await msgSecCheckBatch(userContents, options)
}

