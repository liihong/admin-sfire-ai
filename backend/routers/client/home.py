"""
首页内容 Endpoints
首页内容聚合接口（小程序端/Web端）
独立于文章管理接口，专门为首页提供聚合数据
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.client_public_scope import resolve_optional_public_tenant_id
from services.resource.home import HomeService
from utils.response import success

router = APIRouter()


@router.get("", summary="获取首页内容")
async def get_home_content(
    position: Optional[str] = Query(
        None,
        description="Banner位置筛选：home_top/home_middle/home_bottom/web，不传则返回所有位置"
    ),
    scoped_tenant_id: Optional[int] = Depends(resolve_optional_public_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取首页内容（聚合接口）
    
    返回首页所需的所有数据：
    - banners: Banner列表（按位置分组：home_top, home_middle, home_bottom, web）
    - founder_stories: 创始人故事列表（用于轮播）
    - operation_articles: 运营干货列表（category 02，横向滚动）
    - recent_landing_articles: 最近落地列表（category 05）
    - announcements: 公告列表（最新公告）
    - customer_cases: 客户案例列表（可选）
    
    支持 position 参数按位置过滤 Banner，如 Web 端可传 position=web
    
    路径：GET /api/v1/client/home
    """
    home_service = HomeService(db)
    content = await home_service.get_home_content(
        position=position,
        scoped_tenant_id=scoped_tenant_id,
    )
    
    return success(data=content, msg="获取成功")

