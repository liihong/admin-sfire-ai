/**
 * Generate API - 生成内容相关接口
 */
import { request } from '@/utils/request'
import { useAuthStore } from '@/stores/auth'

// API 基础地址
const BASE_URL = __API_BASE_URL__

/**
 * 生成请求参数类型
 */
export interface GenerateRequest {
  project_id?: number
  agent_type?: string
  messages: Array<{role: string, content: string}>
  model_type?: string
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

/**
 * 生成响应类型
 */
export interface GenerateResponse {
  success: boolean
  content: string
  agent_type: string
  model_type: string
}

/**
 * 快速文案生成请求参数类型
 */
export interface CopywritingRequest {
  content: string
  agent_type?: string
  project_id?: number
  model_type?: string
}

/**
 * 快速文案生成响应类型
 */
export interface CopywritingResponse {
  success: boolean
  content: string
  agent_type: string
  model_type: string
}

/**
 * 聊天请求参数类型
 */
export interface ChatRequest {
    agent_type: string
    conversation_id?: number
    messages: Array<{ role: string, content: string }>
    project_id?: number
    stream: boolean
}

/**
 * 聊天响应数据类型（response.data 的类型）
 */
export interface ChatResponseData {
    content?: string
    conversation_id?: number
    [key: string]: any
}

/**
 * 流式聊天回调函数类型
 */
export interface StreamChatCallbacks {
  /** 接收到内容块时调用 */
  onChunk?: (content: string) => void
  /** 接收到会话ID时调用 */
  onConversationId?: (conversationId: number) => void
  /** 流式响应完成时调用 */
  onDone?: () => void
  /** 发生错误时调用 */
  onError?: (error: string) => void
}

/**
 * 流式聊天接口（对话式创作，支持实时流式输出）
 * 
 * 注意：微信小程序对 SSE 流式响应的支持有限，此实现会尝试使用最佳可用方案
 * 如果平台不支持真正的流式响应，会解析完整的 SSE 响应并逐块调用回调，模拟流式效果
 */
export function chatStream(
  params: ChatRequest,
  callbacks: StreamChatCallbacks
): Promise<void> {
  return new Promise((resolve, reject) => {
    // 在函数内部动态导入 store，避免在模块加载时执行
    const authStore = useAuthStore()
    const token = authStore.getToken()

    // 构建完整 URL
    const url = BASE_URL + '/api/v1/client/chat'

    // 构建请求头
    const header: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream', // 明确请求 SSE 格式
      'X-My-Gate-Key': 'Huoyuan2026'
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    // 用于累积接收到的数据
    let buffer = ''
    let conversationId: number | undefined = undefined
    let isDone = false
    let hasRealStreaming: boolean = false // 标记是否使用了真正的流式

    // 发起请求
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
      responseType: 'text', // 使用文本类型接收 SSE 数据
      enableChunked: true, // 启用分块传输（如果支持）
      timeout: 100000,
      success: (response) => {
        console.log('[chatStream] success 回调触发:', {
          statusCode: response.statusCode,
          dataType: typeof response.data,
          dataLength: typeof response.data === 'string' ? response.data.length : 'N/A',
          hasRealStreaming: hasRealStreaming,
          dataPreview: typeof response.data === 'string'
            ? response.data.substring(0, 500)
            : JSON.stringify(response.data).substring(0, 500)
        })

        // 如果使用了真正的流式（onChunkReceived 工作了），不再处理
        if (hasRealStreaming) {
          console.log('[chatStream] 已使用 onChunkReceived 处理流式数据，跳过 success 回调中的处理')
          if (response.statusCode === 200) {
            resolve()
          } else {
            reject(new Error(`请求失败，状态码: ${response.statusCode}`))
          }
          return
        }

        // 如果没有使用真正的流式，处理完整响应
        console.log('[chatStream] 没有使用流式，开始处理完整响应')
        if (response.data) {
          // 处理字符串类型的响应（SSE 格式）
          if (typeof response.data === 'string') {
            console.log('[chatStream] 响应是字符串类型，长度:', response.data.length)
            // 检查是否是 SSE 格式
            if (response.data.includes('data: ') || response.data.includes('\n\n')) {
              console.log('[chatStream] 检测到 SSE 格式，开始解析')
              // 解析完整的 SSE 响应并模拟流式效果
              simulateStreaming(response.data, callbacks, conversationId)
              // 注意：onDone 会在 simulateStreaming 完成后调用，这里不再调用
              isDone = true  // 标记已完成，防止在下面再次调用 onDone
            } else {
              // 尝试解析为普通 JSON
              try {
                console.log('[chatStream] 尝试解析为 JSON')
                const jsonData = JSON.parse(response.data)
                handleJSONResponse(jsonData, callbacks, conversationId)
              } catch (e) {
                console.warn('[chatStream] JSON 解析失败，直接作为内容处理:', e)
                // 如果不是 JSON，直接作为内容处理
                if (callbacks.onChunk) {
                  callbacks.onChunk(response.data)
                }
                if (callbacks.onDone) {
                  callbacks.onDone()
                }
              }
            }
          }
          // 处理对象类型的响应（普通 JSON，已被自动解析）
          else if (typeof response.data === 'object') {
            console.log('[chatStream] 检测到对象类型响应，直接处理')
            handleJSONResponse(response.data, callbacks, conversationId)
          }
        } else {
          console.warn('[chatStream] 响应数据为空')
        }

        // 检查响应状态
        if (response.statusCode === 200) {
          // 只有在 isDone 为 false 时才调用 onDone
          if (!isDone && callbacks.onDone) {
            console.log('[chatStream] 调用 onDone（非流式响应）')
            callbacks.onDone()
          }
          resolve()
        } else {
          const errorMsg = `请求失败，状态码: ${response.statusCode}`
          if (callbacks.onError) {
            callbacks.onError(errorMsg)
          }
          reject(new Error(errorMsg))
        }
      },
      fail: (error) => {
        const errorMsg = error.errMsg || '网络请求失败'
        if (callbacks.onError) {
          callbacks.onError(errorMsg)
        }
        reject(new Error(errorMsg))
      }
    })

    // 尝试监听分块数据接收（如果平台支持）
    // 注意：微信小程序对 SSE 流式响应的支持有限，需要在 success 回调中处理完整响应
    let chunkReceived = false  // 标记是否真的收到了分块数据
    try {
      const task = requestTask as any
      if (task && typeof task.onChunkReceived === 'function') {
        console.log('[chatStream] 检测到 onChunkReceived，设置监听')
        // 注意：不立即设置 hasRealStreaming = true，而是等到真正收到数据时才设置
        task.onChunkReceived((res: any) => {
          console.log('[chatStream] onChunkReceived 触发，数据:', res)
          if (res && res.data) {
            chunkReceived = true
            hasRealStreaming = true  // 只有真正收到数据时才设置

            // 将 ArrayBuffer 转换为字符串
            let chunkStr = ''
            if (typeof res.data === 'string') {
              chunkStr = res.data
            } else if (res.data instanceof ArrayBuffer) {
              // 将 ArrayBuffer 转换为字符串
              const decoder = new TextDecoder('utf-8')
              chunkStr = decoder.decode(res.data)
            } else if (res.data instanceof Uint8Array) {
              const decoder = new TextDecoder('utf-8')
              chunkStr = decoder.decode(res.data)
            } else {
              // 尝试其他类型
              chunkStr = String(res.data)
            }

            console.log('[chatStream] onChunkReceived 收到数据块，原始类型:', typeof res.data, '转换后长度:', chunkStr.length, '内容:', chunkStr.substring(0, 100))
            buffer += chunkStr
            console.log('[chatStream] 累积缓冲区长度:', buffer.length)

            // 实时处理接收到的数据块
            const result = processSSEBuffer(buffer, callbacks, conversationId)
            if (result.conversationId !== undefined) {
              conversationId = result.conversationId
            }
            buffer = result.remainingBuffer

            // 检查是否完成
            if (buffer.includes('"done":true') || buffer.includes('"done": True') || buffer.includes('"done":true')) {
              isDone = true
              if (callbacks.onDone) {
                callbacks.onDone()
              }
            }
          }
        })
      } else {
        console.log('[chatStream] onChunkReceived 不可用')
      }
    } catch (e) {
      // 平台不支持 onChunkReceived，将在 success 回调中处理完整响应
      console.log('[chatStream] onChunkReceived 设置失败:', e)
    }
  })
}

