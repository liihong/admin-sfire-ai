/**
 * Generate API - 生成内容相关接口
 */
import { request } from '@/utils/request'
import { useAuthStore } from '@/stores/auth'

const BASE_URL = __API_BASE_URL__

export interface GenerateRequest {
  project_id?: number
  agent_type?: string
  messages: Array<{role: string, content: string}>
  model_type?: string
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

export interface GenerateResponse {
  success: boolean
  content: string
  agent_type: string
  model_type: string
}

export interface CopywritingRequest {
  content: string
  agent_type?: string
  project_id?: number
  model_type?: string
}

export interface CopywritingResponse {
  success: boolean
  content: string
  agent_type: string
  model_type: string
}

export interface ChatRequest {
  agent_type: string
  conversation_id?: number
  messages: Array<{ role: string, content: string }>
  project_id?: number
  stream: boolean
}

export interface ChatResponseData {
  content?: string
  conversation_id?: number
  [key: string]: unknown
}

export interface StreamChatCallbacks {
  onChunk?: (content: string) => void
  onConversationId?: (conversationId: number) => void
  onDone?: () => void
  onError?: (error: string) => void
}

/**
 * UTF-8 解码函数（手动实现，兼容不支持 TextDecoder 的环境）
 * 正确解析 UTF-8 多字节字符
 */
function decodeUTF8(uint8Array: Uint8Array): string {
  let result = ''
  let i = 0
  
  while (i < uint8Array.length) {
    const byte1 = uint8Array[i++]
    
    // ASCII 字符 (0xxxxxxx)
    if (byte1 < 0x80) {
      result += String.fromCharCode(byte1)
    }
    // 2字节字符 (110xxxxx 10xxxxxx)
    else if ((byte1 & 0xE0) === 0xC0) {
      if (i >= uint8Array.length) break
      const byte2 = uint8Array[i++]
      if ((byte2 & 0xC0) !== 0x80) {
        // 无效的 UTF-8 序列，跳过
        continue
      }
      const codePoint = ((byte1 & 0x1F) << 6) | (byte2 & 0x3F)
      result += String.fromCharCode(codePoint)
    }
    // 3字节字符 (1110xxxx 10xxxxxx 10xxxxxx)
    else if ((byte1 & 0xF0) === 0xE0) {
      if (i + 1 >= uint8Array.length) break
      const byte2 = uint8Array[i++]
      const byte3 = uint8Array[i++]
      if ((byte2 & 0xC0) !== 0x80 || (byte3 & 0xC0) !== 0x80) {
        // 无效的 UTF-8 序列，跳过
        continue
      }
      const codePoint = ((byte1 & 0x0F) << 12) | ((byte2 & 0x3F) << 6) | (byte3 & 0x3F)
      result += String.fromCharCode(codePoint)
    }
    // 4字节字符 (11110xxx 10xxxxxx 10xxxxxx 10xxxxxx)
    else if ((byte1 & 0xF8) === 0xF0) {
      if (i + 2 >= uint8Array.length) break
      const byte2 = uint8Array[i++]
      const byte3 = uint8Array[i++]
      const byte4 = uint8Array[i++]
      if ((byte2 & 0xC0) !== 0x80 || (byte3 & 0xC0) !== 0x80 || (byte4 & 0xC0) !== 0x80) {
        // 无效的 UTF-8 序列，跳过
        continue
      }
      const codePoint = ((byte1 & 0x07) << 18) | ((byte2 & 0x3F) << 12) | ((byte3 & 0x3F) << 6) | (byte4 & 0x3F)
      // JavaScript 字符串使用 UTF-16，需要处理代理对
      if (codePoint > 0xFFFF) {
        const surrogate1 = 0xD800 + ((codePoint - 0x10000) >> 10)
        const surrogate2 = 0xDC00 + ((codePoint - 0x10000) & 0x3FF)
        result += String.fromCharCode(surrogate1, surrogate2)
      } else {
        result += String.fromCharCode(codePoint)
      }
    }
    // 无效的起始字节，跳过
    else {
      // 跳过无效字节
    }
  }
  
  return result
}

/**
 * 兼容的 ArrayBuffer/Uint8Array 转字符串函数
 * 微信小程序环境可能不支持 TextDecoder，使用兼容方案
 */
function arrayBufferToString(buffer: ArrayBuffer | Uint8Array): string {
  // 优先使用 TextDecoder（如果支持）
  if (typeof TextDecoder !== 'undefined') {
    try {
      const decoder = new TextDecoder('utf-8')
      if (buffer instanceof ArrayBuffer) {
        return decoder.decode(buffer)
      } else if (buffer instanceof Uint8Array) {
        return decoder.decode(buffer)
      }
    } catch {
      // TextDecoder 解码失败，降级到手动转换
    }
  }

  // 降级方案：使用手动实现的 UTF-8 解码函数
  try {
    const uint8Array = buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer
    return decodeUTF8(uint8Array)
  } catch {
    // 如果转换失败，返回空字符串
    return ''
  }
}

/**
 * 流式聊天接口
 * 微信小程序对 SSE 支持有限，自动降级到完整响应解析
 */
export function chatStream(
  params: ChatRequest,
  callbacks: StreamChatCallbacks
): Promise<void> {
  return new Promise((resolve, reject) => {
    const authStore = useAuthStore()
    const token = authStore.getToken()
    const url = BASE_URL + '/api/v1/client/chat'

    const header: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'X-My-Gate-Key': 'Huoyuan2026'
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    let buffer = ''
    let conversationId: number | undefined = undefined
    let isDone = false
    let hasRealStreaming = false

    const requestTask = uni.request({
      url,
      method: 'POST',
      data: {
        agent_type: params.agent_type,
        conversation_id: params.conversation_id,
        messages: params.messages,
        project_id: params.project_id,
        stream: true
      },
      header,
      responseType: 'text',
      enableChunked: true,
      timeout: 100000,
      success: (response) => {
        if (hasRealStreaming) {
          // 检查响应体中的 code 字段（即使 HTTP 状态码是 200）
          let shouldHandleAsError = false
          let errorMsg = `请求失败，状态码: ${response.statusCode}`

          if (response.data) {
            try {
              let responseData: any = null
              if (typeof response.data === 'string') {
                responseData = JSON.parse(response.data)
              } else if (typeof response.data === 'object') {
                responseData = response.data
              }

              // 检查响应体中的 code 字段
              if (responseData && responseData.code !== undefined) {
                if (responseData.code !== 200) {
                  shouldHandleAsError = true
                  errorMsg = responseData.msg || responseData.message || responseData.error || `请求失败，code: ${responseData.code}`
                }
              } else if (response.statusCode !== 200) {
                // 如果没有 code 字段，检查 HTTP 状态码
                shouldHandleAsError = true
                if (responseData) {
                  if (responseData.msg) {
                    errorMsg = String(responseData.msg)
                  } else if (responseData.message) {
                    errorMsg = String(responseData.message)
                  } else if (responseData.error) {
                    errorMsg = String(responseData.error)
                  }
                }
              }
            } catch (e) {
              // 解析失败，如果 HTTP 状态码不是 200，当作错误处理
              if (response.statusCode !== 200) {
                shouldHandleAsError = true
              }
            }
          } else if (response.statusCode !== 200) {
            shouldHandleAsError = true
          }

          if (shouldHandleAsError) {
            if (callbacks.onError) {
              callbacks.onError(errorMsg)
            }
            reject(new Error(errorMsg))
            return
          }

          // 正常情况，resolve
          resolve()
          return
        }

        // 如果状态码不是 200，优先处理错误响应
        if (response.statusCode !== 200) {
          let errorMsg = `请求失败，状态码: ${response.statusCode}`
          if (response.data) {
            try {
              let errorData: any = null
              if (typeof response.data === 'string') {
                // 尝试解析 JSON 字符串
                errorData = JSON.parse(response.data)
              } else if (typeof response.data === 'object') {
                // 直接使用对象
                errorData = response.data
              }

              // 优先使用 msg 字段，其次使用 message 字段
              if (errorData) {
                if (errorData.msg) {
                  errorMsg = String(errorData.msg)
                } else if (errorData.message) {
                  errorMsg = String(errorData.message)
                } else if (errorData.error) {
                  errorMsg = String(errorData.error)
                }
              }
            } catch (e) {
              // 解析失败，使用默认错误信息
              console.error('解析错误响应失败:', e, response.data)
            }
          }
          // 确保调用 onError 回调
          if (callbacks.onError) {
            callbacks.onError(errorMsg)
          }
          reject(new Error(errorMsg))
          return
        }

        // 状态码为 200，但需要检查响应体中的 code 字段
        if (response.data) {
          // 先检查响应体中的 code 字段
          let hasCodeError = false
          let codeErrorMsg = ''

          try {
            let responseData: any = null
            if (typeof response.data === 'string') {
              // 尝试解析 JSON
              if (response.data.includes('data: ') || response.data.includes('\n\n')) {
                // SSE 格式，交给 simulateStreaming 处理
                simulateStreaming(response.data, callbacks, conversationId)
                isDone = true
              } else {
                responseData = JSON.parse(response.data)
              }
            } else if (typeof response.data === 'object') {
              responseData = response.data
            }

            // 检查 code 字段
            if (responseData && responseData.code !== undefined && responseData.code !== 200) {
              hasCodeError = true
              codeErrorMsg = responseData.msg || responseData.message || responseData.error || `请求失败，code: ${responseData.code}`
            }
          } catch (e) {
            // 解析失败，继续正常处理
          }

          if (hasCodeError) {
            // 有 code 错误，调用 onError
            if (callbacks.onError) {
              callbacks.onError(codeErrorMsg)
            }
            reject(new Error(codeErrorMsg))
            return
          }

          // 没有 code 错误，正常处理响应数据
          if (!isDone && response.data) {
            if (typeof response.data === 'string') {
              if (!response.data.includes('data: ') && !response.data.includes('\n\n')) {
                try {
                  const jsonData = JSON.parse(response.data)
                  handleJSONResponse(jsonData, callbacks, conversationId)
                } catch (e) {
                  if (callbacks.onChunk) callbacks.onChunk(response.data)
                  if (callbacks.onDone) callbacks.onDone()
                }
              }
            } else if (typeof response.data === 'object') {
              handleJSONResponse(response.data, callbacks, conversationId)
            }
          }
        }

        if (!isDone && callbacks.onDone) callbacks.onDone()
        resolve()
      },
      fail: (error) => {
        const errorMsg = error.errMsg || '网络请求失败'
        if (callbacks.onError) callbacks.onError(errorMsg)
        reject(new Error(errorMsg))
      }
    })

    // onChunkReceived 处理真正的流式数据
    try {
      interface RequestTaskWithChunk {
        onChunkReceived?: (res: { data: string | ArrayBuffer | Uint8Array }) => void
      }
      const task = requestTask as RequestTaskWithChunk
      if (task && typeof task.onChunkReceived === 'function') {
        task.onChunkReceived((res: { data: string | ArrayBuffer | Uint8Array }) => {
          if (res && res.data) {
            hasRealStreaming = true

            // 关键：将 ArrayBuffer 转换为字符串
            // 注意：responseType 设置为 'text' 时，数据通常已经是字符串
            // 但如果收到 ArrayBuffer/Uint8Array，需要使用 UTF-8 解码
            let chunkStr = ''
            if (typeof res.data === 'string') {
              chunkStr = res.data
            } else if (res.data instanceof ArrayBuffer || res.data instanceof Uint8Array) {
              // 使用兼容的 UTF-8 解码函数
              chunkStr = arrayBufferToString(res.data)
            } else {
              chunkStr = String(res.data)
            }

            buffer += chunkStr

            // 检查是否是错误响应（普通 JSON 格式，不是 SSE 格式）
            // 错误响应可能是：{"code":400,"data":null,"msg":"..."}
            // 尝试解析 buffer 中可能包含的完整 JSON 对象
            try {
              const trimmedBuffer = buffer.trim()
              // 检查是否以 { 开头，可能是 JSON
              if (trimmedBuffer.startsWith('{')) {
                // 尝试找到完整的 JSON 对象
                let braceCount = 0
                let jsonEnd = -1
                for (let i = 0; i < trimmedBuffer.length; i++) {
                  if (trimmedBuffer[i] === '{') braceCount++
                  if (trimmedBuffer[i] === '}') {
                    braceCount--
                    if (braceCount === 0) {
                      jsonEnd = i + 1
                      break
                    }
                  }
                }

                if (jsonEnd > 0) {
                  // 找到了完整的 JSON 对象
                  const jsonStr = trimmedBuffer.substring(0, jsonEnd)
                  const parsed = JSON.parse(jsonStr)
                  // 检查是否有 code 字段且不等于 200
                  if (parsed.code !== undefined && parsed.code !== 200) {
                    const errorMsg = parsed.msg || parsed.message || parsed.error || `请求失败，code: ${parsed.code}`
                    if (callbacks.onError) {
                      callbacks.onError(errorMsg)
                    }
                    buffer = trimmedBuffer.substring(jsonEnd) // 移除已处理的 JSON
                    return
                  }
                }
              }
            } catch (e) {
              // 解析失败，继续处理 SSE 格式
            }

            const result = processSSEBuffer(buffer, callbacks, conversationId)
            if (result.conversationId !== undefined) {
              conversationId = result.conversationId
            }
            buffer = result.remainingBuffer

            if (buffer.includes('"done":true')) {
              isDone = true
              if (callbacks.onDone) callbacks.onDone()
            }
          }
        })
      }
    } catch (e) {
      // 平台不支持 onChunkReceived，降级到 success 回调处理
    }
  })
}

function handleJSONResponse(
  data: any,
  callbacks: StreamChatCallbacks,
  currentConversationId?: number
) {
  let conversationId = currentConversationId

  if (data.code !== undefined) {
    if (data.code !== 200) {
      const errorMsg = data.msg || data.message || '请求失败'
      if (callbacks.onError) callbacks.onError(errorMsg)
      return
    }
    if (data.data) {
      return handleJSONResponse(data.data, callbacks, currentConversationId)
    }
  }

  if (data.conversation_id !== undefined && callbacks.onConversationId) {
    conversationId = data.conversation_id
    callbacks.onConversationId(data.conversation_id)
  }

  if (data.content !== undefined && data.content !== null && data.content !== '') {
    const content = String(data.content)
    if (callbacks.onChunk) callbacks.onChunk(content)
  }

  if (data.error && callbacks.onError) {
    callbacks.onError(String(data.error))
    return
  }

  if (data.done === true || (!data.error && data.content !== undefined)) {
    if (callbacks.onDone) callbacks.onDone()
  }
}

function simulateStreaming(
  sseData: string,
  callbacks: StreamChatCallbacks,
  currentConversationId?: number
) {
  const lines = sseData.split('\n')
  let conversationId = currentConversationId
  const contentChunks: string[] = []
  let hasDone = false

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    if (trimmed.startsWith('data: ')) {
      try {
        const jsonStr = trimmed.substring(6)
        const parsed = JSON.parse(jsonStr)

        if (parsed.conversation_id !== undefined && callbacks.onConversationId) {
          conversationId = parsed.conversation_id
          callbacks.onConversationId(parsed.conversation_id)
        }

        // 支持 { content: "xxx" } 和 { delta: { content: "xxx" } } 两种格式
        let content = ''
        if (parsed.content !== undefined && parsed.content !== null && parsed.content !== '') {
          content = String(parsed.content)
        } else if (parsed.delta?.content !== undefined && parsed.delta.content !== null && parsed.delta.content !== '') {
          content = String(parsed.delta.content)
        }

        if (content) {
          contentChunks.push(content)
        }

        if (parsed.done === true) {
          hasDone = true
        }

        if (parsed.error && callbacks.onError) {
          callbacks.onError(String(parsed.error))
          return
        }
      } catch (e) {
        // 解析失败，跳过该行
      }
    } else if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        const parsed = JSON.parse(trimmed)
        handleJSONResponse(parsed, callbacks, conversationId)
        return
      } catch (e) {
        // 解析失败，跳过
      }
    }
  }

  if (contentChunks.length > 0) {
    let index = 0
    const chunkDelay = 30

    const emitChunks = () => {
      if (index < contentChunks.length && callbacks.onChunk) {
        callbacks.onChunk(contentChunks[index])
        index++
        setTimeout(emitChunks, chunkDelay)
      } else if (callbacks.onDone) {
        callbacks.onDone()
      }
    }

    emitChunks()
  } else {
    if (callbacks.onDone) callbacks.onDone()
  }
}

