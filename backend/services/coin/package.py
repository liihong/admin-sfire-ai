"""
充值套餐服务
用于管理套餐的CRUD操作
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from models.recharge_package import RechargePackage
from schemas.recharge import RechargePackageCreate, RechargePackageUpdate
from utils.exceptions import NotFoundException, BadRequestException


class RechargePackageService:
    """
    充值套餐服务类
    
    职责说明：
    - 套餐数据管理：CRUD操作
    - 套餐查询：获取启用套餐列表、根据ID查询
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化套餐服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
    
    async def get_packages(self, enabled_only: bool = True) -> List[RechargePackage]:
        """
        获取套餐列表
        
        Args:
            enabled_only: 是否只获取启用的套餐
        
        Returns:
            套餐列表（按排序字段排序）
        """
        query = select(RechargePackage)
        
        if enabled_only:
            query = query.where(RechargePackage.status == 1)
        
        query = query.order_by(RechargePackage.sort_order.asc())
        
        result = await self.db.execute(query)
        packages = result.scalars().all()
        
        return list(packages)
    
    async def get_package_by_id(self, package_id: int) -> RechargePackage:
        """
        根据ID获取套餐
        
        Args:
            package_id: 套餐ID
        
        Returns:
            套餐对象
        
        Raises:
            NotFoundException: 套餐不存在
        """
        if package_id <= 0:
            raise BadRequestException("无效的套餐ID")
        
        result = await self.db.execute(
            select(RechargePackage).where(RechargePackage.id == package_id)
        )
        package = result.scalar_one_or_none()
        
        if not package:
            raise NotFoundException(f"套餐 {package_id} 不存在")
        
        return package
    
    async def create_package(self, data: RechargePackageCreate) -> RechargePackage:
        """
        创建套餐（管理后台用）
        
        Args:
            data: 套餐创建数据
        
        Returns:
            创建的套餐对象
        """
        package = RechargePackage(
            name=data.name,
            price=data.price,
            power_amount=data.power_amount,
            unit_price=data.unit_price,
            tag=data.tag,
            description=data.description,
            article_count=data.article_count,
            sort_order=data.sort_order,
            status=data.status,
            is_popular=data.is_popular,
        )
        
        self.db.add(package)
        await self.db.flush()
        await self.db.refresh(package)
        
        logger.info(f"创建套餐成功: {package.id} - {package.name}")
        
        return package
    
    async def update_package(
        self,
        package_id: int,
        data: RechargePackageUpdate
    ) -> RechargePackage:
        """
        更新套餐
        
        Args:
            package_id: 套餐ID
            data: 套餐更新数据
        
        Returns:
            更新后的套餐对象
        
        Raises:
            NotFoundException: 套餐不存在
        """
        package = await self.get_package_by_id(package_id)
        
        # 更新字段（只更新提供的字段）
        if data.name is not None:
            package.name = data.name
        if data.price is not None:
            package.price = data.price
        if data.power_amount is not None:
            package.power_amount = data.power_amount
        if data.unit_price is not None:
            package.unit_price = data.unit_price
        if data.tag is not None:
            package.tag = data.tag
        if data.description is not None:
            package.description = data.description
        if data.article_count is not None:
            package.article_count = data.article_count
        if data.sort_order is not None:
            package.sort_order = data.sort_order
        if data.status is not None:
            package.status = data.status
        if data.is_popular is not None:
            package.is_popular = data.is_popular
        
        await self.db.flush()
        await self.db.refresh(package)
        
        logger.info(f"更新套餐成功: {package.id} - {package.name}")
        
        return package
    
    async def delete_package(self, package_id: int) -> None:
        """
        删除套餐（软删除：设置为禁用状态）
        
        Args:
            package_id: 套餐ID
        
        Raises:
            NotFoundException: 套餐不存在
        """
        package = await self.get_package_by_id(package_id)
        
        # 软删除：设置为禁用状态
        package.status = 0
        
        await self.db.flush()
        
        logger.info(f"删除套餐成功: {package.id} - {package.name}")