/**
 * 处理普通 JSON 响应
 */
function handleJSONResponse(
  data: any,
  callbacks: StreamChatCallbacks,
  currentConversationId?: number
) {
  console.log('[handleJSONResponse] 处理 JSON 响应:', JSON.stringify(data, null, 2))
  let conversationId = currentConversationId

  // 检查是否是后端统一响应格式 {code, data, msg}
  if (data.code !== undefined) {
    console.log('[handleJSONResponse] 检测到统一响应格式，code:', data.code)
    // 如果 code 不是 200，可能是错误
    if (data.code !== 200) {
      const errorMsg = data.msg || data.message || '请求失败'
      console.error('[handleJSONResponse] 响应错误:', errorMsg)
      if (callbacks.onError) {
        callbacks.onError(errorMsg)
      }
      return
    }
    // 提取 data 字段
    if (data.data) {
      console.log('[handleJSONResponse] 提取 data 字段:', data.data)
      return handleJSONResponse(data.data, callbacks, currentConversationId)
    }
  }

  // 处理会话ID
  if (data.conversation_id !== undefined && callbacks.onConversationId) {
    conversationId = data.conversation_id
    console.log('[handleJSONResponse] 会话ID:', conversationId)
    callbacks.onConversationId(data.conversation_id)
  }

  // 处理内容（优先检查 content 字段）
  if (data.content !== undefined && data.content !== null && data.content !== '') {
    const content = String(data.content)
    console.log('[handleJSONResponse] 调用 onChunk，内容:', content, '长度:', content.length)
    if (callbacks.onChunk) {
      callbacks.onChunk(content)
    }
  }

  // 处理错误
  if (data.error && callbacks.onError) {
    console.error('[handleJSONResponse] 错误:', data.error)
    callbacks.onError(String(data.error))
    return
  }

  // 处理完成标志
  if (data.done === true || (!data.error && data.content !== undefined)) {
    console.log('[handleJSONResponse] 调用 onDone')
    if (callbacks.onDone) {
      callbacks.onDone()
    }
  }
}

