# 🪙 火源币算力系统 - 快速使用指南

## 📖 什么是��源币?

火源币是本平台的算力计量单位,用于衡量用户使用AI模型消耗的资源。

**换算公式**:
```
消耗火源币 = [(输入Token × 1.0) + (输出Token × 3.0) + 10] × 模型倍率 × 0.001
```

**示例**:
- 使用Claude 3.5对话(1000输入+500输出) = **2.51火源币**
- 使用GPT-4o-mini对话(1000输入+500输出) = **0.127火源币**

---

## 🎯 核心特性

### 1. 预冻结机制
用户发起请求时,系统会预冻结足够的火源币,生成结束后多退少补。

**好处**:
- 防止用户余额不足时产生大量API费用
- 确保每笔请求都能成功扣费

### 2. 多模型倍率
不同模型有不同的倍率系数:

| 模型 | 倍率 | 说明 |
|------|------|------|
| Claude 3.5 Sonnet | 1.0x | 基准模型,质量高 |
| GPT-4o | 1.5x | 综合能力更强 |
| GPT-4o-mini | 0.1x | 极速版,价格低 |
| DeepSeek-chat | 0.15x | 高性价比 |

### 3. 内容安全审查
- **前置审查**: 用户输入包含敏感词时直接拦截,不扣费
- **后置审查**: AI输出包含敏感词时中断,扣除基础费的10%作为处罚

### 4. 错误全额退款
如果API调用失败(5xx错误),系统会全额退还预冻结的火源币。

---

## 🔧 API使用指南

### 查询余额

```bash
GET /api/v1/client/coin/balance
Authorization: Bearer YOUR_TOKEN
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "balance": 1000.00,          // 总余额
    "frozen_balance": 50.00,     // 冻结中
    "available_balance": 950.00  // 可用余额
  },
  "msg": "查询成功"
}
```

### 查询流水

```bash
GET /api/v1/client/coin/transactions?pageNum=1&pageSize=10
Authorization: Bearer YOUR_TOKEN
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "list": [
      {
        "id": 1,
        "type": "consume",
        "typeName": "消耗",
        "amount": -2.51,
        "beforeBalance": 1000.00,
        "afterBalance": 997.49,
        "remark": "AI对话消耗 - 输入Token: 1000, 输出Token: 500",
        "taskId": "task-uuid",
        "createTime": "2025-01-10T10:00:00"
      }
    ],
    "pageNum": 1,
    "pageSize": 10,
    "total": 100
  },
  "msg": "查询成功"
}
```

### 计算消耗

```bash
POST /api/v1/client/coin/calculate
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "input_tokens": 1000,
  "output_tokens": 500,
  "model_id": 1
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "estimated_cost": 2.51,
    "breakdown": {
      "input_tokens": 1000,
      "output_tokens": 500,
      "input_weight": 1.0,
      "output_weight": 3.0,
      "base_fee": 10.0,
      "rate_multiplier": 1.0,
      "input_cost": 1000.0,
      "output_cost": 1500.0,
      "subtotal": 2510.0,
      "total": 2.51
    }
  },
  "msg": "计算成功"
}
```

### 估算消耗(根据文本)

```bash
POST /api/v1/client/coin/estimate
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "input_text": "你好,请介绍一下Python编程语言",
  "model_id": 1,
  "estimated_output_tokens": 1000  // 可选
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "estimated_cost": 3.62,
    "breakdown": { ... }
  },
  "msg": "估算成功"
}
```

---

## 💻 代码集成示例

### Python示例

