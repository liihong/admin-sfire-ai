import { ref, shallowRef } from "vue";
import { AI } from "@/api/interface";
import { useUserStore } from "@/stores/modules/user";

export interface SSEOptions {
  /** 请求 URL */
  url: string;
  /** 请求方法，默认 POST */
  method?: "GET" | "POST";
  /** 请求体 */
  body?: AI.ReqChatParams;
  /** 自定义请求头 */
  headers?: Record<string, string>;
  /** 连接成功回调 */
  onOpen?: () => void;
  /** 接收消息回调 */
  onMessage?: (chunk: AI.ResStreamChunk) => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
  /** 完成回调 */
  onComplete?: (fullContent: string) => void;
  /** 连接关闭回调 */
  onClose?: () => void;
}

/**
 * @description SSE 流式输出处理 Hook
 * @description 支持 POST 请求的 SSE 流式数据处理
 */
export const useSSE = () => {
  const userStore = useUserStore();

  // 状态
  const isConnecting = ref(false);
  const isStreaming = ref(false);
  const content = ref("");
  const error = ref<Error | null>(null);
  const totalTokens = ref(0);

  // AbortController 用于取消请求
  const abortController = shallowRef<AbortController | null>(null);

  /**
   * @description 开始 SSE 流式请求
   */
  const startStream = async (options: SSEOptions) => {
    const { url, method = "POST", body, headers = {}, onOpen, onMessage, onError, onComplete, onClose } = options;

    // 重置状态
    content.value = "";
    error.value = null;
    totalTokens.value = 0;
    isConnecting.value = true;

    // 创建 AbortController
    abortController.value = new AbortController();

    try {
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: userStore.token ? `Bearer ${userStore.token}` : "",
          Accept: "text/event-stream",
          ...headers
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: abortController.value.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      isConnecting.value = false;
      isStreaming.value = true;
      onOpen?.();

      // 读取流式数据
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          isStreaming.value = false;
          onComplete?.(content.value);
          onClose?.();
          break;
        }

        // 解码数据
        buffer += decoder.decode(value, { stream: true });

        // 处理 SSE 格式数据（以换行分隔）
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();

            // 检查是否是结束标记
            if (data === "[DONE]") {
              isStreaming.value = false;
              onComplete?.(content.value);
              continue;
            }

            try {
              const chunk: AI.ResStreamChunk = JSON.parse(data);
              const deltaContent = chunk.delta?.content || "";

              if (deltaContent) {
                content.value += deltaContent;
                totalTokens.value++;
              }

              onMessage?.(chunk);

              // 检查是否完成
              if (chunk.finish_reason) {
                isStreaming.value = false;
                onComplete?.(content.value);
              }
            } catch (parseError) {
              console.warn("Failed to parse SSE data:", data);
            }
          }
        }
      }
    } catch (err) {
      isConnecting.value = false;
      isStreaming.value = false;

      if (err instanceof Error) {
        // 忽略用户主动取消的错误
        if (err.name === "AbortError") {
          onClose?.();
          return;
        }
        error.value = err;
        onError?.(err);
      }
    }
  };

  /**
   * @description 停止 SSE 流式请求
   */
  const stopStream = () => {
    if (abortController.value) {
      abortController.value.abort();
      abortController.value = null;
    }
    isConnecting.value = false;
    isStreaming.value = false;
  };

  /**
   * @description 重置状态
   */
  const reset = () => {
    stopStream();
    content.value = "";
    error.value = null;
    totalTokens.value = 0;
  };

  return {
    // 状态
    isConnecting,
    isStreaming,
    content,
    error,
    totalTokens,

    // 方法
    startStream,
    stopStream,
    reset
  };
};

/**
 * @description 简化的 SSE Hook，用于快速创建对话
 */
export const useChatSSE = () => {
  const sse = useSSE();
  const messages = ref<AI.Message[]>([]);

  /**
   * @description 发送对话消息
   */
  const sendMessage = async (
    userMessage: string,
    options: {
      url: string;
      model?: string;
      systemPrompt?: string;
      onChunk?: (chunk: string) => void;
      onComplete?: (response: string) => void;
      onError?: (error: Error) => void;
    }
  ) => {
    const { url, model = "gpt-3.5-turbo", systemPrompt, onChunk, onComplete, onError } = options;

    // 添加用户消息
    const userMsg: AI.Message = {
      role: "user",
      content: userMessage,
      timestamp: Date.now()
    };
    messages.value.push(userMsg);

    // 构建消息列表
    const requestMessages: AI.Message[] = [];
    if (systemPrompt) {
      requestMessages.push({ role: "system", content: systemPrompt });
    }
    requestMessages.push(...messages.value);

    // 添加占位的助手消息
    const assistantMsg: AI.Message = {
      role: "assistant",
      content: "",
      timestamp: Date.now()
    };
    messages.value.push(assistantMsg);
    const assistantIndex = messages.value.length - 1;

    await sse.startStream({
      url,
      body: {
        messages: requestMessages,
        model,
        stream: true
      },
      onMessage: chunk => {
        const deltaContent = chunk.delta?.content || "";
        if (deltaContent) {
          messages.value[assistantIndex].content += deltaContent;
          onChunk?.(deltaContent);
        }
      },
      onComplete: fullContent => {
        messages.value[assistantIndex].content = fullContent;
        onComplete?.(fullContent);
      },
      onError: error => {
        // 移除失败的助手消息
        messages.value.pop();
        onError?.(error);
      }
    });
  };

  /**
   * @description 清空对话历史
   */
  const clearMessages = () => {
    messages.value = [];
    sse.reset();
  };

  return {
    ...sse,
    messages,
    sendMessage,
    clearMessages
  };
};