function processSSEBuffer(
  buffer: string,
  callbacks: StreamChatCallbacks,
  currentConversationId?: number
): { conversationId?: number; remainingBuffer: string } {
  const lines = buffer.split('\n')
  const remainingBuffer = lines.pop() || ''
  let conversationId = currentConversationId

  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('data: ')) {
      try {
        const jsonStr = trimmed.substring(6)
        const parsed = JSON.parse(jsonStr)

        if (parsed.conversation_id !== undefined && callbacks.onConversationId) {
          conversationId = parsed.conversation_id
          callbacks.onConversationId(parsed.conversation_id)
        }

        // 支持两种格式
        let content = ''
        if (parsed.content) {
          content = String(parsed.content)
        } else if (parsed.delta?.content) {
          content = String(parsed.delta.content)
        }

        if (content && callbacks.onChunk) {
          callbacks.onChunk(content)
        }

        if (parsed.done === true) {
          if (callbacks.onDone) callbacks.onDone()
        }

        if (parsed.error && callbacks.onError) {
          callbacks.onError(parsed.error)
        }
      } catch (e) {
        // 解析失败，跳过
      }
    }
  }

  return { conversationId, remainingBuffer }
}

export function chat(params: ChatRequest) {
  return request<ChatResponseData>({
    url: '/api/v1/client/chat',
    method: 'POST',
    data: {
      agent_type: params.agent_type,
      conversation_id: params.conversation_id,
      messages: params.messages,
      project_id: params.project_id,
      stream: params.stream
    },
    loadingText: 'AI 生成中...'
  })
}

