"""
快捷入口配置 Pydantic Schemas
快捷入口管理相关数据结构定义
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

from .common import PageParams


# 入口类型
EntryType = Literal["category", "command"]

# 动作类型
ActionType = Literal["agent", "skill", "prompt"]

# 入口标签
EntryTag = Literal["none", "new", "hot"]


class QuickEntryBase(BaseModel):
    """快捷入口基础信息"""
    unique_key: str = Field(..., min_length=1, max_length=64, description="唯一标识")
    type: EntryType = Field(..., description="入口类型: category-今天拍点啥, command-快捷指令库")
    title: str = Field(..., min_length=1, max_length=128, description="标题")
    subtitle: Optional[str] = Field(None, max_length=256, description="副标题")
    icon_class: str = Field(..., min_length=1, max_length=64, description="图标类名（RemixIcon）")
    bg_color: Optional[str] = Field(None, max_length=16, description="背景色（十六进制）")
    action_type: ActionType = Field(..., description="动作类型: agent-调用Agent, skill-调用Skill, prompt-硬编码Prompt")
    action_value: str = Field(..., min_length=1, description="动作值（agent_id/skill_id/prompt文本）")
    tag: EntryTag = Field(default="none", description="标签: none-无标签, new-新上线, hot-最热门")
    priority: int = Field(default=0, ge=0, description="排序权重（数字越小越靠前）")
    status: int = Field(default=1, ge=0, le=2, description="状态：0-禁用, 1-启用, 2-即将上线")


class QuickEntryCreate(QuickEntryBase):
    """创建快捷入口请求"""
    pass


class QuickEntryUpdate(BaseModel):
    """更新快捷入口请求"""
    unique_key: Optional[str] = Field(None, min_length=1, max_length=64)
    type: Optional[EntryType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    subtitle: Optional[str] = Field(None, max_length=256)
    icon_class: Optional[str] = Field(None, min_length=1, max_length=64)
    bg_color: Optional[str] = Field(None, max_length=16)
    action_type: Optional[ActionType] = None
    action_value: Optional[str] = Field(None, min_length=1)
    tag: Optional[EntryTag] = None
    priority: Optional[int] = Field(None, ge=0)
    status: Optional[int] = Field(None, ge=0, le=2)


class QuickEntryResponse(BaseModel):
    """快捷入口响应数据"""
    id: int = Field(..., description="入口ID")
    unique_key: str = Field(..., description="唯一标识")
    type: str = Field(..., description="入口类型")
    title: str = Field(..., description="标题")
    subtitle: Optional[str] = Field(None, description="副标题")
    icon_class: str = Field(..., description="图标类名")
    bg_color: Optional[str] = Field(None, description="背景色")
    action_type: str = Field(..., description="动作类型")
    action_value: str = Field(..., description="动作值")
    tag: str = Field(..., description="标签")
    priority: int = Field(..., description="排序权重")
    status: int = Field(..., description="状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class QuickEntryQueryParams(PageParams):
    """快捷入口查询参数"""
    type: Optional[EntryType] = Field(None, description="入口类型筛选")
    status: Optional[int] = Field(None, ge=0, le=2, description="状态筛选")
    tag: Optional[EntryTag] = Field(None, description="标签筛选")
    title: Optional[str] = Field(None, description="标题（模糊搜索）")


class QuickEntrySortRequest(BaseModel):
    """快捷入口排序请求"""
    items: List[dict] = Field(..., description="排序项列表，格式: [{'id': 1, 'priority': 0}, ...]")


class QuickEntryStatusRequest(BaseModel):
    """快捷入口状态更新请求"""
    status: int = Field(..., ge=0, le=2, description="状态：0-禁用, 1-启用, 2-即将上线")

