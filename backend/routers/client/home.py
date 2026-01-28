"""
首页内容 Endpoints
首页内容聚合接口（小程序端）
独立于文章管理接口，专门为首页提供聚合数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services.resource.home import HomeService
from utils.response import success

router = APIRouter()


@router.get("", summary="获取首页内容")
async def get_home_content(
    db: AsyncSession = Depends(get_db),
):
    """
    获取首页内容（聚合接口）
    
    返回首页所需的所有数据：
    - banners: Banner列表（按位置分组：home_top, home_middle, home_bottom）
    - founder_stories: 创始人故事列表（用于轮播）
    - operation_articles: 运营干货列表（用于横向滚动）
    - announcements: 公告列表（最新公告）
    - customer_cases: 客户案例列表（可选）
    
    该接口独立于文章管理接口，专门为首页优化，提升性能和可维护性
    
    路径：GET /api/v1/client/home
    """
    home_service = HomeService(db)
    content = await home_service.get_home_content()
    
    return success(data=content, msg="获取成功")

