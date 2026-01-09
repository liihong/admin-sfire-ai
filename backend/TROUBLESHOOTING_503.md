# 503错误排查指南

## 问题描述
`/api/v1/client/chat` 接口返回:
```json
data: {"error": {"message": "API 请求失败: HTTP 503", "type": "APIError"}}
```

## 快速排查步骤

### 步骤1: 检查数据库中的模型配置

运行数据库检查脚本:
```bash
cd backend
python check_db_config.py
```

这将显示:
- 所有模型配置
- 启用的模型
- Provider映射是否正确
- 配置问题诊断

### 步骤2: 查看详细错误日志

重启后端服务,然后调用chat接口,查看控制台输出:

```bash
cd backend
python main.py
```

调用接口后,你会看到类似这样的详细日志:

```
❌ [API] LLM API请求失败:
  - HTTP Status: 503
  - API URL: https://api.deepseek.com/v1/chat/completions
  - Model ID: deepseek-chat
  - Model Type: 1
  - Response Headers: {...}
  - Error Response: <错误详情>
  - Request Messages Count: 2
  - System Prompt Length: 1500 chars
  ⚠️ 503错误可能原因:
    1. API网关过载或不可用
    2. Base URL配置错误: ...
    3. 网关认证密钥(X-My-Gate-Key)无效
    4. 外部API服务暂时不可用
    💡 建议: 检查数据库中的base_url和api_key配置
```

### 步骤3: 常见问题修复

#### 问题1: Base URL配置错误

**症状**: 日志显示 `API URL` 不正确

**解决方案**:
```sql
-- 检查base_url配置
SELECT id, name, provider, base_url FROM llm_models WHERE is_enabled = true;

-- 如果base_url包含完整路径,修复它:
UPDATE llm_models
SET base_url = 'https://api.deepseek.com'  -- 只需要域名,不要/v1/chat/completions
WHERE id = 1;
```

**正确的base_url格式**:
- DeepSeek: `https://api.deepseek.com` 或 `https://api.deepseek.com/v1`
- Claude (官方): `https://api.anthropic.com`
- Claude (代理): 你的代理地址
- 豆包: 你的豆包API地址

#### 问题2: Provider字段不匹配

**症状**: 日志显示"未找到启用的模型"

**解决方案**: 确保provider字段值正确:
- DeepSeek模型: `provider = 'deepseek'`
- 豆包模型: `provider = 'doubao'`
- Claude模型: `provider = 'anthropic'`

```sql
-- 修复provider字段
UPDATE llm_models SET provider = 'anthropic' WHERE name LIKE '%claude%';
UPDATE llm_models SET provider = 'deepseek' WHERE name LIKE '%deepseek%';
UPDATE llm_models SET provider = 'doubao' WHERE name LIKE '%豆包%' OR name LIKE '%doubao%';
```

#### 问题3: API Key未配置或无效

**症状**: 401或403错误,或503(网关拒绝)

**解决方案**:
```sql
-- 检查哪些模型没有API Key
SELECT id, name FROM llm_models WHERE is_enabled = true AND (api_key IS NULL OR api_key = '');

-- 更新API Key
UPDATE llm_models
SET api_key = 'sk-你的实际API密钥'
WHERE id = 1;
```

#### 问题4: 网关问题 (最可能导致503)

**症状**: 日志显示HTTP 503,且使用的是网关

**可能原因**:
1. API网关过载
2. 网关认证密钥 `X-My-Gate-Key: Huoyuan2026` 无效
3. 网关配置问题

**临时解决方案 - 跳过网关直连**:

如果你有直连的API密钥,修改代码临时移除网关:

```python
# 在 services/ai.py 中,注释掉网关密钥
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    # "X-My-Gate-Key": "Huoyuan2026",  # 临时注释
}
```

或者在数据库中配置一个不经过网关的base_url。

#### 问题5: 外部API服务不可用

**症状**: 所有配置都正确,但仍然503

**解决方案**:
1. 检查DeepSeek/Claude服务状态
2. 尝试使用curl直接测试API:
```bash
curl -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"hi"}]}'
```

### 步骤4: 使用Debug接口验证

在修复后,使用debug接口验证配置:

```bash
curl -X POST "http://172.18.0.1:9000/api/v1/client/chat/debug" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messages": [{"role": "user", "content": "test"}],
    "model_type": "deepseek",
    "agent_type": "1",
    "stream": false
  }'
```

确认:
- `found_model` 不为null
- `has_api_key` 为true
- `is_enabled` 为true
- `provider` 匹配请求的 `model_type`

## 最可能的原因(按概率排序)

1. **Base URL配置错误** (60%)
   - 包含完整路径如 `/v1/chat/completions`
   - 域名错误
   - 使用了网关地址但网关不可用

2. **Provider字段不匹配** (20%)
   - 请求`model_type=deepseek`但数据库中provider字段值不是`deepseek`

3. **API Key无效** (10%)
   - 未配置或配置错误

4. **网关问题** (8%)
   - 网关过载或配置错误

5. **外部API不可用** (2%)
   - DeepSeek/Claude服务暂时不可用

## 快速修复清单

- [ ] 运行 `python check_db_config.py` 检查配置
- [ ] 查看后端日志中的详细错误信息
- [ ] 确认启用的模型至少有一个
- [ ] 确认启用的模型有API Key
- [ ] 确认Base URL格式正确(只包含域名或域名+/v1)
- [ ] 确认Provider字段值匹配 (deepseek/doubao/anthropic)
- [ ] 尝试使用curl直接测试API
- [ ] 如果使用网关,尝试临时移除网关直连
