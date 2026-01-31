"""
用户权限Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class UserPermissionResponse(BaseModel):
    """用户权限快照响应Schema"""
    max_ip: Optional[int] = Field(None, description="最大IP数量（None表示不限制）")
    ip_type: str = Field(..., description="IP类型：temporary/permanent")
    daily_tokens: Optional[int] = Field(None, description="每日AI能量次数（None表示无限制）")
    can_use_advanced_agent: bool = Field(..., description="是否可使用高级智能体")
    unlimited_conversations: bool = Field(..., description="是否无限制对话")
    level: str = Field(..., description="用户等级代码")
    level_name: str = Field(..., description="等级名称")
    vip_expire_date: Optional[str] = Field(None, description="VIP到期时间（ISO格式）")
    is_vip_expired: bool = Field(..., description="VIP是否过期")
    
    class Config:
        from_attributes = True










