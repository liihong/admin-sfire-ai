# 技能组装功能代码审查报告

**审查时间**: 2026-01-19  
**审查范围**: 技能组装功能相关代码  
**审查人**: AI Code Reviewer

---

## 📋 执行摘要

本次审查发现了 **8个严重问题**、**5个中等问题** 和 **3个轻微问题**，主要集中在：
1. 响应格式不符合项目规范
2. 异步/同步混用导致潜在运行时错误
3. 数据库模型缺少必要字段
4. 安全性问题

---

## 🔴 严重问题 (Critical Issues)

### 1. **响应格式不符合项目规范** ⚠️

**问题描述**: 所有v2路由接口没有使用统一的响应格式 `{code, data, msg}`，而是直接返回Pydantic模型。

**影响范围**:
- `backend/routers/admin/v2/skill_library.py` - 所有接口
- `backend/routers/admin/v2/agents_v2.py` - 所有接口
- `backend/routers/client/v2/execution.py` - 所有接口

**问题代码示例**:
```python
# ❌ 错误：直接返回Pydantic模型
@router.get("/list", response_model=SkillListResponse)
async def get_skill_list(...):
    return SkillListResponse(list=..., total=...)

# ✅ 正确：使用统一响应格式
@router.get("/list")
async def get_skill_list(...):
    skills, total = await SkillService.get_list(...)
    return success(
        data=SkillListResponse(list=..., total=...),
        msg="获取成功"
    )
```

**修复建议**:
- 移除所有 `response_model` 参数
- 使用 `from utils.response import success, fail, page_response`
- 所有成功响应使用 `success(data=..., msg=...)`
- 所有失败响应使用 `fail(msg=..., code=...)`
- 分页响应使用 `page_response(items=..., total=...)`

---

### 2. **异步/同步混用 - PromptBuilder.build_prompt** 🔴

**问题描述**: `PromptBuilder.build_prompt()` 使用同步的 `db.query()`，但在异步路由中被直接调用，会导致运行时错误。

**影响范围**:
- `backend/services/prompt_builder.py:36-94`
- `backend/routers/client/v2/execution.py:94-98, 215-219`
- `backend/routers/admin/v2/agents_v2.py:170-174`

**问题代码**:
```python
# ❌ 错误：在异步路由中直接调用同步方法
@router.post("/agents/{agent_id}/execute")
async def execute_agent(..., db: AsyncSession = Depends(_get_db)):
    agent_prompt, _, _ = PromptBuilder.build_prompt(
        db,  # AsyncSession 不能用于同步 query()
        skill_ids,
        skill_variables,
    )
```

**修复建议**:
- 方案1：将 `PromptBuilder.build_prompt()` 改为异步方法
- 方案2：在调用时使用 `await db.run_sync()` 包装

**推荐方案1**（更符合项目规范）:
```python
@staticmethod
async def build_prompt(
    db: AsyncSession,
    skill_ids: List[int],
    skill_variables: Optional[Dict[int, Dict[str, str]]] = None
) -> Tuple[str, int, List[Dict]]:
    # 使用异步查询
    result = await db.execute(
        select(SkillLibrary).filter(SkillLibrary.id.in_(skill_ids))
    )
    skills = result.scalars().all()
    # ... 后续处理
```

---

### 3. **异步/同步混用 - AgentServiceV2** 🔴

**问题描述**: `AgentServiceV2` 所有方法使用同步 `Session`，但在异步路由中通过 `db.run_sync()` 调用。虽然能工作，但不符合项目"所有数据库操作必须使用异步方式"的规范。

**影响范围**:
- `backend/services/agent_service_v2.py` - 所有方法
- `backend/routers/admin/v2/agents_v2.py` - 所有接口

**问题代码**:
```python
# ❌ 不符合规范：使用同步Session
class AgentServiceV2:
    @staticmethod
    def create_with_skills(
        db: Session,  # 同步Session
        agent_data: dict,
    ) -> Agent:
        # ...
```

**修复建议**:
将所有方法改为异步：
```python
@staticmethod
async def create_with_skills(
    db: AsyncSession,  # 异步Session
    agent_data: dict,
) -> Agent:
    # 使用异步查询
    result = await db.execute(...)
    # ...
```

---

### 4. **异步/同步混用 - SkillService.get_by_ids** 🔴

**问题描述**: `SkillService.get_by_ids()` 是同步方法，但在异步路由中被调用。

**影响范围**:
- `backend/services/skill_service.py:107-114`
- `backend/services/agent_service_v2.py:161` (通过同步方法调用)

**修复建议**:
改为异步方法：
```python
@staticmethod
async def get_by_ids(db: AsyncSession, skill_ids: List[int]) -> List[SkillLibrary]:
    if not skill_ids:
        return []
    result = await db.execute(
        select(SkillLibrary).filter(SkillLibrary.id.in_(skill_ids))
    )
    return result.scalars().all()
```

