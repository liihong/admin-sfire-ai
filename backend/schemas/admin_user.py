"""
AdminUser Pydantic Schemas
管理员用户Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

from .common import PageParams


class AdminUserBase(BaseModel):
    """管理员用户基础信息"""
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    role_id: Optional[int] = Field(None, description="角色ID")
    remark: Optional[str] = Field(None, description="备注")


class AdminUserCreate(AdminUserBase):
    """创建管理员用户请求"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    tenant_id: Optional[int] = Field(
        None,
        description="租户ID；平台管理员必选或默认主租户；租户管理员忽略并由服务端写入当前租户",
    )


class AdminUserUpdate(BaseModel):
    """更新管理员用户请求"""
    username: Optional[str] = Field(None, min_length=2, max_length=64, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="密码（留空则不修改）")
    role_id: Optional[int] = Field(None, description="角色ID")
    is_active: Optional[bool] = Field(None, description="是否激活")
    remark: Optional[str] = Field(None, description="备注")
    tenant_id: Optional[int] = Field(None, description="租户ID；仅平台管理员可修改")


class AdminUserResponse(BaseModel):
    """管理员用户响应"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    role_id: Optional[int] = Field(None, description="角色ID")
    role_name: Optional[str] = Field(None, description="角色名称")
    role_code: Optional[str] = Field(None, description="角色代码")
    tenant_id: Optional[int] = Field(None, description="租户ID；空为平台管理员")
    tenant_name: Optional[str] = Field(None, description="租户名称")
    is_active: bool = Field(..., description="是否激活")
    remark: Optional[str] = Field(None, description="备注")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """管理员用户列表响应"""
    list: List[AdminUserResponse] = Field(..., description="用户列表")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")


class AdminUserQueryParams(PageParams):
    """管理员用户查询参数"""
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    role_id: Optional[int] = Field(None, description="角色ID")
    is_active: Optional[bool] = Field(None, description="是否激活")




