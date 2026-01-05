"""
Role Pydantic Schemas
角色管理Schema（基于roles表和users表的level字段）
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """角色基础信息"""
    name: str = Field(..., min_length=1, max_length=64, description="角色名称")
    code: str = Field(..., min_length=1, max_length=32, description="角色代码（normal/member/partner）")
    description: Optional[str] = Field(None, max_length=255, description="角色描述")
    sort_order: int = Field(default=0, description="排序顺序")


class RoleCreate(RoleBase):
    """创建角色请求"""
    pass


class RoleUpdate(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = None


class RoleResponse(BaseModel):
    """角色响应"""
    id: int = Field(..., description="角色ID（数据库主键）")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码（normal/member/partner，对应users表的level字段）")
    description: Optional[str] = Field(None, description="角色描述")
    sort_order: int = Field(..., description="排序顺序")
    user_count: int = Field(default=0, description="该角色的用户数量（从users表统计）")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """角色列表响应"""
    list: List[RoleResponse] = Field(..., description="角色列表")
    total: int = Field(..., description="总数量")