---

### 5. **Agent模型缺少新字段** 🔴

**问题描述**: 文档要求添加的字段在 `Agent` 模型中不存在，代码中使用 `getattr()` 和 `hasattr()` 来动态访问，这是不安全的做法。

**缺失字段**:
- `agent_mode` (TINYINT)
- `persona_id` (BIGINT)
- `skill_ids` (JSON)
- `skill_variables` (JSON)
- `routing_description` (TEXT)
- `is_routing_enabled` (TINYINT)

**影响范围**:
- `backend/models/agent.py`
- 所有使用这些字段的代码

**问题代码**:
```python
# ❌ 不安全：动态访问不存在的字段
agent_mode = getattr(agent, 'agent_mode', 0)
if hasattr(agent, 'skill_ids'):
    agent.skill_ids = skill_ids
```

**修复建议**:
在 `Agent` 模型中添加这些字段：
```python
# 添加到 backend/models/agent.py
agent_mode: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    default=0,
    comment="0-普通模式, 1-Skill组装模式",
)

skill_ids: Mapped[Optional[List[int]]] = mapped_column(
    JSON,
    nullable=True,
    comment="存储技能ID数组 [1, 5, 20]",
)

skill_variables: Mapped[Optional[Dict]] = mapped_column(
    JSON,
    nullable=True,
    comment="技能变量配置 {skill_id: {var: value}}",
)

routing_description: Mapped[Optional[str]] = mapped_column(
    Text,
    nullable=True,
    comment="路由特征描述",
)

is_routing_enabled: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    default=0,
    comment="是否启用智能路由：0-否 1-是",
)

persona_id: Mapped[Optional[int]] = mapped_column(
    BigInteger,
    nullable=True,
    comment="关联IP基因库ID",
)
```

---

### 6. **execution.py 中直接调用同步方法** 🔴

**问题描述**: `execution.py` 中多处直接调用同步方法，没有使用 `run_sync`。

**影响范围**:
- `backend/routers/client/v2/execution.py:85-90, 94-98, 128, 215-219`

**问题代码**:
```python
# ❌ 错误：AsyncSession不能直接用于同步query()
skill_ids = PromptBuilder.intelligent_routing(
    db,  # AsyncSession
    request_data.input_text,
    skill_ids,
    routing_description
)

agent_prompt, _, skills_used = PromptBuilder.build_prompt(
    db,  # AsyncSession
    skill_ids,
    skill_variables,
)

# ❌ 错误：同步方法在异步路由中调用
AgentServiceV2.increment_usage_count(db, agent_id)
```

**修复建议**:
- 将所有同步方法改为异步
- 或使用 `await db.run_sync()` 包装

---

### 7. **PromptBuilder.intelligent_routing 使用同步查询** 🔴

**问题描述**: `intelligent_routing()` 方法使用同步 `db.query()`，但在异步路由中被调用。

**影响范围**:
- `backend/services/prompt_builder.py:213-268`
- `backend/routers/client/v2/execution.py:85-90`

**修复建议**:
改为异步方法：
```python
@staticmethod
async def intelligent_routing(
    db: AsyncSession,
    user_input: str,
    agent_skill_ids: List[int],
    routing_description: str
) -> List[int]:
    # 使用异步查询
    result = await db.execute(
        select(SkillLibrary).filter(
            SkillLibrary.id.in_(agent_skill_ids),
            SkillLibrary.status == 1
        )
    )
    skills = result.scalars().all()
    # ... 后续处理
```

---

### 8. **Jinja2 safe过滤器安全风险** ⚠️

**问题描述**: `_allowed_filters` 中包含了 `safe` 过滤器，这会禁用HTML转义，可能导致XSS攻击。

**影响范围**:
- `backend/services/prompt_builder.py:26-29`

**问题代码**:
```python
_allowed_filters = {
    'upper', 'lower', 'capitalize', 'title',
    'trim', 'striptags', 'escape', 'safe'  # ⚠️ safe过滤器不安全
}
```

**修复建议**:
移除 `safe` 过滤器，只保留安全的过滤器：
```python
_allowed_filters = {
    'upper', 'lower', 'capitalize', 'title',
    'trim', 'striptags', 'escape'  # 移除 safe
}
```

---

## 🟡 中等问题 (Medium Issues)

### 9. **异常处理不一致**

**问题描述**: 部分接口使用 `HTTPException`，部分使用统一响应格式，不一致。

**影响范围**:
- `backend/routers/admin/v2/skill_library.py`
- `backend/routers/admin/v2/agents_v2.py`

**修复建议**:
- 使用自定义异常类（如 `APIException`, `BadRequestException`）
- 全局异常处理器会自动转换为统一格式
- 无需手动包装异常响应

---

### 10. **SkillService.delete 是软删除但命名误导**

**问题描述**: `delete()` 方法实际是软删除（设置status=0），但方法名暗示是硬删除。

