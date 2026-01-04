"""
Banner Pydantic Schemas
Banner管理相关数据结构定义
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

from .common import PageParams


# 链接类型
LinkType = Literal["none", "internal", "external"]

# Banner位置类型
BannerPosition = Literal["home_top", "home_middle", "home_bottom"]


class BannerBase(BaseModel):
    """Banner基础信息"""
    title: str = Field(..., min_length=1, max_length=128, description="Banner标题")
    image_url: str = Field(..., min_length=1, max_length=512, description="图片URL")
    link_url: Optional[str] = Field(None, max_length=512, description="跳转链接")
    link_type: LinkType = Field(default="none", description="链接类型")
    position: BannerPosition = Field(default="home_top", description="Banner位置")
    sort_order: int = Field(default=0, ge=0, description="排序顺序")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    is_enabled: bool = Field(default=True, description="是否启用")


class BannerCreate(BannerBase):
    """创建Banner请求"""
    pass


class BannerUpdate(BaseModel):
    """更新Banner请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    image_url: Optional[str] = Field(None, min_length=1, max_length=512)
    link_url: Optional[str] = Field(None, max_length=512)
    link_type: Optional[LinkType] = None
    position: Optional[BannerPosition] = None
    sort_order: Optional[int] = Field(None, ge=0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_enabled: Optional[bool] = None


class BannerResponse(BaseModel):
    """Banner响应数据"""
    id: int = Field(..., description="Banner ID")
    title: str = Field(..., description="Banner标题")
    image_url: str = Field(..., description="图片URL")
    link_url: Optional[str] = Field(None, description="跳转链接")
    link_type: str = Field(..., description="链接类型")
    position: str = Field(..., description="Banner位置")
    sort_order: int = Field(..., description="排序顺序")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    is_enabled: bool = Field(..., description="是否启用")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class BannerListResponse(BaseModel):
    """Banner列表响应"""
    list: List[BannerResponse] = Field(..., description="Banner列表")
    total: int = Field(..., description="总数量")


class BannerQueryParams(PageParams):
    """Banner查询参数"""
    title: Optional[str] = Field(None, description="标题（模糊搜索）")
    position: Optional[BannerPosition] = Field(None, description="位置筛选")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class BannerSortRequest(BaseModel):
    """Banner排序请求"""
    items: List[dict] = Field(..., description="排序项列表，格式: [{'id': 1, 'sort_order': 0}, ...]")


class BannerStatusRequest(BaseModel):
    """Banner状态更新请求"""
    is_enabled: bool = Field(..., description="是否启用")

