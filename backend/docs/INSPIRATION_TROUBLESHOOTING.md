# 灵感功能故障排查指南

## 500错误排查步骤

### 1. 检查数据库表是否存在

执行以下SQL检查表是否存在：

```sql
SHOW TABLES LIKE 'inspirations';
```

如果表不存在，执行迁移脚本：

```bash
# 方法1：直接执行SQL文件
mysql -u your_user -p your_database < backend/scripts/migration_add_inspirations.sql

# 方法2：在MySQL客户端中执行
source backend/scripts/migration_add_inspirations.sql
```

### 2. 检查后端日志

查看后端服务的日志输出，查找具体的错误信息：

```bash
# 如果使用uvicorn运行
# 错误信息会在控制台输出

# 如果使用日志文件
tail -f logs/app.log
```

### 3. 常见错误及解决方案

#### 错误1：表不存在 (Table 'xxx.inspirations' doesn't exist)
**解决方案：** 执行迁移脚本创建表

#### 错误2：字段不存在 (Unknown column 'xxx' in 'field list')
**解决方案：** 检查模型定义和数据库表结构是否一致

#### 错误3：外键约束错误 (Cannot add or update a child row)
**解决方案：** 确保 `users` 表和 `projects` 表存在，且外键关联正确

#### 错误4：JSON字段错误
**解决方案：** 确保MySQL版本支持JSON类型（MySQL 5.7+）

### 4. 验证数据库连接

确保数据库连接正常，可以执行：

```python
# 在Python中测试
from db.session import get_db
async for db in get_db():
    result = await db.execute("SELECT 1")
    print("Database connection OK")
    break
```

### 5. 检查模型注册

确保 `Inspiration` 模型已正确注册：

```python
# 检查 models/__init__.py
from models.inspiration import Inspiration, InspirationStatus

# 检查是否在 __all__ 中
```

### 6. 重启后端服务

修复问题后，重启后端服务：

```bash
# 如果使用uvicorn
pkill -f uvicorn
uvicorn main:app --reload

# 如果使用其他方式运行，请相应重启
```

## 测试接口

创建灵感测试：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/client/inspirations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "测试灵感内容",
    "tags": ["#测试"],
    "project_id": null
  }'
```

## 联系支持

如果问题仍未解决，请提供：
1. 完整的错误日志
2. 数据库版本信息
3. Python版本信息
4. 后端服务启动方式