**影响范围**:
- `backend/services/skill_service.py:96-104`

**修复建议**:
- 重命名为 `soft_delete()` 或 `disable()`
- 或添加注释说明是软删除
- 或提供真正的 `delete()` 方法用于硬删除

---

### 11. **缺少输入验证**

**问题描述**: 部分接口缺少对输入参数的验证，如 `skill_ids` 可能为空列表或包含无效ID。

**影响范围**:
- `backend/routers/admin/v2/agents_v2.py:158-183` (preview接口)
- `backend/routers/client/v2/execution.py:23-136`

**修复建议**:
在Schema中添加验证：
```python
class PromptPreviewRequest(BaseModel):
    skill_ids: List[int] = Field(..., min_items=1, description="技能ID数组")
    # ...
```

---

### 12. **execution.py 返回格式不一致**

**问题描述**: `get_project_persona` 和 `build_execution_prompt` 直接返回字典，而不是统一响应格式。

**影响范围**:
- `backend/routers/client/v2/execution.py:139-166, 169-239`

**修复建议**:
使用统一响应格式：
```python
return success(data={
    "project_id": project.id,
    "project_name": project.name,
    "persona_settings": project.persona_settings,
})
```

---

### 13. **Token估算不准确**

**问题描述**: `_estimate_tokens()` 使用简化的计算公式，可能不准确。

**影响范围**:
- `backend/services/prompt_builder.py:131-152`

**修复建议**:
- 使用 `tiktoken` 库进行准确计算
- 或至少根据模型类型选择不同的计算方式

---

## 🟢 轻微问题 (Minor Issues)

### 14. **缺少日志记录**

**问题描述**: 部分关键操作缺少日志记录，不利于问题排查。

**修复建议**:
在关键操作处添加日志：
```python
logger.info(f"创建Agent: {agent.name}, mode={agent_mode}")
logger.warning(f"技能 {skill_id} 不存在，跳过")
```

---

### 15. **代码注释不完整**

**问题描述**: 部分复杂逻辑缺少中文注释。

**修复建议**:
补充关键逻辑的中文注释。

---

### 16. **类型提示不完整**

**问题描述**: 部分方法缺少类型提示，特别是 `db` 参数。

**修复建议**:
补充完整的类型提示。

---

## 📊 问题统计

| 严重程度 | 数量 | 文件数 |
|---------|------|--------|
| 🔴 严重 | 8 | 5 |
| 🟡 中等 | 5 | 3 |
| 🟢 轻微 | 3 | 2 |
| **总计** | **16** | **10** |

---

## 🎯 修复优先级

### P0 - 必须立即修复（阻塞部署）
1. ✅ 响应格式不符合规范（问题1）
2. ✅ Agent模型缺少字段（问题5）
3. ✅ 异步/同步混用（问题2, 3, 4, 6, 7）

### P1 - 尽快修复（影响功能）
4. ✅ Jinja2安全风险（问题8）
5. ✅ 异常处理不一致（问题9）

### P2 - 计划修复（优化体验）
6. ✅ 其他中等问题（问题10-13）
7. ✅ 轻微问题（问题14-16）

---

## 🔧 修复建议总结

### 1. 统一响应格式
- 移除所有 `response_model` 参数
- 使用 `success()`, `fail()`, `page_response()` 包装响应

### 2. 异步化改造
- 将 `PromptBuilder` 所有方法改为异步
- 将 `AgentServiceV2` 所有方法改为异步
- 将 `SkillService.get_by_ids()` 改为异步
- 移除所有 `db.run_sync()` 调用

### 3. 模型字段补充
- 在 `Agent` 模型中添加所有新字段
- 移除所有 `getattr()` 和 `hasattr()` 动态访问

### 4. 安全性加固
- 移除 Jinja2 `safe` 过滤器
- 添加输入验证

### 5. 代码规范
- 统一异常处理
- 补充日志和注释
- 完善类型提示

---

## ✅ 检查清单

在部署前，请确保：

- [ ] 所有接口使用统一响应格式
- [ ] 所有数据库操作使用异步方式
- [ ] Agent模型包含所有新字段
- [ ] 执行数据库迁移脚本
- [ ] 移除Jinja2 safe过滤器
- [ ] 添加输入验证
- [ ] 统一异常处理
- [ ] 补充日志记录
- [ ] 进行完整的功能测试
- [ ] 进行安全性测试

---

## 📝 备注

1. **数据库迁移**: 修复问题5后，需要执行文档中的ALTER TABLE语句
2. **向后兼容**: 修复响应格式时，需要确保前端能正确处理新的响应格式
3. **性能影响**: 异步化改造可能会影响性能，需要测试验证
4. **测试覆盖**: 建议为所有新功能添加单元测试和集成测试

---

**报告生成时间**: 2026-01-19  
**下次审查建议**: 修复P0问题后再次审查

