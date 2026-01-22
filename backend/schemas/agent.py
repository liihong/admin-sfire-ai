"""
智能体（AI Agent）Pydantic Schemas
兼容前端 Agent namespace 定义

版本管理：
- v1版本：直接定义的类（AgentCreate, AgentUpdate等）
- v2版本：通过v2命名空间访问（v2.AgentCreateV2, v2.AgentUpdateV2等）
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field, field_validator

from .common import PageParams


# 智能体状态类型
StatusType = Literal[0, 1]


class AgentConfig(BaseModel):
    """智能体配置参数"""
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数 0-2")
    maxTokens: int = Field(default=2000, ge=1, le=32000, description="最大token数")
    topP: Optional[float] = Field(default=1.0, ge=0, le=1, description="Top P 采样")
    frequencyPenalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="频率惩罚")
    presencePenalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="存在惩罚")


class AgentBase(BaseModel):
    """智能体基础信息"""
    name: str = Field(..., min_length=1, max_length=128, description="智能体名称")
    icon: str = Field(..., max_length=256, description="图标URL或图标标识")
    description: Optional[str] = Field(None, description="描述信息")
    systemPrompt: str = Field(..., min_length=1, description="系统提示词")
    model: str = Field(..., max_length=128, description="使用的AI模型")
    config: AgentConfig = Field(default_factory=AgentConfig, description="配置参数")
    sortOrder: int = Field(default=0, ge=0, description="排序顺序")
    status: StatusType = Field(default=0, description="状态：0-下架, 1-上架")
    # 技能组装模式字段（向后兼容，可选）
    agentMode: Optional[int] = Field(
        default=0,
        ge=0,
        le=1,
        description="运行模式：0-普通模式, 1-Skill组装模式"
    )
    skillIds: Optional[List[int]] = Field(
        default=None,
        description="技能ID数组（按顺序），仅在技能组装模式下使用"
    )
    skillVariables: Optional[dict] = Field(
        default=None,
        description="技能变量配置 {skill_id: {var: value}}，仅在技能组装模式下使用"
    )
    isSystem: Optional[int] = Field(
        default=0,
        ge=0,
        le=1,
        description="是否为系统自用智能体：0-否，1-是"
    )


class AgentCreate(AgentBase):
    """创建智能体请求"""
    pass


class AgentUpdate(BaseModel):
    """更新智能体请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    icon: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    systemPrompt: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, max_length=128)
    config: Optional[AgentConfig] = None
    sortOrder: Optional[int] = Field(None, ge=0)
    status: Optional[StatusType] = None
    # 技能组装模式字段（向后兼容，可选）
    agentMode: Optional[int] = Field(None, ge=0, le=1, description="运行模式：0-普通模式, 1-Skill组装模式")
    skillIds: Optional[List[int]] = Field(None, description="技能ID数组（按顺序）")
    skillVariables: Optional[dict] = Field(None, description="技能变量配置 {skill_id: {var: value}}")
    isSystem: Optional[int] = Field(None, ge=0, le=1, description="是否为系统自用智能体：0-否，1-是")


class AgentResponse(BaseModel):
    """
    智能体响应
    对应前端 Agent.ResAgentItem
    """
    id: str = Field(..., description="智能体ID")
    name: str = Field(..., description="智能体名称")
    icon: str = Field(..., description="图标")
    description: str = Field(default="", description="描述信息")
    systemPrompt: str = Field(..., description="系统提示词")
    model: str = Field(..., description="使用的AI模型")
    config: AgentConfig = Field(..., description="配置参数")
    sortOrder: int = Field(..., description="排序顺序")
    status: StatusType = Field(..., description="状态：0-下架, 1-上架")
    usageCount: int = Field(default=0, description="使用次数")
    createTime: str = Field(..., description="创建时间")
    updateTime: str = Field(..., description="更新时间")
    # 技能组装模式字段（向后兼容）
    agentMode: int = Field(default=0, description="运行模式：0-普通模式, 1-Skill组装模式")
    skillIds: Optional[List[int]] = Field(default=None, description="技能ID数组（按顺序）")
    skillVariables: Optional[dict] = Field(default=None, description="技能变量配置")
    isSystem: int = Field(default=0, description="是否为系统自用智能体：0-否，1-是")

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    list: List[AgentResponse] = Field(..., description="智能体列表")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")


