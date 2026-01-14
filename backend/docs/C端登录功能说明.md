# C端用户登录功能实现说明

## 功能概述

实现了C端用户(小程序用户)在PC端的账号密码登录功能,包括以下安全验证和业务逻辑:

### 实现的功能

#### 1. 密码加密传输 ✅
- **前端**: 使用 MD5 对密码进行加密
- **后端**: 接收 MD5 加密后的密码,与数据库中的 bcrypt 哈希进行验证
- **文件位置**:
  - 前端加密工具: `frontend/src/utils/encrypt.ts`
  - 后端验证逻辑: `backend/routers/client/web_auth.py:88`

#### 2. 登录响应增加 updated_at 字段 ✅
- 登录成功后返���用户的 `updated_at` 时间戳
- 格式: `YYYY-MM-DD HH:MM:SS`
- **文件位置**: `backend/routers/client/web_auth.py:143-145`

#### 3. 会员过期检验 ✅
- 检查用户的 `vip_expire_date` 字段
- 如果会员已过期,在响应中添加标识:
  - `vip_expired`: true/false
  - `vip_expire_date`: 过期日期
- 前端显示警告提示用户续费
- **文件位置**:
  - 后端检查逻辑: `backend/routers/client/web_auth.py:106-112`
  - 前端提示逻辑: `frontend/src/stores/modules/miniprogramUser.ts:189-195`

#### 4. 账号状态检验 (is_active) ✅
- 验证用户的 `is_active` 字段
- 如果账号被封禁(is_active=false),返回错误提示:
  - "账号已被封禁，请联系管理员"
- **文件位置**: `backend/routers/client/web_auth.py:82-84`

## 接口说明

### 登录接口

**URL**: `POST /api/v1/client/auth/account/login`

**请求参数**:
```json
{
  "phone": "13800138000",      // 手机号
  "password": "md5_hashed_pass" // MD5加密后的密码
}
```

**响应参数**:
```json
{
  "code": 200,
  "data": {
    "success": true,
    "token": "jwt_token_string",
    "userInfo": {
      "openid": "wx_openid",
      "nickname": "用户昵称",
      "avatarUrl": "头像URL",
      "gender": 0,
      "city": "",
      "province": "",
      "country": ""
    },
    "updated_at": "2024-01-14 12:00:00",  // 账号更新时间
    "vip_expired": false,                  // 会员是否过期
    "vip_expire_date": "2024-12-31"       // 会员到期日期
  },
  "msg": "登录成功"
}
```

**错误响应**:

1. 手机号或密码错误:
```json
{
  "code": 400,
  "msg": "手机号或密码错误"
}
```

2. 账号未设置密码:
```json
{
  "code": 400,
  "msg": "该账号未设置密码，请使用微信扫码登录"
}
```

3. 账号已被封禁:
```json
{
  "code": 400,
  "msg": "账号已被封禁，请联系管理员"
}
```

## 密码验证流程

1. **前端**: 用户输入明文密码 → MD5加密 → 发送到后端
2. **后端**:
   - 接收MD5加密的密码
   - 从数据库获取用户的bcrypt哈希密码
   - 使用bcrypt验证MD5密码与哈希密码是否匹配
   - 返回验证结果

**示例**:
```
原始密码: 123456
前端MD5: e10adc3949ba59abbe56e057f20f883e
数据库bcrypt: $2b$12$...
后端验证: bcrypt.checkpw(md5_password, bcrypt_hash) → True/False
```

## 测试

### 生成测试用户

运行测试密码生成工具:
```bash
cd backend
python scripts/test_password.py
```

该工具会:
1. 生成密码的MD5和bcrypt哈希
2. 提供SQL插入语句
3. 演示完整的验证流程

### 手动测试

1. 创建测试用户:
```sql
INSERT INTO users (username, phone, password_hash, nickname, is_active, level, vip_expire_date)
VALUES ('test_user', '13800138000', '$2b$12$...', '测试用户', 1, 'normal', NULL);
```

2. 前端登录:
   - 手机号: `13800138000`
   - 密码: `123456` (或其他测试密码)

3. 验证功能:
   - ✓ 密码正确可以登录
   - ✓ 密码错误返回提示
   - ✓ 封禁账号无法登录
   - ✓ 过期会员显示续费提示

## 相关文件

### 前端
- `frontend/src/utils/encrypt.ts` - MD5加密工具
- `frontend/src/stores/modules/miniprogramUser.ts` - 用户登录逻辑
- `frontend/src/api/modules/miniprogram.ts` - 接口类型定义
- `frontend/src/views/miniprogram/login/index.vue` - 登录页面

### 后端
- `backend/routers/client/web_auth.py` - 登录接口实现
- `backend/core/security.py` - 密码验证工具
- `backend/models/user.py` - 用户数据模型
- `backend/scripts/test_password.py` - 测试密码生成工具

## 安全说明

1. **密码传输**: 前端使用MD5加密,避免明文传输
2. **密码存储**: 后端使用bcrypt哈希,带随机盐值,安全可靠
3. **账号状态**: 检查is_active字段,防止封禁用户登录
4. **会员管理**: 检查vip_expire_date,提示过期用户续费

## 注意事项

1. MD5仅用于传输加密,不是最终的安全方案
2. 建议后续升级为RSA非对称加密或使用HTTPS
3. 数据库密码始终使用bcrypt哈希存储
4. 会员过期不影响登录,仅显示提示
5. 账号封禁将阻止登录
