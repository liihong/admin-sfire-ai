"""
用户等级配置服务
提供用户等级配置的CRUD操作
"""
from typing import List, Optional, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.user_level import UserLevel as UserLevelModel
from services.base import BaseService


class UserLevelService(BaseService):
    """
    用户等级服务类
    
    继承BaseService，提供等级配置的CRUD操作
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, UserLevelModel, "用户等级", check_soft_delete=False)
    
    async def get_all_enabled_levels(self, tenant_id: Optional[int] = None) -> List[UserLevelModel]:
        """
        获取某租户下所有启用的等级配置（tenant_id 默认按主租户，与存量数据一致）
        """
        from core.tenant_constants import effective_tenant_id

        tid = effective_tenant_id(tenant_id)
        query = select(UserLevelModel).where(
            UserLevelModel.is_enabled == True,
            UserLevelModel.tenant_id == tid,
        ).order_by(UserLevelModel.sort_order)
        
        result = await self.db.execute(query)
        levels = result.scalars().all()
        
        return list(levels)
    
    async def get_level_by_code(self, code: str, tenant_id: Optional[int] = None) -> Optional[UserLevelModel]:
        """
        根据等级代码获取等级配置（同租户内需唯一）
        """
        from core.tenant_constants import effective_tenant_id

        tid = effective_tenant_id(tenant_id)
        query = select(UserLevelModel).where(
            UserLevelModel.code == code,
            UserLevelModel.tenant_id == tid,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
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

