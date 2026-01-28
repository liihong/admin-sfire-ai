"""
用户权限快照服务
统一管理用户等级对应的权限配置，支持动态调整
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.user import User
from models.user_level import UserLevel as UserLevelModel
from models.project import Project, ProjectStatus


class PermissionService:
    """
    权限服务类
    
    职责：
    - 获取用户权限快照（实时检查VIP过期）
    - 从数据库读取等级配置（支持动态调整）
    - 检查VIP是否过期
    - 检查用户是否可以创建IP
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_permission(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户权限快照
        
        这是核心方法，所有权限判断都应该调用这个方法
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限配置字典，包含：
            - max_ip: 最大IP数量（None表示不限制）
            - ip_type: IP类型（temporary/permanent）
            - daily_tokens: 每日AI能量次数（None表示无限制）
            - can_use_advanced_agent: 是否可使用高级智能体
            - unlimited_conversations: 是否无限制对话
            - level: 用户等级代码
            - level_name: 等级名称
            - vip_expire_date: VIP到期时间
            - is_vip_expired: VIP是否过期
        """
        # 查询用户信息（预加载等级配置）
        query = select(User).where(
            User.id == user_id,
            User.is_deleted == False
        ).options(selectinload(User.user_level))
        
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # 用户不存在，返回默认权限（normal）
            logger.warning(f"用户不存在: user_id={user_id}，返回默认权限")
            return await self._get_default_permission()
        
        # 检查VIP是否过期，获取有效等级
        effective_level_code = self._get_effective_level_code(user)
        
        # 获取等级配置
        level_config = await self.get_level_config(effective_level_code)
        
        # 构建权限快照
        permission = {
            "max_ip": level_config.get("max_ip_count"),
            "ip_type": level_config.get("ip_type"),
            "daily_tokens": level_config.get("daily_tokens_limit"),
            "can_use_advanced_agent": level_config.get("can_use_advanced_agent", False),
            "unlimited_conversations": level_config.get("unlimited_conversations", False),
            "level": effective_level_code,
            "level_name": level_config.get("name", "未知"),
            "vip_expire_date": user.vip_expire_date.isoformat() if user.vip_expire_date else None,
            "is_vip_expired": self._is_vip_expired(user),
        }
        
        return permission
    
    async def get_level_config(self, level_code: str) -> Dict[str, Any]:
        """
        从数据库读取等级配置（支持动态调整）
        
        Args:
            level_code: 等级代码（normal/vip/svip/max）
            
        Returns:
            等级配置字典
        """
        query = select(UserLevelModel).where(
            UserLevelModel.code == level_code,
            UserLevelModel.is_enabled == True
        )
        
        result = await self.db.execute(query)
        level = result.scalar_one_or_none()
        
        if not level:
            logger.warning(f"等级配置不存在或已禁用: level_code={level_code}，返回默认配置")
            return await self._get_default_level_config()
        
        return {
            "code": level.code,
            "name": level.name,
            "max_ip_count": level.max_ip_count,
            "ip_type": level.ip_type,
            "daily_tokens_limit": level.daily_tokens_limit,
            "can_use_advanced_agent": level.can_use_advanced_agent,
            "unlimited_conversations": level.unlimited_conversations,
            "is_enabled": level.is_enabled,
            "sort_order": level.sort_order,
        }
    
    def _get_effective_level_code(self, user: User) -> str:
        """
        获取用户有效等级代码（考虑VIP过期）
        
        Args:
            user: 用户对象
            
        Returns:
            有效等级代码
        """
        # 优先使用level_code（新系统）
        if user.level_code:
            # 如果用户等级是VIP/SVIP/MAX，检查是否过期
            if user.level_code in ["vip", "svip", "max"]:
                if self._is_vip_expired(user):
                    # VIP过期，降级为normal
                    logger.info(f"用户VIP已过期: user_id={user.id}, level_code={user.level_code}")
                    return "normal"
            return user.level_code
        
        # 兼容旧数据：从level枚举映射到level_code
        level_mapping = {
            "normal": "normal",
            "member": "vip",      # member映射为vip
            "partner": "svip",    # partner映射为svip
        }
        
        old_level_code = user.level.value if hasattr(user.level, "value") else str(user.level)
        mapped_code = level_mapping.get(old_level_code, "normal")
        
        # 检查VIP是否过期
        if mapped_code in ["vip", "svip", "max"]:
            if self._is_vip_expired(user):
                return "normal"
        
        return mapped_code
    
    def _is_vip_expired(self, user: User) -> bool:
        """
        检查VIP是否过期
        
        Args:
            user: 用户对象
            
        Returns:
            True-已过期, False-未过期或永久有效
        """
        if not user.vip_expire_date:
            return False  # 没有设置过期时间，视为永久有效
        
        now = datetime.now(timezone.utc)
        is_expired = user.vip_expire_date < now
        
        if is_expired:
            logger.debug(f"用户VIP已过期: user_id={user.id}, expire_date={user.vip_expire_date}")
        
        return is_expired
    
    async def check_can_create_ip(self, user_id: int) -> Tuple[bool, str]:
        """
        检查用户是否可以创建新IP
        
        Args:
            user_id: 用户ID
            
        Returns:
            (是否可以创建, 错误消息)
        """
        # 获取用户权限
        permission = await self.get_user_permission(user_id)
        
        # 获取当前活跃IP数量（不包括已冻结和已删除的）
        query = select(Project).where(
            Project.user_id == user_id,
            Project.is_deleted == False,
            Project.status == ProjectStatus.ACTIVE.value  # 只统计正常状态的IP
        )
        
        result = await self.db.execute(query)
        active_projects = result.scalars().all()
        current_count = len(active_projects)
        
        # 检查是否可以创建
        max_ip = permission.get("max_ip")
        
        if max_ip is None:
            # 不限制
            return True, ""
        
        if current_count >= max_ip:
            level_name = permission.get("level_name", "当前等级")
            return False, f"您的{level_name}最多可创建 {max_ip} 个IP，当前已有 {current_count} 个，请升级会员或删除部分IP"
        
        return True, ""
    
    async def _get_default_permission(self) -> Dict[str, Any]:
        """获取默认权限（normal等级）"""
        default_config = await self._get_default_level_config()
        return {
            "max_ip": default_config.get("max_ip_count"),
            "ip_type": default_config.get("ip_type"),
            "daily_tokens": default_config.get("daily_tokens_limit"),
            "can_use_advanced_agent": default_config.get("can_use_advanced_agent", False),
            "unlimited_conversations": default_config.get("unlimited_conversations", False),
            "level": "normal",
            "level_name": default_config.get("name", "观望者"),
            "vip_expire_date": None,
            "is_vip_expired": False,
        }
    
    async def _get_default_level_config(self) -> Dict[str, Any]:
        """获取默认等级配置（normal）"""
        return {
            "code": "normal",
            "name": "观望者",
            "max_ip_count": 1,
            "ip_type": "temporary",
            "daily_tokens_limit": 3,
            "can_use_advanced_agent": False,
            "unlimited_conversations": False,
            "is_enabled": True,
            "sort_order": 1,
        }