class AgentQueryParams(PageParams):
    """智能体查询参数
    
    说明：
        - name: 按名称模糊查询
        - status: 按状态筛选
        - agentMode: 按智能体模式筛选（0-普通模式, 1-Skill 组装模式）
    """
    name: Optional[str] = Field(None, description="智能体名称（模糊查询）")
    status: Optional[StatusType] = Field(None, description="状态")
    agentMode: Optional[int] = Field(
        default=None,
        ge=0,
        description="智能体模式：0-普通模式, 1-Skill 组装模式",
    )


class PromptTemplate(BaseModel):
    """预设模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    content: str = Field(..., description="模板内容")
    category: str = Field(..., description="分类")


class AgentStatusUpdate(BaseModel):
    """更新智能体状态请求"""
    status: StatusType = Field(..., description="状态：0-下架, 1-上架")


class AgentSortUpdate(BaseModel):
    """更新智能体排序请求"""
    sortOrder: int = Field(..., ge=0, description="排序顺序")


class BatchSortItem(BaseModel):
    """批量排序项"""
    id: str = Field(..., description="智能体ID")
    sortOrder: int = Field(..., ge=0, description="排序顺序")


class BatchSortRequest(BaseModel):
    """批量排序请求"""
    items: List[BatchSortItem] = Field(..., description="排序项列表")


# ============== v2版本Schema（技能组装模式） ==============

# v2版本类型定义（需要在v2类外部定义，以便在嵌套类中使用）
AgentMode = Literal[0, 1]  # 0-普通模式, 1-Skill组装模式
V2StatusType = Literal[0, 1]  # 0-下架, 1-上架

class v2:
    """
    v2版本Schema命名空间
    支持技能组装模式的Agent相关Schema
    """
    
    # Agent模式类型（引用外部定义的类型）
    AgentMode = AgentMode  # 0-普通模式, 1-Skill组装模式
    StatusType = V2StatusType  # 0-下架, 1-上架
    
    class AgentConfigV2(BaseModel):
        """Agent配置参数（v2版本）"""
        temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数 0-2")
        maxTokens: int = Field(default=2000, ge=1, le=32000, description="最大token数")
        topP: Optional[float] = Field(default=1.0, ge=0, le=1, description="Top P 采样")
        frequencyPenalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="频率惩罚")
        presencePenalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="存在惩罚")
    
    class AgentCreateV2(BaseModel):
        """创建Agent请求（v2版本）"""
        name: str = Field(..., min_length=1, max_length=128, description="智能体名称")
        icon: str = Field(..., max_length=256, description="图标URL或图标标识")
        description: Optional[str] = Field(None, description="描述信息")
        agent_mode: AgentMode = Field(default=0, description="0-普通模式, 1-Skill组装模式")
        system_prompt: Optional[str] = Field(None, description="系统提示词(普通模式使用)")
        model: str = Field(..., max_length=128, description="使用的AI模型")
        config: Optional["AgentConfigV2"] = Field(default_factory=lambda: v2.AgentConfigV2(), description="配置参数")
        sort_order: int = Field(default=0, ge=0, description="排序顺序")
        status: V2StatusType = Field(default=0, description="状态：0-下架, 1-上架")
        skill_ids: Optional[List[int]] = Field(None, description="技能ID数组(按顺序)")
        skill_variables: Optional[Dict[int, Dict[str, str]]] = Field(
            None,
            description="技能变量配置 {skill_id: {var: value}}"
        )
        routing_description: Optional[str] = Field(None, description="路由特征描述")
        is_routing_enabled: int = Field(default=0, description="是否启用智能路由：0-否 1-是")
        is_system: int = Field(default=0, ge=0, le=1, description="是否为系统自用智能体：0-否，1-是")
        
        @field_validator('skill_ids')
        @classmethod
        def validate_skill_ids(cls, v, info):
            """验证技能模式下的skill_ids"""
            if info.data.get('agent_mode') == 1:
                if not v or len(v) == 0:
                    raise ValueError('技能模式下必须提供skill_ids')
            return v
    
    class AgentUpdateV2(BaseModel):
        """更新Agent请求（v2版本）"""
        name: Optional[str] = Field(None, min_length=1, max_length=128)
        icon: Optional[str] = Field(None, max_length=256)
        description: Optional[str] = None
        agent_mode: Optional[AgentMode] = None
        system_prompt: Optional[str] = None
        model: Optional[str] = Field(None, max_length=128)
        config: Optional["AgentConfigV2"] = None
        sort_order: Optional[int] = Field(None, ge=0)
        status: Optional[V2StatusType] = None
        skill_ids: Optional[List[int]] = None
        skill_variables: Optional[Dict[int, Dict[str, str]]] = None
        routing_description: Optional[str] = None
        is_routing_enabled: Optional[int] = None
        is_system: Optional[int] = Field(None, ge=0, le=1, description="是否为系统自用智能体：0-否，1-是")
    
    class AgentResponseV2(BaseModel):
        """Agent响应（v2版本）"""
        id: int = Field(..., description="智能体ID")
        name: str = Field(..., description="智能体名称")
        icon: str = Field(..., description="图标")
        description: str = Field(default="", description="描述信息")
        agent_mode: AgentMode = Field(..., description="运行模式：0-普通, 1-Skill组装")
        system_prompt: str = Field(..., description="系统提示词")
        model: str = Field(..., description="使用的AI模型")
        config: Optional["AgentConfigV2"] = Field(None, description="配置参数")
        sort_order: int = Field(..., description="排序顺序")
        status: V2StatusType = Field(..., description="状态：0-下架, 1-上架")
        usage_count: int = Field(default=0, description="使用次数")
        skill_ids: Optional[List[int]] = Field(None, description="技能ID数组")
        skill_variables: Optional[Dict[int, Dict[str, str]]] = Field(None, description="技能变量")
        routing_description: Optional[str] = Field(None, description="路由特征描述")
        is_routing_enabled: int = Field(default=0, description="是否启用智能路由")
        is_system: int = Field(default=0, description="是否为系统自用智能体：0-否，1-是")
        skills_detail: Optional[List["SkillResponse"]] = Field(None, description="关联的技能详情")
        created_at: datetime = Field(..., description="创建时间")
        updated_at: Optional[datetime] = Field(None, description="更新时间")
        
        class Config:
            from_attributes = True
    
    class AgentListResponseV2(BaseModel):
        """Agent列表响应（v2版本）"""
        list: List["AgentResponseV2"] = Field(..., description="Agent列表")
        total: int = Field(..., description="总数量")
    
    class AgentQueryParamsV2(BaseModel):
        """Agent查询参数（v2版本）"""
        page: int = Field(default=1, ge=1, description="页码")
        size: int = Field(default=20, ge=1, le=100, description="每页数量")
        name: Optional[str] = Field(None, description="智能体名称(模糊查询)")
        agent_mode: Optional[AgentMode] = Field(None, description="运行模式筛选")
        status: Optional[V2StatusType] = Field(None, description="状态筛选")
    
    class PromptPreviewRequest(BaseModel):
        """Prompt预览请求"""
        skill_ids: List[int] = Field(..., min_items=1, description="技能ID数组（至少1个）")
        skill_variables: Optional[Dict[int, Dict[str, str]]] = Field(
            None,
            description="技能变量配置"
        )
    
    class PromptPreviewResponse(BaseModel):
        """Prompt预览响应"""
        full_prompt: str = Field(..., description="完整的Prompt")
        token_count: int = Field(..., description="Token数量")
        skills_used: List[dict] = Field(..., description="使用的技能列表")
    
    class AgentExecuteRequest(BaseModel):
        """Agent执行请求（前端用户使用）"""
        user_id: int = Field(..., gt=0, description="用户ID")
        project_id: int = Field(..., gt=0, description="项目ID")
        input_text: str = Field(..., min_length=1, description="用户输入（不能为空）")
        enable_persona: bool = Field(default=True, description="是否启用IP基因")
    
    class AgentExecuteResponse(BaseModel):
        """Agent执行响应"""
        response: str = Field(..., description="AI回复")
        prompt_used: str = Field(..., description="实际使用的Prompt")
        skills_applied: List[int] = Field(..., description="实际应用的技能ID列表")
    
    class RoutingPreviewRequest(BaseModel):
        """智能路由预览请求"""
        user_input: str = Field(..., min_length=1, description="模拟的用户输入")
        use_vector: bool = Field(default=True, description="是否使用向量检索")
        top_k: int = Field(default=3, ge=1, le=10, description="选择Top-K个技能")
        threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    
    class SkillRoutingInfo(BaseModel):
        """技能路由信息"""
        id: int = Field(..., description="技能ID")
        name: str = Field(..., description="技能名称")
        category: str = Field(..., description="技能分类")
        similarity: float = Field(..., description="相似度得分")
        meta_description: Optional[str] = Field(None, description="特征描述")
    
    class RoutingPreviewResponse(BaseModel):
        """智能路由预览响应"""
        selected_skills: List["SkillRoutingInfo"] = Field(..., description="选中的技能列表")
        rejected_skills: List["SkillRoutingInfo"] = Field(..., description="未选中的技能列表")
        token_comparison: Dict = Field(..., description="Token对比 {full: 全量, routed: 路由后, saved_percent: 节省比例}")
        final_prompt: str = Field(..., description="最终组装的Prompt")
        routing_method: str = Field(..., description="使用的路由方法: vector/keywords")
    
    # ============== 技能相关Schema（v2版本） ==============
    
    class SkillBase(BaseModel):
        """技能基础信息"""
        name: str = Field(..., min_length=1, max_length=100, description="技能名称")
        category: str = Field(..., description="分类：model/hook/rule/audit")
        meta_description: Optional[str] = Field(None, description="特征简述(路由用)")
        content: str = Field(..., min_length=1, description="实际Prompt片段")
        status: int = Field(default=1, description="状态：1-启用 0-禁用")
    
    class SkillCreate(SkillBase):
        """创建技能请求"""
        pass
    
    class SkillUpdate(BaseModel):
        """更新技能请求"""
        name: Optional[str] = Field(None, min_length=1, max_length=100)
        category: Optional[str] = None
        meta_description: Optional[str] = None
        content: Optional[str] = Field(None, min_length=1)
        status: Optional[int] = None
    
    class SkillResponse(SkillBase):
        """技能响应"""
        id: int = Field(..., description="技能ID")
        created_at: datetime = Field(..., description="创建时间")
        
        class Config:
            from_attributes = True
    
    class SkillListResponse(BaseModel):
        """技能列表响应"""
        list: List["SkillResponse"] = Field(..., description="技能列表")
        total: int = Field(..., description="总数量")
    
    class SkillCategoryResponse(BaseModel):
        """技能分类响应"""
        category: str = Field(..., description="分类名称")
        count: int = Field(..., description="该分类下的技能数量")
    
    class SkillQueryParams(BaseModel):
        """技能查询参数"""
        page: int = Field(default=1, ge=1, description="页码")
        size: int = Field(default=20, ge=1, le=100, description="每页数量")
        category: Optional[str] = Field(None, description="分类筛选")
        status: Optional[int] = Field(None, description="状态筛选")


