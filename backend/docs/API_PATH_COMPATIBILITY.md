# API路径兼容性说明文档

## 一、概述

本文档说明架构重构后API路径的兼容性情况。**重要：重构后所有API路径完全不变，前端无需任何修改。**

## 二、API路径结构

### 2.1 路径前缀

所有API路径遵循以下结构：

```
/api/{version}/{client_type}/{domain}/{resource}/{action}
```

- `version`: v1, v2（版本号）
- `client_type`: admin（管理端）, client（客户端）
- `domain`: agent, conversation, user等（领域）
- `resource`: agents, conversations等（资源）
- `action`: list, create, update等（操作）

### 2.2 路径注册方式

路径前缀在`main.py`中统一注册：

```python
# main.py
app.include_router(client_router, prefix="/api/v1/client", tags=["C端接口"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["B端接口"])
app.include_router(admin_v2_router, prefix="/api/v2/admin", tags=["B端接口（v2）"])
app.include_router(client_v2_router, prefix="/api/v2/client", tags=["C端接口（v2）"])
```

## 三、路径映射表

### 3.1 管理端（Admin）API路径

| 功能 | v1路径 | v2路径 | 说明 |
|------|--------|--------|------|
| Agent列表 | `/api/v1/admin/agents` | `/api/v2/admin/agents/list` | v2版本路径不同 |
| Agent详情 | `/api/v1/admin/agents/{id}` | `/api/v2/admin/agents/{id}` | 路径相同 |
| Agent创建 | `/api/v1/admin/agents` (POST) | `/api/v2/admin/agents` (POST) | 路径相同 |
| Agent更新 | `/api/v1/admin/agents/{id}` (PUT) | `/api/v2/admin/agents/{id}` (PUT) | 路径相同 |
| 技能库列表 | - | `/api/v2/admin/skill-library` | 仅v2版本 |
| Prompt预览 | - | `/api/v2/admin/agents/preview-prompt` | 仅v2版本 |
| 路由预览 | - | `/api/v2/admin/agents/preview-routing` | 仅v2版本 |

### 3.2 客户端（Client）API路径

| 功能 | v1路径 | v2路径 | 说明 |
|------|--------|--------|------|
| Agent列表 | `/api/v1/client/agents` | - | 仅v1版本 |
| Agent执行 | `/api/v1/client/chat` (POST) | `/api/v2/client/execution/agents/{id}/execute` | v2版本路径不同 |
| 快速对话 | `/api/v1/client/chat/quick` (POST) | - | 仅v1版本 |
| 项目IP人设 | - | `/api/v2/client/execution/projects/{id}/persona` | 仅v2版本 |
| Prompt构建 | - | `/api/v2/client/execution/build-prompt` | 仅v2版本 |
| 会话列表 | `/api/v1/client/conversations` | `/api/v1/client/conversations` | 路径相同 |
| 会话创建 | `/api/v1/client/conversations` (POST) | `/api/v1/client/conversations` (POST) | 路径相同 |

## 四、重构前后对比

### 4.1 重构前

```
routers/
├── admin/
│   ├── agents.py          # v1路由
│   └── v2/
│       └── agents_v2.py  # v2路由
└── client/
    ├── creation.py        # v1路由
    └── v2/
        └── execution.py   # v2路由
```

### 4.2 重构后

```
routers/
├── admin/
│   └── agent.py           # v1和v2路由合并
└── client/
    └── agent.py          # v1和v2路由合并
```

### 4.3 路径保持不变

**重构前后API路径完全一致**：

- 路径前缀在`main.py`中统一管理，保持不变
- 路由文件内部路径保持不变
- 仅内部代码组织方式改变

## 五、路由注册方式

### 5.1 重构前

```python
# routers/admin/__init__.py
admin_router.include_router(agents.router, prefix="/agents")

# routers/admin/v2/__init__.py
admin_v2_router.include_router(agents_v2.router)
```

### 5.2 重构后

