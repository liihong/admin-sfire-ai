"""
用户等级配置服务
提供用户等级配置的 CRUD 操作（全租户共用系统等级，存储于 SYSTEM_USER_LEVEL_TENANT_ID）
"""
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.tenant_constants import SYSTEM_USER_LEVEL_TENANT_ID
from models.user_level import UserLevel as UserLevelModel
from services.base import BaseService


class UserLevelService(BaseService):
    """
    用户等级服务类

    继承 BaseService，提供等级配置的 CRUD 操作
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db, UserLevelModel, "用户等级", check_soft_delete=False)

    def _system_level_condition(self):
        return UserLevelModel.tenant_id == SYSTEM_USER_LEVEL_TENANT_ID

    async def get_all_enabled_levels(self, tenant_id: Optional[int] = None) -> List[UserLevelModel]:
        """
        获取系统级所有启用的等级配置（全租户共用，忽略 tenant_id 参数）
        """
        query = (
            select(UserLevelModel)
            .where(
                UserLevelModel.is_enabled == True,
                self._system_level_condition(),
            )
            .order_by(UserLevelModel.sort_order)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_level_by_code(self, code: str, tenant_id: Optional[int] = None) -> Optional[UserLevelModel]:
        """
        根据等级代码获取系统级等级配置（全租户共用）
        """
        query = select(UserLevelModel).where(
            UserLevelModel.code == code,
            self._system_level_condition(),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        conditions: Optional[List] = None,
        order_by: Optional[Any] = None,
        offset: int = 0,
        limit: int = 10,
        formatter: Optional[Any] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """仅返回系统级等级列表"""
        system_conditions = [self._system_level_condition()]
        if conditions:
            system_conditions.extend(conditions)
        return await super().get_list(
            conditions=system_conditions,
            order_by=order_by or UserLevelModel.sort_order,
            offset=offset,
            limit=limit,
            formatter=formatter,
        )

    async def create(self, data, unique_fields=None, before_create=None, after_create=None, exclude_fields=None):
        """创建系统级等级，强制 tenant_id=SYSTEM_USER_LEVEL_TENANT_ID"""
        from utils.exceptions import BadRequestException

        existing = await self.get_level_by_code(data.code)
        if existing:
            raise BadRequestException(msg=f"等级代码 '{data.code}' 已存在")

        def _force_system_tenant(obj, _data):
            obj.tenant_id = SYSTEM_USER_LEVEL_TENANT_ID
            if before_create:
                before_create(obj, _data)

        return await super().create(
            data,
            unique_fields=None,
            before_create=_force_system_tenant,
            after_create=after_create,
            exclude_fields=exclude_fields,
        )

    async def get_by_id(self, obj_id, error_msg=None, include_relations=None):
        level = await super().get_by_id(obj_id, error_msg, include_relations)
        if level.tenant_id != SYSTEM_USER_LEVEL_TENANT_ID:
            from utils.exceptions import NotFoundException
            raise NotFoundException(msg=error_msg or f"{self.resource_name}不存在")
        return level

    async def update_level_config(
        self,
        level_id: int,
        max_ip_count: Optional[int] = None,
        daily_tokens_limit: Optional[int] = None,
        can_use_advanced_agent: Optional[bool] = None,
        unlimited_conversations: Optional[bool] = None,
        is_enabled: Optional[bool] = None,
    ) -> UserLevelModel:
        """
        更新等级配置（部分字段）

        Args:
            level_id: 等级ID
            max_ip_count: 最大IP数量（可选）
            daily_tokens_limit: 每日AI能量限制（可选）
            can_use_advanced_agent: 是否可使用高级智能体（可选）
            unlimited_conversations: 是否无限制对话（可选）
            is_enabled: 是否启用（可选）

        Returns:
            更新后的等级配置对象
        """
        level = await self.get_by_id(level_id)
        if level.tenant_id != SYSTEM_USER_LEVEL_TENANT_ID:
            from utils.exceptions import BadRequestException
            raise BadRequestException(msg="仅支持修改系统级用户等级")

        if max_ip_count is not None:
            level.max_ip_count = max_ip_count
        if daily_tokens_limit is not None:
            level.daily_tokens_limit = daily_tokens_limit
        if can_use_advanced_agent is not None:
            level.can_use_advanced_agent = can_use_advanced_agent
        if unlimited_conversations is not None:
            level.unlimited_conversations = unlimited_conversations
        if is_enabled is not None:
            level.is_enabled = is_enabled

        await self.db.flush()
        await self.db.refresh(level)

        logger.info(f"更新等级配置: level_id={level_id}, code={level.code}")

        return level
