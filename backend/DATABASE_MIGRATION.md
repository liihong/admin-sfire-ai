# 数据库迁移指南

## 当前数据库配置

### 开发环境配置（env.example）

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=sfire_admin
```

### 连接 URL 格式

- **异步连接**（应用使用）: `mysql+aiomysql://user:password@host:port/database?charset=utf8mb4`
- **同步连接**（迁移工具使用）: `mysql+pymysql://user:password@host:port/database?charset=utf8mb4`

---

## 迁移到线上 MySQL 数据库步骤

### 第一步：准备线上数据库

1. **创建数据库**
   ```sql
   CREATE DATABASE sfire_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **创建数据库用户（推荐）**
   ```sql
   -- 创建用户
   CREATE USER 'sfire_admin'@'%' IDENTIFIED BY 'your-strong-password';
   
   -- 授予权限
   GRANT ALL PRIVILEGES ON sfire_admin.* TO 'sfire_admin'@'%';
   FLUSH PRIVILEGES;
   ```

3. **验证连接**
   ```bash
   mysql -h your-mysql-host -P 3306 -u sfire_admin -p sfire_admin
   ```

### 第二步：配置环境变量

在 `backend` 目录下创建 `.env` 文件（如果不存在），配置线上数据库信息：

```env
# 应用配置
APP_NAME=SFire-Admin-API
APP_ENV=production
DEBUG=false
SECRET_KEY=your-production-secret-key-change-this

# 服务器配置
HOST=0.0.0.0
PORT=8000

# MySQL 数据库配置（线上）
MYSQL_HOST=your-mysql-host.com
MYSQL_PORT=3306
MYSQL_USER=sfire_admin
MYSQL_PASSWORD=your-strong-password
MYSQL_DATABASE=sfire_admin

# Redis 配置（线上）
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# JWT 配置
JWT_SECRET_KEY=your-production-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 跨域配置（线上前端地址）
CORS_ORIGINS=["https://your-frontend-domain.com"]

# 第三方 API 配置
TIKHUB_API_KEY=your-tikhub-api-key
OPENAI_API_KEY=your-openai-api-key
```

### 第三步：导出本地数据（可选）

如果需要迁移现有数据：

```bash
# 导出数据库结构
mysqldump -h localhost -u root -p --no-data sfire_admin > schema.sql

# 导出数据库数据
mysqldump -h localhost -u root -p --no-create-info sfire_admin > data.sql

# 导出完整数据库（结构+数据）
mysqldump -h localhost -u root -p sfire_admin > full_backup.sql
```

### 第四步：导入到线上数据库

```bash
# 导入数据库结构
mysql -h your-mysql-host -u sfire_admin -p sfire_admin < schema.sql

# 导入数据库数据
mysql -h your-mysql-host -u sfire_admin -p sfire_admin < data.sql

# 或导入完整备份
mysql -h your-mysql-host -u sfire_admin -p sfire_admin < full_backup.sql
```

### 第五步：使用初始化脚本（推荐）

如果线上数据库是全新的，使用初始化脚本：

```bash
cd backend

# 确保 .env 文件配置了线上数据库信息
python -m scripts.init_db
```

这会：
- 创建所有数据库表
- 初始化菜单数据
- 创建默认管理员账号（admin / admin123）

### 第六步：验证连接

```bash
cd backend

# 测试数据库连接
python -c "
import asyncio
from app.core.config import settings
from app.db.session import init_db, async_session_maker
from app.models.user import User
from sqlalchemy import select

async def test():
    await init_db()
    async with async_session_maker() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        print(f'Database connection: OK')
        print(f'Users count: {await db.scalar(select(func.count(User.id)))}')

asyncio.run(test())
"
```

### 第七步：更新应用配置

确保生产环境的配置正确：

1. **检查 `.env` 文件**
   - `APP_ENV=production`
   - `DEBUG=false`
   - 使用强密码和密钥

2. **检查数据库连接池配置**
   - 生产环境建议使用连接池
   - 当前配置：`pool_recycle=3600`（1小时回收连接）

3. **检查 Redis 配置**
   - 如果使用 Redis 缓存，确保 Redis 服务可用

---

## 常见问题排查

### 1. 连接超时

**错误**: `Can't connect to MySQL server`

**解决方案**:
- 检查 MySQL 服务是否运行
- 检查防火墙设置
- 检查 MySQL 用户是否有远程连接权限
- 检查 `bind-address` 配置（MySQL 配置文件）

### 2. 认证失败

**错误**: `Access denied for user`

**解决方案**:
- 检查用户名和密码是否正确
- 检查用户是否有访问数据库的权限
- 检查用户的主机限制（`'user'@'%'` vs `'user'@'localhost'`）

### 3. 字符编码问题

**错误**: 中文乱码

**解决方案**:
- 确保数据库使用 `utf8mb4` 字符集
- 确保连接 URL 包含 `?charset=utf8mb4`
- 检查表字段的字符集设置

### 4. SSL 连接问题

如果线上数据库要求 SSL 连接，修改连接 URL：

```python
# 在 app/core/config.py 的 MYSQL_DATABASE_URL 中添加 SSL 参数
f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
"?charset=utf8mb4&ssl_disabled=false"
```

---

## 数据库表结构

当前项目包含以下表：

1. **users** - 用户表
2. **compute_logs** - 算力变动记录表
3. **menus** - 菜单表

所有表都包含：
- `id` - 主键（BigInteger）
- `created_at` - 创建时间
- `updated_at` - 更新时间

---

## 安全建议

1. **使用专用数据库用户**
   - 不要使用 `root` 用户
   - 只授予必要的权限

2. **使用强密码**
   - 密码长度至少 16 位
   - 包含大小写字母、数字、特殊字符

3. **启用 SSL 连接**
   - 生产环境建议启用 SSL

4. **定期备份**
   ```bash
   # 每日备份脚本示例
   mysqldump -h your-mysql-host -u sfire_admin -p sfire_admin | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

5. **保护 .env 文件**
   - 不要将 `.env` 文件提交到 Git
   - 使用环境变量或密钥管理服务

---

## 迁移检查清单

- [ ] 创建线上数据库
- [ ] 创建数据库用户并授予权限
- [ ] 配置 `.env` 文件（线上数据库信息）
- [ ] 测试数据库连接
- [ ] 运行初始化脚本或导入数据
- [ ] 验证数据完整性
- [ ] 更新应用配置（APP_ENV, DEBUG 等）
- [ ] 测试应用功能
- [ ] 配置数据库备份策略
- [ ] 监控数据库性能




