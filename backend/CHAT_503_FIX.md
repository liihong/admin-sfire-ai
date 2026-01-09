# Chat接口503错误修复说明

## 问题描述
`/api/v1/client/chat` 接口一直报错503,但在 `/api/v1/admin/ai/chat` 测试接口中模型可以正常联通。

## 根本原因分析

### 1. ���示词过长问题 (主要原因)
Client接口构建的 `system_prompt` 包含:
- 智能体系统提示词
- 对话历史(最近6轮)
- IP人设信息(简介、语气、受众、风格、口头禅、关键词、禁忌、对标账号)
- 融合说明文字

这可能导致提示词长度超过模型限制,造成API请求超时或被拒绝。

### 2. 模型查询失败
Provider映射可能导致数据库查询不到启用的模型配置。

### 3. 异常信息不明确
错误被捕获后返回通用的503错误,没有详细的错误信息,难以排查。

## 已实施的修复方案

### ✅ 1. 添加详细的调试日志
**位置**: `backend/routers/client/creation.py:565-579`

在调用AI服务前打印关键信息:
- Conversation ID, User ID
- Agent Type, Model Type, Provider
- Model ID for AI, DB Model名称
- Base URL
- System Prompt长度
- User Prompt长度
- 消息数量
- Temperature, Max Tokens, Stream模式

```python
logger.info(f"📊 [DEBUG] Chat Request Info:")
logger.info(f"  - Conversation ID: {conversation_id}")
logger.info(f"  - Model ID for AI: {model_id_for_ai}")
logger.info(f"  - System Prompt Length: {len(final_system_prompt)} chars")
# ... 更多详细信息
```

### ✅ 2. 增强模型查询验证和错误提示
**位置**: `backend/routers/client/creation.py:525-563`

- 在查询模型时打印provider映射信息
- 如果查询失败,列出所有启用的模型信息
- 提供详细的错误上下文

```python
if not llm_model:
    logger.error(f"❌ [DEBUG] Model not found in database:")
    logger.error(f"  - Requested model_type: {request.model_type}")
    logger.error(f"  - Mapped provider: {provider}")
    # 查询并打印所有启用的模型
    all_enabled = await db.execute(select(LLMModel).where(LLMModel.is_enabled == True))
    # ...
```

### ✅ 3. System Prompt长度限制和智能截断
**位置**: `backend/routers/client/creation.py:507-540`

限制system prompt最大8000字符,超出时采用智能截断策略:
1. 优先保留完整的智能体核心prompt
2. 其次添加IP人设的关键部分
3. 最后添加简化的对话历史(最多2轮)

```python
MAX_SYSTEM_PROMPT_LENGTH = 8000
if len(final_system_prompt) > MAX_SYSTEM_PROMPT_LENGTH:
    logger.warning(f"⚠️ System prompt too long, truncating...")
    # 智能截断策略
    # ...
```

### ✅ 4. 改进异常处理,返回详细错误
**位置**: `backend/routers/client/creation.py:690-706, 749-760`

- 在流式响应的异常捕获中添加详细日志
- 在接口级别的异常捕获中添加完整上下文
- 包含错误类型、消息、堆栈跟踪

```python
except Exception as e:
    logger.error(f"❌ [DEBUG] Stream generation failed:")
    logger.error(f"  - Error Type: {type(e).__name__}")
    logger.error(f"  - Error Message: {str(e)}")
    logger.error(f"  - Traceback:\n{traceback.format_exc()}")
    # ...
```

### ✅ 5. 新增Debug接口
**位置**: `backend/routers/client/creation.py:763-928`

新增 `/api/v1/client/chat/debug` 接口,用于快速排查问题:
- 返回模型配置查询结果
- 显示提示词构建过程和长度
- 展示所有中间步骤
- **不实际调用AI API**,避免触发503

## 使用指南

### 1. 使用Debug接口排查问题

**请求示例**:
```bash
curl -X POST http://172.18.0.1:9000/api/v1/client/chat/debug \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "model_type": "deepseek",
    "agent_type": "1",
    "project_id": null,
    "stream": false
  }'
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "request_params": {
      "model_type": "deepseek",
      "agent_type": "1",
      "stream": false
    },
    "step_results": {
      "model_type_check": {
        "is_supported": true,
        "supported_models": ["deepseek", "doubao", "claude"]
      },
      "model_query": {
        "provider": "deepseek",
        "found_model": {
          "id": 1,
          "name": "DeepSeek Chat",
          "model_id": "deepseek-chat",
          "base_url": "https://api.deepseek.com",
          "has_api_key": true,
          "is_enabled": true
        }
      },
      "prompt_building": {
        "user_prompt_length": 2,
        "estimated_system_prompt_length": 1500
      }
    }
  }
}
```

### 2. 查看日志排查问题

启动服务后,调用 `/api/v1/client/chat` 接口,然后查看日志:

```bash
# 查看详细日志
tail -f backend/logs/app.log | grep DEBUG

# 关键日志标识:
# 📊 [DEBUG] - 请求基本信息
# 🔍 [DEBUG] - 模型配置查询
# ⚠️ [DEBUG] - 提示词长度警告
# ❌ [DEBUG] - 错误详情
```

### 3. 常见问题排查

#### 问题1: 模型未找到
**日志特征**:
```
❌ [DEBUG] Model not found in database:
  - Requested model_type: deepseek
  - Mapped provider: deepseek
  - All enabled models in database:
    * Model A (provider=openai)
```

**解决方案**: 检查数据库中是否有 `provider=deepseek` 且 `is_enabled=true` 的模型配置。

#### 问题2: 提示词过长
**日志特征**:
```
⚠️ [DEBUG] System prompt too long (12000 chars), truncating to 8000 chars
  - Base agent prompt length: 2000 chars
  - Conversation context length: 6000 chars
  - IP persona prompt length: 4000 chars
```

**解决方案**: 已自动截断,如需调整阈值,修改 `MAX_SYSTEM_PROMPT_LENGTH` 常量。

#### 问题3: API调用失败
**日志特征**:
```
❌ [DEBUG] Stream generation failed:
  - Error Type: HTTPStatusError
  - Error Message: 503 Service Unavailable
  - Traceback: ...
```

**解决方案**: 检查模型API Key是否正确、Base URL是否可访问、账户余额是否充足。

## 测试建议

1. **先调用Debug接口**,确认配置无误
2. **查看日志**,观察每一步的执行情况
3. **逐步测试**:
   - 不带project_id(去掉IP人设)
   - 不带历史消息(单轮对话)
   - 简短提示词

## 数据库检查

确保数据库中有正确的模型配置:

```sql
-- 查看所有启用的模型
SELECT id, name, provider, model_id, base_url, is_enabled
FROM llm_models
WHERE is_enabled = true;

-- 确认provider字段值匹配
-- deepseek -> provider='deepseek'
-- doubao -> provider='doubao'
-- claude -> provider='anthropic'
```

## 后续优化建议

1. 将提示词长度限制配置化(存储在数据库中)
2. 实现Token计数而非字符计数
3. 添加请求重试机制
4. 实现流式响应的超时控制
5. 添加Prometheus监控指标

## 修改文件列表

- `backend/routers/client/creation.py` - 主要修复文件

## 联系方式

如有问题,请查看日志或使用debug接口获取详细信息。
