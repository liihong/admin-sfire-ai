"""
数据字典服务
提供字典类型和字典项的 CRUD 操作
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.dictionary import Dictionary, DictionaryItem
from schemas.dictionary import (
    DictCreate,
    DictUpdate,
    DictQueryParams,
    DictItemCreate,
    DictItemUpdate,
    DictItemQueryParams,
    DictItemSimple,
)
from utils.exceptions import NotFoundException, BadRequestException


class DictionaryService:
    """
    字典类型服务
    
    提供字典类型的 CRUD 操作和字典项查询功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== 字典类型操作 ==============
    
    async def get_dict_by_id(self, dict_id: int, with_items: bool = False) -> Dictionary:
        """
        根据ID获取字典类型
        
        Args:
            dict_id: 字典ID
            with_items: 是否包含字典项
        
        Returns:
            字典类型对象
        """
        query = select(Dictionary).where(Dictionary.id == dict_id)
        
        if with_items:
            query = query.options(selectinload(Dictionary.items))
        
        result = await self.db.execute(query)
        dict_obj = result.scalar_one_or_none()
        
        if not dict_obj:
            raise NotFoundException(msg="字典类型不存在")
        
        return dict_obj
    
    async def get_dict_by_code(self, dict_code: str, with_items: bool = False) -> Optional[Dictionary]:
        """
        根据编码获取字典类型
        
        Args:
            dict_code: 字典编码
            with_items: 是否包含字典项
        
        Returns:
            字典类型对象（不存在时返回 None）
        """
        query = select(Dictionary).where(Dictionary.dict_code == dict_code)
        
        if with_items:
            query = query.options(selectinload(Dictionary.items))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_dict(self, data: DictCreate) -> Dictionary:
        """
        创建字典类型
        
        Args:
            data: 创建数据
        
        Returns:
            创建的字典类型
        """
        # 检查编码是否已存在
        existing = await self.get_dict_by_code(data.dict_code)
        if existing:
            raise BadRequestException(msg=f"字典编码 '{data.dict_code}' 已存在")
        
        dict_obj = Dictionary(**data.model_dump())
        self.db.add(dict_obj)
        await self.db.flush()
        await self.db.refresh(dict_obj)
        
        logger.info(f"字典类型创建成功: {dict_obj.dict_code}")
        return dict_obj
    
    async def update_dict(self, dict_id: int, data: DictUpdate) -> Dictionary:
        """
        更新字典类型
        
        Args:
            dict_id: 字典ID
            data: 更新数据
        
        Returns:
            更新后的字典类型
        """
        dict_obj = await self.get_dict_by_id(dict_id)
        
        # 如果要更新编码，检查是否与其他记录冲突
        if data.dict_code and data.dict_code != dict_obj.dict_code:
            existing = await self.get_dict_by_code(data.dict_code)
            if existing:
                raise BadRequestException(msg=f"字典编码 '{data.dict_code}' 已存在")
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dict_obj, field, value)
        
        await self.db.flush()
        await self.db.refresh(dict_obj)
        
        logger.info(f"字典类型更新成功: {dict_obj.dict_code}")
        return dict_obj
    
    async def delete_dict(self, dict_id: int) -> None:
        """
        删除字典类型（级联删除字典项）
        
        Args:
            dict_id: 字典ID
        """
        dict_obj = await self.get_dict_by_id(dict_id)
        
        await self.db.delete(dict_obj)
        await self.db.flush()
        
        logger.info(f"字典类型删除成功: {dict_obj.dict_code}")
    
    async def get_dict_list(
        self,
        params: DictQueryParams
    ) -> Tuple[List[Dictionary], int]:
        """
        获取字典类型列表（分页）
        
        Args:
            params: 查询参数
        
        Returns:
            (字典类型列表, 总数量)
        """
        # 构建查询条件
        conditions = []
        
        if params.dict_code:
            conditions.append(Dictionary.dict_code == params.dict_code)
        
        if params.dict_name:
            conditions.append(Dictionary.dict_name.like(f"%{params.dict_name}%"))
        
        if params.is_enabled is not None:
            conditions.append(Dictionary.is_enabled == params.is_enabled)
        
        # 查询总数
        count_query = select(func.count(Dictionary.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(Dictionary)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Dictionary.sort_order, Dictionary.id)
        
        offset = (params.pageNum - 1) * params.pageSize
        query = query.offset(offset).limit(params.pageSize)
        
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total
    
    # ============== 字典项操作 ==============
    
    async def get_item_by_id(self, item_id: int) -> DictionaryItem:
        """
        根据ID获取字典项
        
        Args:
            item_id: 字典项ID
        
        Returns:
            字典项对象
        """
        query = select(DictionaryItem).where(DictionaryItem.id == item_id)
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise NotFoundException(msg="字典项不存在")
        
        return item
    
    async def create_item(self, data: DictItemCreate) -> DictionaryItem:
        """
        创建字典项
        
        Args:
            data: 创建数据
        
        Returns:
            创建的字典项
        """
        # 验证字典类型是否存在
        await self.get_dict_by_id(data.dict_id)
        
        item = DictionaryItem(**data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        
        logger.info(f"字典项创建成功: {item.item_label}")
        return item
    
    async def update_item(self, item_id: int, data: DictItemUpdate) -> DictionaryItem:
        """
        更新字典项
        
        Args:
            item_id: 字典项ID
            data: 更新数据
        
        Returns:
            更新后的字典项
        """
        item = await self.get_item_by_id(item_id)
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        await self.db.flush()
        await self.db.refresh(item)
        
        logger.info(f"字典项更新成功: {item.item_label}")
        return item
    
    async def delete_item(self, item_id: int) -> None:
        """
        删除字典项
        
        Args:
            item_id: 字典项ID
        """
        item = await self.get_item_by_id(item_id)
        
        await self.db.delete(item)
        await self.db.flush()
        
        logger.info(f"字典项删除成功: {item.item_label}")
    
    async def get_item_list(
        self,
        params: DictItemQueryParams
    ) -> Tuple[List[DictionaryItem], int]:
        """
        获取字典项列表（分页）
        
        Args:
            params: 查询参数
        
        Returns:
            (字典项列表, 总数量)
        """
        # 构建查询条件
        conditions = []
        
        if params.dict_id:
            conditions.append(DictionaryItem.dict_id == params.dict_id)
        
        if params.dict_code:
            # 需要关联查询
            subquery = select(Dictionary.id).where(Dictionary.dict_code == params.dict_code)
            conditions.append(DictionaryItem.dict_id.in_(subquery))
        
        if params.item_value:
            conditions.append(DictionaryItem.item_value.like(f"%{params.item_value}%"))
        
        if params.item_label:
            conditions.append(DictionaryItem.item_label.like(f"%{params.item_label}%"))
        
        if params.is_enabled is not None:
            conditions.append(DictionaryItem.is_enabled == params.is_enabled)
        
        # 查询总数
        count_query = select(func.count(DictionaryItem.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(DictionaryItem)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(DictionaryItem.sort_order, DictionaryItem.id)
        
        offset = (params.pageNum - 1) * params.pageSize
        query = query.offset(offset).limit(params.pageSize)
        
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total
    
    # ============== 便捷查询方法 ==============
    
    async def get_items_by_code(
        self,
        dict_code: str,
        enabled_only: bool = True
    ) -> List[DictItemSimple]:
        """
        根据字典编码获取所有字典项（用于下拉选项）
        
        Args:
            dict_code: 字典编码
            enabled_only: 是否只返回启用的项
        
        Returns:
            字典项简单响应列表 [{label, value}]
        """
        # 获取字典类型
        dict_obj = await self.get_dict_by_code(dict_code, with_items=True)
        
        if not dict_obj:
            return []
        
        # 如果字典类型被禁用，返回空列表
        if enabled_only and not dict_obj.is_enabled:
            return []
        
        # 过滤并排序字典项
        items = dict_obj.items
        if enabled_only:
            items = [item for item in items if item.is_enabled]
        
        # 按排序顺序排序
        items = sorted(items, key=lambda x: (x.sort_order, x.id))
        
        return [DictItemSimple.from_item(item) for item in items]
    
    async def get_multiple_dict_items(
        self,
        dict_codes: List[str],
        enabled_only: bool = True
    ) -> Dict[str, List[DictItemSimple]]:
        """
        批量获取多个字典的字典项
        
        Args:
            dict_codes: 字典编码列表
            enabled_only: 是否只返回启用的项
        
        Returns:
            字典项映射 {dict_code: [{label, value}]}
        """
        result = {}
        for code in dict_codes:
            result[code] = await self.get_items_by_code(code, enabled_only)
        return result




















