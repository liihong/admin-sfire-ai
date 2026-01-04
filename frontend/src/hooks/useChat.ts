import { ref, nextTick, Ref } from "vue";

/**
 * 聊天消息接口
 */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  streaming?: boolean; // 是否正在流式输出
}

/**
 * 聊天管理 Hook
 * 
 * @description 用于管理聊天消息列表，自动滚动到底部
 * 
 * @example
 * ```ts
 * const { messages, addMessage, updateLastMessage, clearMessages, scrollToBottom } = useChat();
 * ```
 */
export function useChat(chatContainerRef?: Ref<HTMLElement | undefined>) {
  /** 消息列表 */
  const messages = ref<ChatMessage[]>([]);

  /**
   * 生成唯一ID
   */
  const generateId = (): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  /**
   * 添加消息
   * 
   * @param role 消息角色
   * @param content 消息内容
   * @param streaming 是否正在流式输出
   */
  const addMessage = (role: "user" | "assistant" | "system", content: string, streaming = false): ChatMessage => {
    const message: ChatMessage = {
      id: generateId(),
      role,
      content,
      timestamp: Date.now(),
      streaming
    };
    messages.value.push(message);
    nextTick(() => {
      scrollToBottom();
    });
    return message;
  };

  /**
   * 更新最后一条消息
   * 
   * @param content 新的消息内容
   * @param streaming 是否正在流式输出
   */
  const updateLastMessage = (content: string, streaming = false): void => {
    if (messages.value.length > 0) {
      const lastMessage = messages.value[messages.value.length - 1];
      lastMessage.content = content;
      lastMessage.streaming = streaming;
      nextTick(() => {
        scrollToBottom();
      });
    }
  };

  /**
   * 追加到最后一条消息
   * 
   * @param content 要追加的内容
   */
  const appendToLastMessage = (content: string): void => {
    if (messages.value.length > 0) {
      const lastMessage = messages.value[messages.value.length - 1];
      lastMessage.content += content;
      lastMessage.streaming = true;
      nextTick(() => {
        scrollToBottom();
      });
    }
  };

  /**
   * 标记最后一条消息完成流式输出
   */
  const finishLastMessage = (): void => {
    if (messages.value.length > 0) {
      const lastMessage = messages.value[messages.value.length - 1];
      lastMessage.streaming = false;
    }
  };

  /**
   * 清空所有消息
   */
  const clearMessages = (): void => {
    messages.value = [];
  };

  /**
   * 滚动到底部
   */
  const scrollToBottom = (): void => {
    if (!chatContainerRef?.value) return;
    
    nextTick(() => {
      const container = chatContainerRef.value;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    });
  };

  /**
   * 删除指定消息
   * 
   * @param messageId 消息ID
   */
  const removeMessage = (messageId: string): void => {
    const index = messages.value.findIndex(msg => msg.id === messageId);
    if (index > -1) {
      messages.value.splice(index, 1);
    }
  };

  return {
    messages,
    addMessage,
    updateLastMessage,
    appendToLastMessage,
    finishLastMessage,
    clearMessages,
    removeMessage,
    scrollToBottom
  };
}