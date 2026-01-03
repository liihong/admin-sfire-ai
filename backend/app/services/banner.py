"""
Banner Service
Banner管理服务层
"""
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.banner import Banner, LinkType, BannerPosition
from app.schemas.banner import (
    BannerCreate,
    BannerUpdate,
    BannerQueryParams,
    BannerResponse,
)
from app.utils.exceptions import NotFoundException, BadRequestException


class BannerService:
    """Banner管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _format_banner_response(self, banner: Banner) -> dict:
        """格式化Banner响应"""
        return {
            "id": banner.id,
            "title": banner.title,
            "image_url": banner.image_url,
            "link_url": banner.link_url,
            "link_type": banner.link_type.value,
            "position": banner.position.value,
            "sort_order": banner.sort_order,
            "start_time": banner.start_time.isoformat() if banner.start_time else None,
            "end_time": banner.end_time.isoformat() if banner.end_time else None,
            "is_enabled": banner.is_enabled,
            "created_at": banner.created_at.isoformat() if banner.created_at else None,
            "updated_at": banner.updated_at.isoformat() if banner.updated_at else None,
        }
    
    async def get_banners(
        self,
        params: BannerQueryParams
    ) -> Tuple[List[dict], int]:
        """
        获取Banner列表
        
        Args:
            params: 查询参数
        
        Returns:
            (Banner列表, 总数量)
        """
        # 构建查询条件
        conditions = []
        
        if params.title:
            conditions.append(Banner.title.like(f"%{params.title}%"))
        
        if params.position:
            position_enum = BannerPosition(params.position)
            conditions.append(Banner.position == position_enum)
        
        if params.is_enabled is not None:
            conditions.append(Banner.is_enabled == params.is_enabled)
        
        # 查询总数
        count_query = select(func.count(Banner.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(Banner)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(asc(Banner.sort_order), desc(Banner.created_at))
        query = query.offset(params.offset).limit(params.pageSize)
        
        result = await self.db.execute(query)
        banners = result.scalars().all()
        
        # 格式化响应
        banner_list = [self._format_banner_response(banner) for banner in banners]
        
        return banner_list, total
    
    async def get_banner_by_id(self, banner_id: int) -> dict:
        """
        根据ID获取Banner
        
        Args:
            banner_id: Banner ID
        
        Returns:
            Banner信息
        """
        result = await self.db.execute(
            select(Banner).where(Banner.id == banner_id)
        )
        banner = result.scalar_one_or_none()
        
        if not banner:
            raise NotFoundException(msg="Banner不存在")
        
        return self._format_banner_response(banner)
    
    async def create_banner(self, banner_data: BannerCreate) -> dict:
        """
        创建Banner
        
        Args:
            banner_data: Banner创建数据
        
        Returns:
            新Banner信息
        """
        # 验证时间范围
        if banner_data.start_time and banner_data.end_time:
            if banner_data.start_time >= banner_data.end_time:
                raise BadRequestException(msg="开始时间必须早于结束时间")
        
        # 创建Banner
        banner = Banner(
            title=banner_data.title,
            image_url=banner_data.image_url,
            link_url=banner_data.link_url,
            link_type=LinkType(banner_data.link_type),
            position=BannerPosition(banner_data.position),
            sort_order=banner_data.sort_order,
            start_time=banner_data.start_time,
            end_time=banner_data.end_time,
            is_enabled=banner_data.is_enabled,
        )
        
        self.db.add(banner)
        await self.db.flush()
        await self.db.refresh(banner)
        
        logger.info(f"Banner created: {banner.title} (ID: {banner.id})")
        
        return self._format_banner_response(banner)
    
    async def update_banner(self, banner_id: int, banner_data: BannerUpdate) -> dict:
        """
        更新Banner
        
        Args:
            banner_id: Banner ID
            banner_data: Banner更新数据
        
        Returns:
            更新后的Banner信息
        """
        result = await self.db.execute(
            select(Banner).where(Banner.id == banner_id)
        )
        banner = result.scalar_one_or_none()
        
        if not banner:
            raise NotFoundException(msg="Banner不存在")
        
        # 验证时间范围
        start_time = banner_data.start_time if banner_data.start_time is not None else banner.start_time
        end_time = banner_data.end_time if banner_data.end_time is not None else banner.end_time
        
        if start_time and end_time:
            if start_time >= end_time:
                raise BadRequestException(msg="开始时间必须早于结束时间")
        
        # 更新字段
        update_data = banner_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "link_type" and value is not None:
                setattr(banner, field, LinkType(value))
            elif field == "position" and value is not None:
                setattr(banner, field, BannerPosition(value))
            else:
                setattr(banner, field, value)
        
        await self.db.flush()
        await self.db.refresh(banner)
        
        logger.info(f"Banner updated: {banner.title} (ID: {banner.id})")
        
        return self._format_banner_response(banner)
    
    async def delete_banner(self, banner_id: int) -> None:
        """
        删除Banner
        
        Args:
            banner_id: Banner ID
        """
        result = await self.db.execute(
            select(Banner).where(Banner.id == banner_id)
        )
        banner = result.scalar_one_or_none()
        
        if not banner:
            raise NotFoundException(msg="Banner不存在")
        
        await self.db.delete(banner)
        await self.db.flush()
        
        logger.info(f"Banner deleted: {banner.title} (ID: {banner.id})")
    
    async def update_banner_status(self, banner_id: int, is_enabled: bool) -> dict:
        """
        更新Banner状态
        
        Args:
            banner_id: Banner ID
            is_enabled: 是否启用
        
        Returns:
            更新后的Banner信息
        """
        result = await self.db.execute(
            select(Banner).where(Banner.id == banner_id)
        )
        banner = result.scalar_one_or_none()
        
        if not banner:
            raise NotFoundException(msg="Banner不存在")
        
        banner.is_enabled = is_enabled
        await self.db.flush()
        await self.db.refresh(banner)
        
        logger.info(f"Banner status updated: {banner.title} (ID: {banner.id}, enabled: {is_enabled})")
        
        return self._format_banner_response(banner)
    
    async def update_banner_sort(self, sort_items: List[dict]) -> None:
        """
        批量更新Banner排序
        
        Args:
            sort_items: 排序项列表，格式: [{'id': 1, 'sort_order': 0}, ...]
        """
        for item in sort_items:
            banner_id = item.get("id")
            sort_order = item.get("sort_order")
            
            if banner_id is None or sort_order is None:
                continue
            
            result = await self.db.execute(
                select(Banner).where(Banner.id == banner_id)
            )
            banner = result.scalar_one_or_none()
            
            if banner:
                banner.sort_order = sort_order
        
        await self.db.flush()
        
        logger.info(f"Banner sort updated: {len(sort_items)} items")

