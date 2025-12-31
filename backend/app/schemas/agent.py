"""
智能体（AI Agent）Pydantic Schemas
兼容前端 Agent namespace 定义
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

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

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """智能体列表响应"""
    list: List[AgentResponse] = Field(..., description="智能体列表")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")


class AgentQueryParams(PageParams):
    """智能体查询参数"""
    name: Optional[str] = Field(None, description="智能体名称（模糊查询）")
    status: Optional[StatusType] = Field(None, description="状态")


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