```python
# routers/admin/agent.py
router_v1 = APIRouter(prefix="/agents", tags=["Agent管理"])
router_v2 = APIRouter(prefix="/agents", tags=["Agent管理（v2）"])

# routers/admin/__init__.py
admin_router.include_router(agent.router_v1)
admin_v2_router.include_router(agent.router_v2)
```

### 5.3 路径保持不变

- v1路径：`/api/v1/admin/agents`（通过admin_router注册）
- v2路径：`/api/v2/admin/agents`（通过admin_v2_router注册）
- 路径前缀在`main.py`中统一管理，保持不变

## 六、前端适配说明

### 6.1 无需修改

**重构后前端无需任何修改**：

- API路径完全不变
- 请求方式不变（GET、POST、PUT、DELETE）
- 请求参数不变
- 响应格式不变

### 6.2 前端代码示例

前端代码保持不变：

```typescript
// 前端API调用示例（无需修改）
// v1版本
GET /api/v1/admin/agents
POST /api/v1/admin/agents
PUT /api/v1/admin/agents/{id}

// v2版本
GET /api/v2/admin/agents/list
POST /api/v2/client/execution/agents/{id}/execute
```

## 七、测试验证

### 7.1 测试清单

重构后需要验证以下路径：

**管理端（Admin）**：
- [ ] `/api/v1/admin/agents` - Agent列表
- [ ] `/api/v1/admin/agents/{id}` - Agent详情
- [ ] `/api/v2/admin/agents/list` - Agent列表（v2）
- [ ] `/api/v2/admin/agents/{id}` - Agent详情（v2）
- [ ] `/api/v2/admin/skill-library` - 技能库列表

**客户端（Client）**：
- [ ] `/api/v1/client/agents` - Agent列表
- [ ] `/api/v1/client/chat` - Agent执行
- [ ] `/api/v2/client/execution/agents/{id}/execute` - Agent执行（v2）
- [ ] `/api/v2/client/execution/projects/{id}/persona` - 项目IP人设

### 7.2 测试方法

1. **使用Postman或curl测试**：
   ```bash
   curl -X GET http://localhost:8000/api/v1/admin/agents
   curl -X GET http://localhost:8000/api/v2/admin/agents/list
   ```

2. **使用Swagger UI测试**：
   - 访问 `http://localhost:8000/docs`
   - 测试所有API端点

3. **前端集成测试**：
   - 运行前端应用
   - 测试所有功能模块
   - 确保API调用正常

## 八、注意事项

### 8.1 路径前缀管理

- 路径前缀在`main.py`中统一管理
- 不要在各路由文件中硬编码路径前缀
- 修改路径前缀只需修改`main.py`

### 8.2 版本管理

- v1和v2版本通过不同的router注册
- 路由文件内部通过路由分组区分版本
- Schema版本通过命名空间区分

### 8.3 向后兼容

- 重构后保持所有API路径不变
- 不删除任何现有API端点
- 新增API端点遵循现有路径规范

## 九、常见问题

### Q1: 重构后前端需要修改吗？

A: **不需要**。所有API路径完全不变，前端无需任何修改。

### Q2: 如何添加新的API端点？

A: 在对应的路由文件中添加新的路由函数，遵循现有的路径规范。

### Q3: 如何修改API路径？

A: 修改`main.py`中的路径前缀，或者修改路由文件中的路径定义。

### Q4: v1和v2版本如何区分？

A: 通过不同的router注册（admin_router和admin_v2_router），路径前缀不同（/api/v1和/api/v2）。

### Q5: 如何测试API路径？

A: 使用Postman、curl或Swagger UI测试所有API端点，确保路径正确。

## 十、总结

1. **API路径完全不变**：重构后所有API路径保持原样
2. **前端无需修改**：前端代码无需任何改动
3. **路径统一管理**：路径前缀在main.py中统一管理
4. **版本清晰区分**：v1和v2版本通过不同的router注册
5. **向后兼容**：不删除任何现有API端点

