# Claude 模型缓存功能实现说明

## 概述

为了优化性能和降低成本，我们为 Claude 模型实现了提示词缓存功能。此功能完全兼容 OpenRouter 和 Anthropic 原生 API。

## 实现原理

根据 Anthropic 的缓存机制，我们需要：
1. 将原本的纯字符串 `content` 改为列表结构
2. 在需要缓存的文本块后面添加 `cache_control` 标记

## 代码修改

### 修改文件
- `backend/services/llm_service.py` 中的 `ClaudeLLM` 类

### 核心改动

#### 1. OpenAI 兼容格式（OpenRouter 等）

**针对 Claude 模型：**
```python
if is_claude_model:
    messages.append({
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    })
```

**针对其他模型：**
```python
else:
    messages.append({"role": "system", "content": system_prompt})
```

#### 2. Anthropic 原生 API 格式

**针对 Claude 模型：**
```python
user_content = [{"type": "text", "text": prompt}]
if is_claude_model:
    user_content[0]["cache_control"] = {"type": "ephemeral"}
```

## 兼容性保证

- ✅ **Claude 模型**（claude-3-5-sonnet, claude-3-opus 等）：使用缓存结构
- ✅ **DeepSeek 模型**：继续使用普通字符串格式
- ✅ **Doubao 模型**：继续使用普通字符串格式
- ✅ **其他 OpenAI 兼容模型**：继续使用普通字符串格式

## 缓存策略

### 缓存位置
- **System Prompt**：会被缓存（通常很大且在多轮对话中重复使用）
- **User Prompt**：不会被缓存（每轮对话都不同）

### 缓存效果
- **降低延迟**：缓存的系统提示词不需要重复处理
- **降低成本**：缓存的输入 tokens 按 90% 折扣计费
- **提升性能**：特别适合有大量系统提示词的场景

## 模型识别逻辑

通过检查模型名称来判断是否为 Claude 模型：
```python
is_claude_model = kwargs.get("model", self.model).startswith("claude")
```

这确保了只有真正的 Claude 模型才会使用缓存结构，其他模型保持原有格式。

## 使用示例

### 后端代码（自动）

```python
# 在 AIService 或其他地方调用
llm = LLMFactory.create("claude")
response = await llm.generate_stream(
    prompt="你好",
    system_prompt="你是一个很有用的助手...",
    model="claude-3-5-sonnet-20241022"
)
# 自动为 system_prompt 启用缓存
```

### API 请求格式（实际发送）

**Claude 模型的请求：**
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "你是一个很有用的助手...",
          "cache_control": {"type": "ephemeral"}
        }
      ]
    },
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": true
}
```

**其他模型的请求（保持不变）：**
```json
{
  "model": "deepseek-chat",
  "messages": [
    {
      "role": "system",
      "content": "你是一个很有用的助手..."
    },
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": true
}
```

## 监控和验证

可以通过以下方式验证缓存是否生效：

1. **检查响应头**：OpenRouter 和 Anthropic API 会在响应中包含缓存使用信息
2. **监控成本**：查看 API 账单，缓存 tokens 应该有 90% 折扣
3. **性能测试**：对比启用缓存前后的响应时间

## 注意事项

1. **缓存有效期**：使用 `ephemeral` 类型，缓存在会话期间有效
2. **缓存位置**：建议只缓存 system_prompt，不缓存 user 消息
3. **向后兼容**：非 Claude 模型完全不受影响，保持原有行为

## 参考资料

- [Anthropic Prompt Caching Documentation](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [OpenRouter Caching Support](https://openrouter.ai/docs#prompt-caching)

## 更新日期

2025-01-09
