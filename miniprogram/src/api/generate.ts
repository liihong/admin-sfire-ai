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
  [key: string]: any
}

export interface StreamChatCallbacks {
  onChunk?: (content: string) => void
  onConversationId?: (conversationId: number) => void
  onDone?: () => void
  onError?: (error: string) => void
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
    const decoder = new TextDecoder('utf-8')

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
          if (response.statusCode === 200) {
            resolve()
          } else {
            reject(new Error(`请求失败，状态码: ${response.statusCode}`))
          }
          return
        }

        if (response.data) {
          if (typeof response.data === 'string') {
            if (response.data.includes('data: ') || response.data.includes('\n\n')) {
              simulateStreaming(response.data, callbacks, conversationId)
              isDone = true
            } else {
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

        if (response.statusCode === 200) {
          if (!isDone && callbacks.onDone) callbacks.onDone()
          resolve()
        } else {
          const errorMsg = `请求失败，状态码: ${response.statusCode}`
          if (callbacks.onError) callbacks.onError(errorMsg)
          reject(new Error(errorMsg))
        }
      },
      fail: (error) => {
        const errorMsg = error.errMsg || '网络请求失败'
        if (callbacks.onError) callbacks.onError(errorMsg)
        reject(new Error(errorMsg))
      }
    })

    // onChunkReceived 处理真正的流式数据
    try {
      const task = requestTask as any
      if (task && typeof task.onChunkReceived === 'function') {
        task.onChunkReceived((res: any) => {
          if (res && res.data) {
            hasRealStreaming = true

            // 关键：将 ArrayBuffer 转换为字符串
            let chunkStr = ''
            if (typeof res.data === 'string') {
              chunkStr = res.data
            } else if (res.data instanceof ArrayBuffer || res.data instanceof Uint8Array) {
              chunkStr = decoder.decode(res.data)
            } else {
              chunkStr = String(res.data)
            }

            buffer += chunkStr
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
