
#Agent相关的 Pydantic Schemas
# v2版本：支持技能组装模式
from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator

from .skill import SkillResponse


# Agent模式类型
AgentMode = Literal[0, 1]  # 0-普通模式, 1-Skill组装模式
StatusType = Literal[0, 1]  # 0-下架, 1-上架


class AgentConfigV2(BaseModel):
    """Agent配置参数"""
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数 0-2")
    maxTokens: int = Field(default=2000, ge=1, le=32000, description="最大token数")
    topP: Optional[float] = Field(default=1.0, ge=0, le=1, description="Top P 采样")
    frequencyPenalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="频率惩罚")
    presencePenalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="存在惩罚")


class AgentCreateV2(BaseModel):
    """创建Agent请求(v2版本)"""
    name: str = Field(..., min_length=1, max_length=128, description="智能体名称")
    icon: str = Field(..., max_length=256, description="图标URL或图标标识")
    description: Optional[str] = Field(None, description="描述信息")
    agent_mode: AgentMode = Field(default=0, description="0-普通模式, 1-Skill组装模式")
    system_prompt: Optional[str] = Field(None, description="系统提示词(普通模式使用)")
    model: str = Field(..., max_length=128, description="使用的AI模型")
    config: Optional[AgentConfigV2] = Field(default_factory=AgentConfigV2, description="配置参数")
    sort_order: int = Field(default=0, ge=0, description="排序顺序")
    status: StatusType = Field(default=0, description="状态：0-下架, 1-上架")

    # 技能模式专属字段
    skill_ids: Optional[List[int]] = Field(None, description="技能ID数组(按顺序)")
    skill_variables: Optional[Dict[int, Dict[str, str]]] = Field(
        None,
        description="技能变量配置 {skill_id: {var: value}}"
    )
    
    @field_validator('skill_ids')
    @classmethod
    def validate_skill_ids(cls, v, info):
        """验证技能模式下的skill_ids"""
        if info.data.get('agent_mode') == 1:
            if not v or len(v) == 0:
                raise ValueError('技能模式下必须提供skill_ids')
        return v
    routing_description: Optional[str] = Field(None, description="路由特征描述")
    is_routing_enabled: int = Field(default=0, description="是否启用智能路由：0-否 1-是")


class AgentUpdateV2(BaseModel):
    """更新Agent请求(v2版本)"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    icon: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    agent_mode: Optional[AgentMode] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = Field(None, max_length=128)
    config: Optional[AgentConfigV2] = None
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[StatusType] = None

    # 技能模式专属字段
    skill_ids: Optional[List[int]] = None
    skill_variables: Optional[Dict[int, Dict[str, str]]] = None
    routing_description: Optional[str] = None
    is_routing_enabled: Optional[int] = None


class AgentResponseV2(BaseModel):
    """Agent响应(v2版本)"""
    id: int = Field(..., description="智能体ID")
    name: str = Field(..., description="智能体名称")
    icon: str = Field(..., description="图标")
    description: str = Field(default="", description="描述信息")
    agent_mode: AgentMode = Field(..., description="运行模式：0-普通, 1-Skill组装")
    system_prompt: str = Field(..., description="系统提示词")
    model: str = Field(..., description="使用的AI模型")
    config: Optional[AgentConfigV2] = Field(None, description="配置参数")
    sort_order: int = Field(..., description="排序顺序")
    status: StatusType = Field(..., description="状态：0-下架, 1-上架")
    usage_count: int = Field(default=0, description="使用次数")

    # 技能模式专属字段
    skill_ids: Optional[List[int]] = Field(None, description="技能ID数组")
    skill_variables: Optional[Dict[int, Dict[str, str]]] = Field(None, description="技能变量")
    routing_description: Optional[str] = Field(None, description="路由特征描述")
    is_routing_enabled: int = Field(default=0, description="是否启用智能路由")

    # 关联的技能详情(仅在详情接口返回)
    skills_detail: Optional[List[SkillResponse]] = Field(None, description="关联的技能详情")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class AgentListResponseV2(BaseModel):
    """Agent列表响应(v2版本)"""
    list: List[AgentResponseV2] = Field(..., description="Agent列表")
    total: int = Field(..., description="总数量")


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
    """Agent执行请求(前端用户使用)"""
    user_id: int = Field(..., gt=0, description="用户ID")
    project_id: int = Field(..., gt=0, description="项目ID")
    input_text: str = Field(..., min_length=1, description="用户输入（不能为空）")
    enable_persona: bool = Field(default=True, description="是否启用IP基因")


class AgentExecuteResponse(BaseModel):
    """Agent执行响应"""
    response: str = Field(..., description="AI回复")
    prompt_used: str = Field(..., description="实际使用的Prompt")
    skills_applied: List[int] = Field(..., description="实际应用的技能ID列表")


class AgentQueryParamsV2(BaseModel):
    """Agent查询参数(v2版本)"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    name: Optional[str] = Field(None, description="智能体名称(模糊查询)")
    agent_mode: Optional[AgentMode] = Field(None, description="运行模式筛选")
    status: Optional[StatusType] = Field(None, description="状态筛选")


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
    selected_skills: List[SkillRoutingInfo] = Field(..., description="选中的技能列表")
    rejected_skills: List[SkillRoutingInfo] = Field(..., description="未选中的技能列表")
    token_comparison: Dict = Field(..., description="Token对比 {full: 全量, routed: 路由后, saved_percent: 节省比例}")
    final_prompt: str = Field(..., description="最终组装的Prompt")
    routing_method: str = Field(..., description="使用的路由方法: vector/keywords")