/**
 * 模拟流式效果：解析完整的 SSE 响应并逐块调用回调
 * 这样可以提供类似流式的用户体验，即使平台不支持真正的流式响应
 */
function simulateStreaming(
  sseData: string,
  callbacks: StreamChatCallbacks,
  currentConversationId?: number
) {
  console.log('[simulateStreaming] 开始解析 SSE 数据，长度:', sseData.length)
  console.log('[simulateStreaming] 数据预览:', sseData.substring(0, 200))
  console.log('[simulateStreaming] 完整数据:', sseData)

  const lines = sseData.split('\n')
  let conversationId = currentConversationId
  const contentChunks: string[] = [] // 收集所有内容块
  let hasDone = false

  // 解析所有 SSE 数据
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue // 跳过空行

    // 处理 SSE 格式：data: {...}
    if (trimmed.startsWith('data: ')) {
      try {
        const jsonStr = trimmed.substring(6) // 移除 "data: " 前缀
        console.log('[simulateStreaming] 解析 SSE 行:', jsonStr.substring(0, 100))
        const parsed = JSON.parse(jsonStr)

        // 处理会话ID
        if (parsed.conversation_id !== undefined) {
          conversationId = parsed.conversation_id
          console.log('[simulateStreaming] 会话ID:', conversationId)
          if (callbacks.onConversationId) {
            callbacks.onConversationId(parsed.conversation_id)
          }
        }

        // 收集内容块
        // 后端返回的格式可能是：{ content: "xxx" } 或 { delta: { content: "xxx" } }
        let content = ''
        if (parsed.content !== undefined && parsed.content !== null && parsed.content !== '') {
          content = String(parsed.content)
        } else if (parsed.delta?.content !== undefined && parsed.delta.content !== null && parsed.delta.content !== '') {
          content = String(parsed.delta.content)
        }

        if (content) {
          console.log('[simulateStreaming] 收集内容块:', content, '长度:', content.length)
          contentChunks.push(content)
        }

        // 处理完成标志
        if (parsed.done === true) {
          hasDone = true
          console.log('[simulateStreaming] 检测到完成标志')
        }

        // 处理错误
        if (parsed.error && callbacks.onError) {
          console.error('[simulateStreaming] 错误:', parsed.error)
          callbacks.onError(String(parsed.error))
          return
        }
      } catch (e) {
        console.warn('[simulateStreaming] 解析 SSE 数据失败:', trimmed.substring(0, 100), e)
      }
    }
    // 尝试直接解析 JSON（如果不是 SSE 格式）
    else if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        console.log('[simulateStreaming] 尝试直接解析 JSON:', trimmed.substring(0, 100))
        const parsed = JSON.parse(trimmed)
        handleJSONResponse(parsed, callbacks, conversationId)
        return // 如果是普通 JSON，直接处理并返回
      } catch (e) {
        console.warn('[simulateStreaming] JSON 解析失败:', e)
      }
    }
  }

  console.log('[simulateStreaming] 解析完成，内容块数量:', contentChunks.length, 'hasDone:', hasDone)

  // 如果有内容块，逐块调用回调，模拟流式效果
  if (contentChunks.length > 0) {
    let index = 0
    const chunkDelay = 30 // 每个块的延迟（毫秒），增加延迟让流式效果更明显

    const emitChunks = () => {
      if (index < contentChunks.length && callbacks.onChunk) {
        console.log('[simulateStreaming] 发送内容块', index + 1, '/', contentChunks.length, ':', contentChunks[index])
        callbacks.onChunk(contentChunks[index])
        index++
        setTimeout(emitChunks, chunkDelay)
      } else if (callbacks.onDone) {
        console.log('[simulateStreaming] 所有内容块发送完成')
        callbacks.onDone()
      }
    }

    // 立即开始发送第一个块
    emitChunks()
  } else {
    console.warn('[simulateStreaming] 没有找到内容块')
    if (callbacks.onDone) {
      callbacks.onDone()
    }
  }
}

