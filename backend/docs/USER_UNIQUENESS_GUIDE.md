# 用户唯一性绑定指南

## 概述

本文档说明用户唯一性绑定机制，确保手机号、openid、unionid 的一致性，避免重复用户问题。

## 用户标识字段说明

### 1. openid
- **作用**：微信小程序用户唯一标识（同一小程序内唯一）
- **特点**：每个小程序都有独立的 openid
- **问题**：在微信开发者工具中测试时，会返回 mock openid（`o_mock_` 开头）

### 2. unionid
- **作用**：微信开放平台用户唯一标识（跨小程序、跨平台唯一）
- **特点**：同一微信用户在不同小程序中的 unionid 相同
- **优势**：最可靠的用户唯一标识
- **限制**：需要用户授权，且小程序需要绑定到微信开放平台

### 3. phone（手机号）
- **作用**：用户手机号
- **特点**：用户手动授权获取
- **优势**：用户可识别，便于客服和管理

## 用户查找优先级

登录时的用户查找优先级（从高到低）：

1. **unionid**（最可靠，跨平台唯一）
2. **openid**（小程序内唯一）
3. **phone**（手机号，用户可识别）

## 用户绑定逻辑

### 登录流程

1. **获取微信信息**
   - 调用微信 API 获取 openid 和 unionid
   - 如果提供了 phone_code，获取手机号

2. **查找用户**
   - 优先通过 unionid 查找（最可靠）
   - 如果找不到，通过 openid 查找
   - 如果还找不到，通过手机号查找

3. **更新绑定信息**
   - 如果找到用户，更新 openid、unionid、手机号（如果不同）
   - 如果找不到用户，创建新用户

### 绑定规则

- **unionid**：如果获取到，优先更新（因为它是跨平台唯一标识）
- **openid**：如果当前为空或不同，更新为新值
- **phone**：如果当前为空，绑定新手机号；如果已存在但不同，保持原有手机号（记录警告）

## 历史数据同步

### 问题

数据库中可能存在 unionid 为空的用户，这些是历史数据。

### 解决方案

1. **自动更新**（推荐）
   - 用户重新登录小程序时，会自动更新 unionid
   - 无需人工干预

2. **查询统计**
   ```bash
   # 使用脚本查询统计信息
   python backend/scripts/sync_user_unionid.py --stats
   
   # 查询 unionid 为空的用户列表
   python backend/scripts/sync_user_unionid.py --query --limit 100
   ```

3. **管理接口**
   ```http
   GET /api/admin/users/statistics/unionid
   ```
   返回统计信息：
   - 总用户数
   - 有 unionid 的用户数
   - 没有 unionid 的用户数
   - 有 openid 但没有 unionid 的用户数
   - 有手机号但没有 unionid 的用户数

## 代码改进

### 1. 登录逻辑优化

**文件**：`backend/routers/client/auth.py`

**改进点**：
- 优先通过 unionid 查找用户
- 每次登录都更新 unionid（如果获取到）
- 更新 openid 和手机号绑定
- 添加详细的日志记录

**关键代码**：
```python
# 优先通过 unionid 查找用户（跨平台识别，最可靠）
if unionid:
    user = await user_service.get_user_by_unionid(unionid)

# 如果通过 unionid 没找到，再通过 openid 查找
if not user:
    user = await user_service.get_user_by_openid(openid)

# 如果还找不到，通过手机号查找
if not user and phone_number:
    user = await user_service.get_user_by_phone(phone_number)
```

### 2. 唯一性检查

**改进点**：
- 创建用户前检查 openid 和手机号冲突
- 如果通过手机号找到用户，绑定 openid 和 unionid
- 防止重复用户创建

### 3. 数据修复脚本

**文件**：`backend/scripts/sync_user_unionid.py`

**功能**：
- 查询 unionid 为空的用户
- 统计用户 unionid 情况
- 提供数据修复参考

**使用方法**：
```bash
# 查看统计信息
python backend/scripts/sync_user_unionid.py --stats

# 查询 unionid 为空的用户（最多100个）
python backend/scripts/sync_user_unionid.py --query --limit 100
```

### 4. 管理接口

**文件**：`backend/routers/admin/users.py`

**接口**：`GET /api/admin/users/statistics/unionid`

**功能**：返回用户 unionid 统计信息

## 注意事项

### 1. Mock OpenID

在微信开发者工具中测试时，会返回 mock openid（`o_mock_` 开头）。这是正常的测试行为，不影响生产环境。

**检测**：代码会自动检测并记录警告日志。

### 2. UnionID 获取限制

- unionid 只能通过微信 API 获取
- 需要用户重新登录小程序才能获取
- 小程序需要绑定到微信开放平台

### 3. 数据一致性

- 优先使用 unionid 作为用户唯一标识
- 如果 unionid 不可用，使用 openid
- 手机号作为辅助标识，用于用户识别

### 4. 冲突处理

- 如果手机号已存在但 openid 不同，记录警告但不更新手机号
- 如果 unionid 不一致，记录错误但不更新（保持原有 unionid）
- 如果 openid 不一致，更新为新值（因为 openid 可能变化）

## 最佳实践

1. **用户登录时**
   - 确保每次登录都更新 unionid（如果获取到）
   - 更新 openid 和手机号绑定
   - 记录详细的日志，便于排查问题

2. **数据修复**
   - 定期查询 unionid 为空的用户
   - 引导用户重新登录小程序，自动更新 unionid
   - 使用管理接口监控数据同步情况

3. **问题排查**
   - 查看日志中的 openid 和 unionid 信息
   - 检查是否有 mock openid 警告
   - 查看用户查找和绑定过程的日志

## 相关文件

- `backend/routers/client/auth.py` - 登录逻辑
- `backend/services/user/user.py` - 用户服务
- `backend/models/user.py` - 用户模型
- `backend/scripts/sync_user_unionid.py` - 数据修复脚本
- `backend/routers/admin/users.py` - 管理接口

## 更新日志

- 2024-XX-XX: 优化用户查找逻辑，优先使用 unionid
- 2024-XX-XX: 添加 unionid 自动更新机制
- 2024-XX-XX: 创建数据修复脚本和管理接口






