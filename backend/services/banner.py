"""
Banner Service
Banner管理服务层
"""
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.banner import Banner, LinkType, BannerPosition
from schemas.banner import (
    BannerCreate,
    BannerUpdate,
    BannerQueryParams,
    BannerResponse,
)
from utils.exceptions import NotFoundException, BadRequestException
from services.base import BaseService


class BannerService(BaseService):
    """Banner管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Banner, "Banner", check_soft_delete=False)
    
    def _format_response(self, banner: Banner) -> dict:
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
        banner_list = [self._format_response(banner) for banner in banners]
        
        return banner_list, total
    
    async def get_banner_by_id(self, banner_id: int) -> dict:
        """
        根据ID获取Banner
        
        Args:
            banner_id: Banner ID
        
        Returns:
            Banner信息
        """
        banner = await super().get_by_id(banner_id, error_msg="Banner不存在")
        return self._format_response(banner)
    
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
        
        def before_create(banner: Banner, data: BannerCreate):
            """创建前的钩子函数"""
            # 转换枚举类型
            if hasattr(data, "link_type") and data.link_type:
                banner.link_type = LinkType(data.link_type)
            if hasattr(data, "position") and data.position:
                banner.position = BannerPosition(data.position)
        
        banner = await super().create(
            data=banner_data,
            before_create=before_create,
        )
        
        await self.db.flush()
        await self.db.refresh(banner)
        
        return self._format_response(banner)
    
    async def update_banner(self, banner_id: int, banner_data: BannerUpdate) -> dict:
        """
        更新Banner
        
        Args:
            banner_id: Banner ID
            banner_data: Banner更新数据
        
        Returns:
            更新后的Banner信息
        """
        # 验证时间范围
        banner = await super().get_by_id(banner_id)
        start_time = banner_data.start_time if banner_data.start_time is not None else banner.start_time
        end_time = banner_data.end_time if banner_data.end_time is not None else banner.end_time
        
        if start_time and end_time:
            if start_time >= end_time:
                raise BadRequestException(msg="开始时间必须早于结束时间")
        
        def before_update(banner: Banner, data: BannerUpdate):
            """更新前的钩子函数"""
            # 处理枚举类型转换
            update_data = data.model_dump(exclude_unset=True)
            if "link_type" in update_data and update_data["link_type"] is not None:
                banner.link_type = LinkType(update_data["link_type"])
            if "position" in update_data and update_data["position"] is not None:
                banner.position = BannerPosition(update_data["position"])
        
        banner = await super().update(
            obj_id=banner_id,
            data=banner_data,
            before_update=before_update,
        )
        
        await self.db.flush()
        await self.db.refresh(banner)
        
        return self._format_response(banner)
    
    async def delete_banner(self, banner_id: int) -> None:
        """
        删除Banner
        
        Args:
            banner_id: Banner ID
        """
        await super().delete(banner_id, hard_delete=True)
        await self.db.flush()
    
    async def update_banner_status(self, banner_id: int, is_enabled: bool) -> dict:
        """
        更新Banner状态
        
        Args:
            banner_id: Banner ID
            is_enabled: 是否启用
        
        Returns:
            更新后的Banner信息
        """
        banner = await super().get_by_id(banner_id)
        banner.is_enabled = is_enabled
        await self.db.flush()
        await self.db.refresh(banner)
        
        return self._format_response(banner)
    
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
            
            try:
                banner = await super().get_by_id(banner_id)
                banner.sort_order = sort_order
            except NotFoundException:
                continue
        
        await self.db.flush()
        
        logger.info(f"Banner sort updated: {len(sort_items)} items")