/**
 * 处理 SSE 格式的缓冲区数据
 * @param buffer 待处理的缓冲区数据
 * @param callbacks 回调函数
 * @param currentConversationId 当前会话ID
 * @returns 新的会话ID和剩余缓冲区
 */
function processSSEBuffer(
  buffer: string,
  callbacks: StreamChatCallbacks,
  currentConversationId?: number
): { conversationId?: number; remainingBuffer: string } {
  const lines = buffer.split('\n')
  // 保留最后一行（可能不完整）
  const remainingBuffer = lines.pop() || ''
  let conversationId = currentConversationId

  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('data: ')) {
      try {
        const jsonStr = trimmed.substring(6) // 移除 "data: " 前缀
        const parsed = JSON.parse(jsonStr)

        // 处理会话ID
        if (parsed.conversation_id !== undefined && callbacks.onConversationId) {
          conversationId = parsed.conversation_id
          callbacks.onConversationId(parsed.conversation_id)
        }

        // 处理内容块（支持两种格式）
        let content = ''
        if (parsed.content) {
          content = String(parsed.content)
        } else if (parsed.delta?.content) {
          content = String(parsed.delta.content)
        }

        if (content && callbacks.onChunk) {
          console.log('[processSSEBuffer] 收到内容块:', content, '长度:', content.length)
          callbacks.onChunk(content)
        }

        // 处理完成标志
        if (parsed.done === true || parsed.done === true) {
          console.log('[processSSEBuffer] 检测到完成标志')
          if (callbacks.onDone) {
            callbacks.onDone()
          }
        }

        // 处理错误
        if (parsed.error && callbacks.onError) {
          callbacks.onError(parsed.error)
        }
      } catch (e) {
        console.warn('解析 SSE 数据失败:', trimmed, e)
      }
    }
  }

  return { conversationId, remainingBuffer }
}

/**
 * 聊天接口（对话式创作，非流式，用于兼容）
 */
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

