"""
技能库相关的 Pydantic Schemas
v2版本：支持技能组装模式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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
    list: List[SkillResponse] = Field(..., description="技能列表")
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
