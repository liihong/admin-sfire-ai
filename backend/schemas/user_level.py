"""
用户等级配置Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class UserLevelBase(BaseModel):
    """用户等级基础Schema"""
    code: str = Field(..., description="等级代码：normal/vip/svip/max")
    name: str = Field(..., description="等级名称（中文显示）")
    max_ip_count: Optional[int] = Field(None, description="最大IP数量（NULL表示不限制）")
    ip_type: str = Field(default="permanent", description="IP类型：temporary/permanent")
    daily_tokens_limit: Optional[int] = Field(None, description="每日AI能量限制（NULL表示无限制）")
    can_use_advanced_agent: bool = Field(default=False, description="是否可使用高级智能体")
    unlimited_conversations: bool = Field(default=False, description="是否无限制对话")
    is_enabled: bool = Field(default=True, description="是否启用该等级")
    sort_order: int = Field(default=0, description="排序顺序（数字越小越靠前）")


class UserLevelCreate(UserLevelBase):
    """创建用户等级Schema"""
    pass


class UserLevelUpdate(BaseModel):
    """更新用户等级Schema"""
    name: Optional[str] = Field(None, description="等级名称")
    max_ip_count: Optional[int] = Field(None, description="最大IP数量")
    ip_type: Optional[str] = Field(None, description="IP类型")
    daily_tokens_limit: Optional[int] = Field(None, description="每日AI能量限制")
    can_use_advanced_agent: Optional[bool] = Field(None, description="是否可使用高级智能体")
    unlimited_conversations: Optional[bool] = Field(None, description="是否无限制对话")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class UserLevelResponse(UserLevelBase):
    """用户等级响应Schema"""
    id: int = Field(..., description="等级ID")
    
    class Config:
        from_attributes = True