```python
import httpx

async def chat_with_deduction(user_token: str, message: str):
    """带算力扣除的对话"""

    # 1. 查询余额
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://your-api.com/api/v1/client/coin/balance",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        balance_data = response.json()
        available = balance_data["data"]["available_balance"]

        if available < 1.0:
            print("余额不足,请充值")
            return

    # 2. 估算消耗
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-api.com/api/v1/client/coin/estimate",
            headers={
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            },
            json={
                "input_text": message,
                "model_id": 1
            }
        )
        estimate_data = response.json()
        estimated_cost = estimate_data["data"]["estimated_cost"]

        print(f"预计消耗: {estimated_cost} 火源币")

    # 3. 调用对话接口(自动扣除算力)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-api.com/api/v1/client/chat",
            headers={
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            },
            json={
                "message": message,
                "model_id": 1,
                "stream": True
            },
            timeout=60.0
        )

        # 流式输出
        async for line in response.aiter_lines():
            if line:
                print(line)

    # 4. 查询最终扣费
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://your-api.com/api/v1/client/coin/transactions?pageNum=1&pageSize=1",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        transaction_data = response.json()
        actual_cost = abs(transaction_data["data"]["list"][0]["amount"])

        print(f"实际消耗: {actual_cost} 火源币")
```

---

## 🔍 常见问题

### Q1: 为什么有时候预冻结的金额比实际消耗多?

**A**: 预冻结是按最大可能消耗估算的,实际生成结束后会按真实Token数结算,多退少补。这就像餐厅用餐先押金,吃完按实际消费结算一样。

### Q2: 如果生成中断了会扣费吗?

**A**: 分情况:
- **API错误**(如5xx): 全额退款,不扣费
- **内容违规**: 扣除基础费的10%作为处罚
- **用户主动中断**: 按已生成的内容比例扣费

### Q3: 不同模型价格差异有多大?

**A**: 很大!以1000输入+500输出为例:
- GPT-4o-mini: 0.127火源币
- DeepSeek-chat: 0.19火源币
- Claude 3.5 Sonnet: 2.51火源币
- Claude 3 Opus: 5.02火源币

**性价比推荐**: 日常聊天用 GPT-4o-mini,复杂任务用 Claude 3.5 Sonnet

### Q4: 火源币如何充值?

**A**: 目前需要管理员手动充值,后续会开放在线支付接口。

### Q5: 如何查看详细的费用明细?

**A**: 调用 `/coin/calculate` 接口会返回详细的费用明细,包括:
- 输入Token数量和成本
- 输出Token数量和成本
- 基础调度费
- 模型倍率
- 最终总费用

---

## 📊 费用计算器

### 简易计算公式

| 场景 | 输入 | 输出 | 模型 | 消耗(火源币) |
|------|------|------|------|-------------|
| 简单对话 | 500 | 300 | GPT-4o-mini | 0.06 |
| 代码生成 | 1500 | 800 | Claude 3.5 | 4.03 |
| 长文本分析 | 3000 | 1500 | Claude 3.5 | 8.77 |
| 快速问答 | 200 | 100 | GPT-4o-mini | 0.02 |

**估算方法**:
- 中文文本约 1字符 = 0.6 Token
- 英文文本约 1字符 = 0.25 Token
- 混合文本约 1字符 = 0.4 Token

---

## 🎓 最佳实践

### 1. 选择合适的模型
- **日常聊天**: GPT-4o-mini (便宜快速)
- **代码生成**: DeepSeek-coder (专业便宜)
- **复杂推理**: Claude 3.5 Sonnet (质量高)
- **最高质量**: Claude 3 Opus (价格高)

### 2. 优化输入长度
- 删除不必要的上下文
- 使用精简的提示词
- 避免重复发送相同内容

### 3. 控制输出长度
- 设置合理的 `max_tokens` 参数
- 使用精确的指令减少冗余输出

### 4. 定期查看流水
- 监控自己的算力消耗
- 发现异常及时联系客服

---

## 📞 技术支持

如有问题,请联系:
- 技术文档: `/docs/COIN_SYSTEM_REPORT.md`
- API文档: `/docs` (Swagger UI)
- 问题反馈: GitHub Issues

---

**祝您使用愉快! 🎉**
