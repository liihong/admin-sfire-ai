"""
Quick Entry Service
快捷入口管理服务层
"""
from typing import List, Tuple, Optional
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.quick_entry import QuickEntry, EntryType, ActionType, EntryTag
from schemas.quick_entry import (
    QuickEntryCreate,
    QuickEntryUpdate,
    QuickEntryQueryParams,
    QuickEntryResponse,
)
from utils.exceptions import NotFoundException, BadRequestException
from services.base import BaseService


class QuickEntryService(BaseService):
    """快捷入口管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, QuickEntry, "快捷入口", check_soft_delete=False)
    
    def _format_response(self, entry: QuickEntry) -> dict:
        """格式化快捷入口响应"""
        return {
            "id": entry.id,
            "unique_key": entry.unique_key,
            "type": entry.type.value,
            "title": entry.title,
            "subtitle": entry.subtitle,
            "icon_class": entry.icon_class,
            "bg_color": entry.bg_color,
            "action_type": entry.action_type.value,
            "action_value": entry.action_value,
            "tag": entry.tag.value,
            "priority": entry.priority,
            "status": entry.status,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }
    
    async def get_quick_entries(
        self,
        params: QuickEntryQueryParams
    ) -> Tuple[List[dict], int]:
        """
        获取快捷入口列表
        
        Args:
            params: 查询参数
        
        Returns:
            (快捷入口列表, 总数量)
        """
        # 构建查询条件
        conditions = []
        
        if params.type:
            type_enum = EntryType(params.type)
            conditions.append(QuickEntry.type == type_enum)
        
        if params.status is not None:
            conditions.append(QuickEntry.status == params.status)
        
        if params.tag:
            tag_enum = EntryTag(params.tag)
            conditions.append(QuickEntry.tag == tag_enum)
        
        if params.title:
            conditions.append(QuickEntry.title.like(f"%{params.title}%"))
        
        # 查询总数
        count_query = select(func.count(QuickEntry.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(QuickEntry)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(asc(QuickEntry.priority), desc(QuickEntry.created_at))
        query = query.offset(params.offset).limit(params.pageSize)
        
        result = await self.db.execute(query)
        entries = result.scalars().all()
        
        # 格式化响应
        entry_list = [self._format_response(entry) for entry in entries]
        
        return entry_list, total
    
    async def get_quick_entry_by_id(self, entry_id: int) -> dict:
        """
        根据ID获取快捷入口
        
        Args:
            entry_id: 入口ID
        
        Returns:
            快捷入口信息
        """
        entry = await super().get_by_id(entry_id, error_msg="快捷入口不存在")
        return self._format_response(entry)
    
    async def create_quick_entry(self, entry_data: QuickEntryCreate) -> dict:
        """
        创建快捷入口
        
        Args:
            entry_data: 快捷入口创建数据
        
        Returns:
            新快捷入口信息
        """
        def before_create(entry: QuickEntry, data: QuickEntryCreate):
            """创建前的钩子函数"""
            # 转换枚举类型
            entry.type = EntryType(data.type)
            entry.action_type = ActionType(data.action_type)
            entry.tag = EntryTag(data.tag)
        
        entry = await super().create(
            data=entry_data,
            unique_fields={
                "unique_key": {"error_msg": "唯一标识已存在"}
            },
            before_create=before_create,
        )
        
        await self.db.flush()
        await self.db.refresh(entry)
        
        return self._format_response(entry)
    
    async def update_quick_entry(self, entry_id: int, entry_data: QuickEntryUpdate) -> dict:
        """
        更新快捷入口
        
        Args:
            entry_id: 入口ID
            entry_data: 快捷入口更新数据
        
        Returns:
            更新后的快捷入口信息
        """
        def before_update(entry: QuickEntry, data: QuickEntryUpdate):
            """更新前的钩子函数"""
            # 处理枚举类型转换
            update_data = data.model_dump(exclude_unset=True)
            if "type" in update_data and update_data["type"] is not None:
                entry.type = EntryType(update_data["type"])
            if "action_type" in update_data and update_data["action_type"] is not None:
                entry.action_type = ActionType(update_data["action_type"])
            if "tag" in update_data and update_data["tag"] is not None:
                entry.tag = EntryTag(update_data["tag"])
        
        # 检查唯一性（如果更新了 unique_key）
        unique_fields = None
        if entry_data.unique_key is not None:
            unique_fields = {
                "unique_key": {"error_msg": "唯一标识已存在"}
            }
        
        entry = await super().update(
            obj_id=entry_id,
            data=entry_data,
            unique_fields=unique_fields,
            before_update=before_update,
        )
        
        await self.db.flush()
        await self.db.refresh(entry)
        
        return self._format_response(entry)
    
    async def delete_quick_entry(self, entry_id: int) -> None:
        """
        删除快捷入口
        
        Args:
            entry_id: 入口ID
        """
        await super().delete(entry_id, hard_delete=True)
        await self.db.flush()
    
    async def update_quick_entry_status(self, entry_id: int, status: int) -> dict:
        """
        更新快捷入口状态
        
        Args:
            entry_id: 入口ID
            status: 状态值（0-禁用, 1-启用, 2-即将上线）
        
        Returns:
            更新后的快捷入口信息
        """
        if status not in [0, 1, 2]:
            raise BadRequestException(msg="状态值无效，必须是0、1或2")
        
        entry = await super().get_by_id(entry_id)
        entry.status = status
        await self.db.flush()
        await self.db.refresh(entry)
        
        return self._format_response(entry)
    
    async def update_quick_entry_sort(self, sort_items: List[dict]) -> None:
        """
        批量更新快捷入口排序
        
        Args:
            sort_items: 排序项列表，格式: [{'id': 1, 'priority': 0}, ...]
        """
        for item in sort_items:
            entry_id = item.get("id")
            priority = item.get("priority")
            
            if entry_id is None or priority is None:
                continue
            
            try:
                entry = await super().get_by_id(entry_id)
                entry.priority = priority
            except NotFoundException:
                continue
        
        await self.db.flush()
        
        logger.info(f"快捷入口排序更新: {len(sort_items)} 项")

