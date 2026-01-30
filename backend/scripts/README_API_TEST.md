# API连接测试脚本使用说明

## 功能说明

`test_api_connection.py` 是一个用于测试API接口和nginx中转服务可用性的工具脚本。

### 测试内容

1. **基本连接测试** - 测试HTTP连接和nginx服务器响应
2. **SSL证书测试** - 检查SSL证书有效性
3. **Nginx健康检查** - 查找并测试常见的健康检查端点
4. **Chat Completions API测试** - 测试完整的API接口功能

## 使用方法

### 基本用法

```bash
# 使用默认URL测试
python scripts/test_api_connection.py

# 指定URL测试
python scripts/test_api_connection.py https://47.82.181.13/api/v1/chat/completions

# 指定URL和API Key测试
python scripts/test_api_connection.py https://47.82.181.13/api/v1/chat/completions your_api_key_here
```

### 使用环境变量

脚本会自动从环境变量中读取API Key：

```bash
# 设置环境变量
export OPENAI_API_KEY=your_api_key_here
# 或
export AI_COLLECT_API_KEY=your_api_key_here

# 运行测试
python scripts/test_api_connection.py
```

### 在虚拟环境中运行

```bash
# 激活虚拟环境
cd backend
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 运行测试
python scripts/test_api_connection.py
```

## 输出说明

脚本会输出详细的测试结果，包括：

- ✅ 成功标记（绿色）
- ❌ 错误标记（红色）
- ⚠️ 警告标记（黄色）
- ℹ️ 信息标记（蓝色）

## 测试结果解读

### 基本连接测试
- **成功**: 服务器可以访问，nginx正常响应
- **失败**: 检查网络连接、防火墙、DNS解析

### SSL证书测试
- **成功**: SSL证书有效
- **失败**: 证书无效（但通常不影响使用，因为代码中设置了 `verify=False`）

### Nginx健康检查
- **成功**: 找到健康检查端点
- **失败**: 未找到（通常不影响API功能）

### API接口测试
- **200**: API请求成功
- **401**: 认证失败，检查API Key和网关密钥
- **404**: 接口不存在，检查URL路径
- **502**: 网关错误，检查nginx配置和后端服务
- **503**: 服务不可用，检查服务状态

## 常见问题

### 1. 连接失败
- 检查服务器是否启动
- 检查防火墙规则
- 检查DNS解析
- 检查端口是否开放

### 2. 认证失败 (401)
- 检查API Key是否正确
- 检查网关认证密钥 `X-My-Gate-Key` 是否正确（默认: `Huoyuan2026`）

### 3. 502 Bad Gateway
- 检查nginx配置
- 检查后端服务是否启动
- 检查nginx日志

### 4. SSL证书错误
- 如果只是警告，通常不影响使用
- 代码中已设置 `verify=False`，会忽略证书错误

## 示例输出

```
============================================================
  API连接测试工具
============================================================
测试时间: 2026-01-30 12:00:00

ℹ️  目标URL: https://47.82.181.13/api/v1/chat/completions
ℹ️  基础URL: https://47.82.181.13

============================================================
1. 基本连接测试 (GET请求)
============================================================

ℹ️  测试URL: https://47.82.181.13
✅ HTTP连接成功
ℹ️    - 状态码: 200
✅ 检测到nginx服务器: nginx/1.18.0

...

============================================================
测试总结
============================================================

ℹ️  总测试数: 4
ℹ️  通过: 3
ℹ️  失败: 1

  ✅ 通过 - 基本连接
  ⚠️ 失败 - SSL证书
  ✅ 通过 - Nginx健康检查
  ✅ 通过 - API接口

✅ 服务基本可用！
```

