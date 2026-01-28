"""
文章 Pydantic Schemas
文章管理相关数据结构定义
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

from .common import PageParams


# 文章类型
ArticleCategory = Literal["founder_story", "operation_article", "customer_case", "announcement"]


class ArticleBase(BaseModel):
    """文章基础信息"""
    category: ArticleCategory = Field(..., description="文章类型")
    title: str = Field(..., min_length=1, max_length=256, description="文章标题")
    content: str = Field(..., min_length=1, description="文章内容（富文本）")
    summary: Optional[str] = Field(None, max_length=500, description="文章摘要/简介")
    cover_image: Optional[str] = Field(None, max_length=512, description="封面图URL")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    sort_order: int = Field(default=0, ge=0, description="排序顺序")
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    is_published: bool = Field(default=False, description="是否已发布")
    is_enabled: bool = Field(default=True, description="是否启用")


class ArticleCreate(ArticleBase):
    """创建文章请求"""
    pass


class ArticleUpdate(BaseModel):
    """更新文章请求"""
    category: Optional[ArticleCategory] = None
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = Field(None, max_length=512)
    tags: Optional[List[str]] = None
    sort_order: Optional[int] = Field(None, ge=0)
    publish_time: Optional[datetime] = None
    is_published: Optional[bool] = None
    is_enabled: Optional[bool] = None


class ArticleResponse(BaseModel):
    """文章响应数据"""
    id: int = Field(..., description="文章ID")
    category: str = Field(..., description="文章类型")
    title: str = Field(..., description="文章标题")
    content: str = Field(..., description="文章内容")
    summary: Optional[str] = Field(None, description="文章摘要")
    cover_image: Optional[str] = Field(None, description="封面图URL")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    sort_order: int = Field(..., description="排序顺序")
    publish_time: Optional[str] = Field(None, description="发布时间")
    view_count: int = Field(..., description="浏览量")
    is_published: bool = Field(..., description="是否已发布")
    is_enabled: bool = Field(..., description="是否启用")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class ArticleQueryParams(PageParams):
    """文章查询参数"""
    category: Optional[ArticleCategory] = Field(None, description="文章类型筛选")
    title: Optional[str] = Field(None, description="标题（模糊搜索）")
    tag: Optional[str] = Field(None, description="标签筛选")
    is_published: Optional[bool] = Field(None, description="是否已发布")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class ArticleStatusRequest(BaseModel):
    """文章状态更新请求"""
    is_published: Optional[bool] = Field(None, description="是否已发布")
    is_enabled: Optional[bool] = Field(None, description="是否启用")

