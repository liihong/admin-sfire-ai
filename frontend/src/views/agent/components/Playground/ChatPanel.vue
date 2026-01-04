<template>
    <div class="chat-panel">
      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="chatContainerRef">
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-item"
          :class="{ 'message-user': message.role === 'user', 'message-assistant': message.role === 'assistant' }"
        >
          <div class="message-avatar">
            <el-icon v-if="message.role === 'user'" :size="20">
              <User />
            </el-icon>
            <el-icon v-else :size="20">
              <ChatDotRound />
            </el-icon>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(message.content)"></div>
            <div v-if="message.streaming" class="message-streaming">
              <span class="cursor">▋</span>
            </div>
          </div>
        </div>
  
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <el-empty description="开始与智能体对话..." :image-size="120" />
        </div>
      </div>
  
      <!-- 输入区域 -->
      <div class="chat-input-area">
        <div class="input-wrapper">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            placeholder="输入消息..."
            :disabled="isStreaming"
            @keydown.ctrl.enter="handleSend"
            @keydown.meta.enter="handleSend"
          />
          <div class="input-actions">
            <div class="input-tip">
              <el-text type="info" size="small">Ctrl/Cmd + Enter 发送</el-text>
            </div>
            <div class="input-buttons">
              <el-button :icon="Delete" text @click="handleClear">清空</el-button>
              <el-button
                type="primary"
                :icon="Promotion"
                :loading="isStreaming"
                :disabled="!userInput.trim()"
                @click="handleSend"
              >
                {{ isStreaming ? "生成中..." : "开始调试" }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts" name="ChatPanel">
  import { ref, computed, watch, nextTick } from "vue";
  import { ElMessage } from "element-plus";
  import { User, ChatDotRound, Promotion, Delete } from "@element-plus/icons-vue";
  import { useChat } from "@/hooks/useChat";
  import { useSSE } from "@/hooks/useSSE";
  import { PORT1 } from "@/api/config/servicePort";
  import type { ChatMessage } from "@/hooks/useChat";
  
  interface Props {
    agentConfig: {
      systemPrompt: string;
      model: string;
      temperature: number;
      maxTokens: number;
      topP: number;
      frequencyPenalty: number;
      presencePenalty: number;
      contextMessages: Array<{ role: "user" | "assistant"; content: string }>;
    };
    systemPrompt?: string;
  }
  
  const props = defineProps<Props>();
  
  const emit = defineEmits<{
    "save-config": [];
  }>();
  
  // 聊天容器引用
  const chatContainerRef = ref<HTMLElement>();
  
  // 使用聊天Hook
  const { messages, addMessage, appendToLastMessage, finishLastMessage, clearMessages, scrollToBottom } = useChat(chatContainerRef);
  
  // 使用SSE Hook
  const { isStreaming, startStream, stopStream } = useSSE();
  
  // 用户输入
  const userInput = ref("");
  
  // 渲染Markdown（简单实现，支持基本语法）
  const renderMarkdown = (text: string): string => {
    if (!text) return "";
  
    // 转义HTML
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  
    // 代码块
    html = html.replace(/```([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>');
  
    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
  
    // 粗体
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  
    // 斜体
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  
    // 链接
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  
    // 换行
    html = html.replace(/\n/g, "<br>");
  
    return html;
  };
  
  // 发送消息
  const handleSend = async () => {
    if (!userInput.value.trim() || isStreaming.value) return;
  
    const userMessage = userInput.value.trim();
    userInput.value = "";
  
    // 添加用户消息
    addMessage("user", userMessage);
  
    // 添加助手消息占位
    const assistantMessage = addMessage("assistant", "", true);
  
    // 构建消息列表（包含系统提示词和上下文）
    const requestMessages: Array<{ role: "user" | "assistant" | "system"; content: string }> = [];
  
    // 添加系统提示词
    if (props.systemPrompt || props.agentConfig.systemPrompt) {
      requestMessages.push({
        role: "system",
        content: props.systemPrompt || props.agentConfig.systemPrompt
      });
    }
  
    // 添加上下文示例
    if (props.agentConfig.contextMessages.length > 0) {
      props.agentConfig.contextMessages.forEach(ctx => {
        if (ctx.content.trim()) {
          requestMessages.push({
            role: ctx.role,
            content: ctx.content
          });
        }
      });
    }
  
    // 添加用户消息
    requestMessages.push({
      role: "user",
      content: userMessage
    });
  
    // 开始SSE流式请求
    try {
      await startStream({
        url: `${import.meta.env.VITE_API_URL}${PORT1}/ai/chat/stream`,
        body: {
          messages: requestMessages,
          model: props.agentConfig.model,
          temperature: props.agentConfig.temperature,
          max_tokens: props.agentConfig.maxTokens,
          top_p: props.agentConfig.topP,
          frequency_penalty: props.agentConfig.frequencyPenalty,
          presence_penalty: props.agentConfig.presencePenalty,
          stream: true
        },
        onMessage: (chunk) => {
          const deltaContent = chunk.delta?.content || "";
          if (deltaContent) {
            appendToLastMessage(deltaContent);
          }
        },
        onComplete: () => {
          finishLastMessage();
        },
        onError: (error) => {
          ElMessage.error(error.message || "请求失败");
          // 移除失败的助手消息
          if (messages.value.length > 0 && messages.value[messages.value.length - 1].id === assistantMessage.id) {
            messages.value.pop();
          }
        }
      });
    } catch (error: unknown) {
      const err = error as { message?: string };
      ElMessage.error(err.message || "发送消息失败");
      // 移除失败的助手消息
      if (messages.value.length > 0 && messages.value[messages.value.length - 1].id === assistantMessage.id) {
        messages.value.pop();
      }
    }
  };
  
  // 清空消息
  const handleClear = () => {
    clearMessages();
    userInput.value = "";
  };
  
  // 监听消息变化，自动滚动
  watch(
    () => messages.value.length,
    () => {
      scrollToBottom();
    }
  );
  </script>
  
  <style scoped lang="scss">
  .chat-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: var(--el-bg-color-page);
  
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 20px;
  
      .message-item {
        display: flex;
        gap: 12px;
        max-width: 80%;
        animation: fadeIn 0.3s ease-in;
  
        &.message-user {
          align-self: flex-end;
          flex-direction: row-reverse;
  
          .message-avatar {
            background: linear-gradient(135deg, var(--el-color-primary) 0%, #ff9500 100%);
            color: white;
          }
  
          .message-content {
            background-color: var(--el-color-primary);
            color: white;
  
            .message-text {
              color: white;
            }
  
            a {
              color: rgba(255, 255, 255, 0.9);
              text-decoration: underline;
            }
          }
        }
  
        &.message-assistant {
          align-self: flex-start;
  
          .message-avatar {
            background-color: var(--el-fill-color);
            color: var(--el-color-primary);
          }
  
          .message-content {
            background-color: var(--el-bg-color);
            border: 1px solid var(--el-border-color-lighter);
          }
        }
  
        .message-avatar {
          flex-shrink: 0;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
  
        .message-content {
          padding: 12px 16px;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
          word-wrap: break-word;
          line-height: 1.6;
  
          .message-text {
            color: var(--el-text-color-primary);
            font-size: 14px;
  
            :deep(.code-block) {
              background-color: var(--el-fill-color-dark);
              padding: 12px;
              border-radius: 6px;
              margin: 8px 0;
              overflow-x: auto;
              font-family: "Courier New", monospace;
              font-size: 13px;
  
              code {
                background: transparent;
                padding: 0;
              }
            }
  
            :deep(.inline-code) {
              background-color: var(--el-fill-color);
              padding: 2px 6px;
              border-radius: 4px;
              font-family: "Courier New", monospace;
              font-size: 13px;
              color: var(--el-color-primary);
            }
  
            :deep(strong) {
              font-weight: 600;
              color: var(--el-text-color-primary);
            }
  
            :deep(em) {
              font-style: italic;
            }
  
            :deep(a) {
              color: var(--el-color-primary);
              text-decoration: none;
  
              &:hover {
                text-decoration: underline;
              }
            }
          }
  
          .message-streaming {
            display: inline-block;
            margin-left: 4px;
  
            .cursor {
              display: inline-block;
              width: 2px;
              height: 16px;
              background-color: var(--el-color-primary);
              animation: blink 1s infinite;
              vertical-align: middle;
            }
          }
        }
      }
  
      .empty-state {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  
    .chat-input-area {
      padding: 16px 20px;
      background-color: var(--el-bg-color);
      border-top: 1px solid var(--el-border-color-lighter);
      box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
  
      .input-wrapper {
        .input-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 8px;
  
          .input-tip {
            flex: 1;
          }
  
          .input-buttons {
            display: flex;
            gap: 8px;
          }
        }
      }
    }
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes blink {
    0%, 50% {
      opacity: 1;
    }
    51%, 100% {
      opacity: 0;
    }
  }
  </style>