# AI智能填写接口配置说明

## 环境变量配置

AI智能填写接口（`/api/v1/client/projects/ai-collect` 和 `/api/v1/client/projects/ai-compress`）支持通过环境变量配置模型参数。

### 配置优先级

1. **数据库模型配置**（最高优先级）
   - 如果 `AI_COLLECT_MODEL_ID` 是数据库中的模型ID，优先使用数据库中的 `api_key` 和 `base_url`

2. **AI_COLLECT 专用环境变量**（次优先级）
   - `AI_COLLECT_API_KEY`: AI采集接口专用的API Key
   - `AI_COLLECT_BASE_URL`: AI采集接口专用的Base URL

3. **通用环境变量**（最低优先级）
   - `OPENAI_API_KEY`: 通用OpenAI API Key
   - 默认 Base URL: `https://api.deepseek.com`

### 环境变量说明

在 `.env` 文件中添加以下配置：

```bash
# AI智能填写接口配置
# 模型ID：可以是数据库中的模型ID（数字），或模型标识（如 "doubao", "deepseek"）
# 如果为空，默认使用 "doubao"
AI_COLLECT_MODEL_ID=doubao

# AI采集接口专用的API Key（可选）
# 如果设置了此变量，将优先使用此API Key，而不是数据库配置或通用配置
AI_COLLECT_API_KEY=your-api-key-here

# AI采集接口专用的Base URL（可选）
# 如果设置了此变量，将优先使用此Base URL
# 如果不设置，将使用模型默认的Base URL或通用Base URL
AI_COLLECT_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### 配置示例

#### 示例1：使用豆包（Doubao）模型

```bash
AI_COLLECT_MODEL_ID=doubao
AI_COLLECT_API_KEY=your-doubao-api-key
AI_COLLECT_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

#### 示例2：使用DeepSeek模型

```bash
AI_COLLECT_MODEL_ID=deepseek
AI_COLLECT_API_KEY=your-deepseek-api-key
AI_COLLECT_BASE_URL=https://api.deepseek.com
```

#### 示例3：使用数据库中的模型配置

```bash
# 假设数据库中有ID为1的模型配置
AI_COLLECT_MODEL_ID=1
# 如果数据库模型已配置api_key和base_url，则无需设置以下变量
# AI_COLLECT_API_KEY=
# AI_COLLECT_BASE_URL=
```

#### 示例4：使用通用配置（向后兼容）

```bash
# 不设置AI_COLLECT相关变量，使用通用配置
OPENAI_API_KEY=your-openai-api-key
# 将使用默认Base URL: https://api.deepseek.com
```

### 注意事项

1. **模型ID格式**：
   - 数字字符串（如 "1", "2"）：从数据库查找对应ID的模型配置
   - 模型标识（如 "doubao", "deepseek"）：从数据库查找对应model_id的模型配置
   - 如果都找不到，使用环境变量配置

2. **Base URL格式**：
   - 不需要包含 `/chat/completions` 路径
   - 不需要包含版本号（如 `/v1`），系统会自动处理
   - 示例：`https://ark.cn-beijing.volces.com/api/v3` ✅
   - 错误：`https://ark.cn-beijing.volces.com/api/v3/chat/completions` ❌

3. **API Key验证**：
   - 如果所有配置都未设置API Key，接口会返回错误
   - 建议至少设置 `AI_COLLECT_API_KEY` 或 `OPENAI_API_KEY` 之一

### 测试配置

配置完成后，可以通过以下方式测试：

1. 调用 `/api/v1/client/projects/ai-collect` 接口
2. 查看后端日志，确认使用的API Key和Base URL
3. 如果配置错误，接口会返回明确的错误信息














