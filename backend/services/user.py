"""
User Service
用户管理服务
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple, Optional, Dict, Any
import secrets
import string

from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.user import User, UserLevel
from models.compute import ComputeLog, ComputeType
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserQueryParams,
)
from core.security import hash_password
from utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from utils.pagination import paginate, build_order_by, PageResult
from services.base import BaseService


# 等级映射
LEVEL_MAP = {
    "normal": 0,
    "member": 1,
    "partner": 2,
}

LEVEL_REVERSE_MAP = {
    0: UserLevel.NORMAL,
    1: UserLevel.MEMBER,
    2: UserLevel.PARTNER,
}


class UserService(BaseService):
    """用户管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User, "用户", check_soft_delete=True)
    
    def _level_to_int(self, level: UserLevel) -> int:
        """将 UserLevel 枚举转为整数"""
        return LEVEL_MAP.get(level.value, 0)
    
    def _format_response(self, user: User) -> dict:
        """格式化用户响应数据（兼容前端接口）"""
        return {
            "id": str(user.id),
            "username": user.username,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "level": self._level_to_int(user.level),
            "computePower": {
                "balance": float(user.balance),
                "frozen": float(user.frozen_balance),
                "totalConsumed": 0,  # TODO: 从 compute_logs 统计
                "totalRecharged": 0,  # TODO: 从 compute_logs 统计
                "lastRechargeTime": None,
            },
            "role": "admin" if user.level == UserLevel.PARTNER else "user",
            "inviteCode": None,  # TODO: 生成邀请码逻辑
            "inviterId": str(user.parent_id) if user.parent_id else None,
            "inviterName": user.parent.username if user.parent else None,  # 使用预加载的 parent 关系
            "createTime": user.created_at.isoformat() if user.created_at else None,
            "lastLoginTime": None,  # TODO: 记录登录时间
            "status": 1 if user.is_active else 0,
        }
    
    async def get_users(
        self,
        params: UserQueryParams
    ) -> Tuple[List[dict], int]:
        """
        获取用户列表
        
        Args:
            params: 查询参数
        
        Returns:
            (用户列表, 总数量)
        """
        # 构建查询条件
        conditions = [User.is_deleted == False]
        
        if params.username:
            conditions.append(User.username.like(f"%{params.username}%"))
        
        if params.phone:
            conditions.append(User.phone.like(f"%{params.phone}%"))
        
        if params.level:
            level_enum = UserLevel(params.level)
            conditions.append(User.level == level_enum)
        
        if params.is_active is not None:
            conditions.append(User.is_active == params.is_active)
        
        if params.minBalance is not None:
            conditions.append(User.balance >= params.minBalance)
        
        if params.maxBalance is not None:
            conditions.append(User.balance <= params.maxBalance)
        
        # 查询总数
        count_query = select(func.count(User.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据 - 使用 selectinload 预加载 parent 关系以避免 N+1 查询
        from sqlalchemy.orm import selectinload
        query = (
            select(User)
            .options(selectinload(User.parent))
            .where(and_(*conditions))
            .order_by(User.created_at.desc())
            .offset(params.offset)
            .limit(params.pageSize)
        )
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # 格式化响应
        user_list = [self._format_response(user) for user in users]
        
        return user_list, total
    
    async def get_user_by_id(self, user_id: int) -> dict:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息
        """
        user = await super().get_by_id(user_id, include_relations=[User.parent])
        return self._format_response(user)
    
    async def create_user(self, user_data: UserCreate) -> dict:
        """
        创建用户
        
        Args:
            user_data: 用户创建数据
        
        Returns:
            新用户信息
        """
        # 定义唯一性检查字段
        unique_fields = {
            "username": {"error_msg": "用户名已存在"},
        }
        if user_data.phone:
            unique_fields["phone"] = {"error_msg": "手机号已被注册"}
        
        def before_create(user: User, data: UserCreate):
            """创建前的钩子函数"""
            # 处理密码哈希
            user.password_hash = hash_password(data.password)
            # 转换等级
            if data.level:
                user.level = UserLevel(data.level)
            else:
                user.level = UserLevel.NORMAL
        
        user = await super().create(
            data=user_data,
            unique_fields=unique_fields,
            before_create=before_create,
        )
        
        await self.db.flush()
        await self.db.refresh(user)
        
        return self._format_response(user)
    
    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate
    ) -> dict:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 更新数据
        
        Returns:
            更新后的用户信息
        """
        def before_update(user: User, data: UserUpdate):
            """更新前的钩子函数"""
            # 特殊处理等级字段
            update_data = data.model_dump(exclude_unset=True)
            if "level" in update_data and update_data["level"]:
                user.level = UserLevel(update_data["level"])
        
        user = await super().update(
            obj_id=user_id,
            data=user_data,
            before_update=before_update,
        )
        
        await self.db.flush()
        await self.db.refresh(user)
        
        return self._format_response(user)
    
    async def delete_user(self, user_id: int) -> None:
        """
        删除用户（软删除）
        
        Args:
            user_id: 用户ID
        """
        await super().delete(user_id, hard_delete=False)
        await self.db.flush()
    
    async def change_status(self, user_id: int, status: int) -> None:
        """
        修改用户状态
        
        Args:
            user_id: 用户ID
            status: 状态 (0-封禁, 1-正常)
        """
        await super().change_status(user_id, status)
        await self.db.flush()
    
    async def recharge(
        self,
        user_id: int,
        amount: Decimal,
        remark: Optional[str] = None
    ) -> None:
        """
        用户充值
        
        Args:
            user_id: 用户ID
            amount: 充值金额
            remark: 备注
        """
        user = await super().get_by_id(user_id)
        
        user.balance += amount
        
        # TODO: 记录算力变动日志
        
        await self.db.flush()
        
        logger.info(
            f"User recharged: {user.username}, "
            f"amount: {amount}, remark: {remark}"
        )
    
    async def deduct(
        self,
        user_id: int,
        amount: Decimal,
        reason: str
    ) -> None:
        """
        用户扣费
        
        Args:
            user_id: 用户ID
            amount: 扣费金额
            reason: 扣费原因
        """
        user = await super().get_by_id(user_id)
        
        if user.available_balance < amount:
            raise BadRequestException(msg="可用余额不足")
        
        user.balance -= amount
        
        # TODO: 记录算力变动日志
        
        await self.db.flush()
        
        logger.info(
            f"User deducted: {user.username}, "
            f"amount: {amount}, reason: {reason}"
        )
    
    async def change_level(
        self,
        user_id: int,
        level: str,
        remark: Optional[str] = None
    ) -> None:
        """
        修改用户等级
        
        Args:
            user_id: 用户ID
            level: 等级 (normal/member/partner)
            remark: 备注
        """
        user = await super().get_by_id(user_id)
        
        old_level = user.level
        user.level = UserLevel(level)
        
        await self.db.flush()
        
        logger.info(
            f"User level changed: {user.username}, "
            f"{old_level.value} -> {level}, remark: {remark}"
        )
    
    async def get_user_by_openid(self, openid: str) -> Optional[User]:
        """
        通过 openid 查找用户
        
        Args:
            openid: 微信 openid
        
        Returns:
            用户对象，如果不存在则返回 None
        """
        result = await self.db.execute(
            select(User).where(
                User.openid == openid,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        通过用户名查找用户
        
        Args:
            username: 用户名
        
        Returns:
            用户对象，如果不存在则返回 None
        """
        result = await self.db.execute(
            select(User).where(
                User.username == username,
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def create_user_from_dict(self, user_data: dict) -> User:
        """
        从字典创建用户（用于小程序登录等场景）
        
        Args:
            user_data: 用户数据字典
        
        Returns:
            创建的用户对象
        """
        from models.user import UserLevel
        
        # 检查用户名是否已存在
        if user_data.get("username"):
            existing = await self.get_user_by_username(user_data["username"])
            if existing:
                raise BadRequestException(msg="用户名已存在")
        
        # 检查 openid 是否已存在
        if user_data.get("openid"):
            existing = await self.get_user_by_openid(user_data["openid"])
            if existing:
                return existing
        
        # 转换等级
        level = user_data.get("level", "normal")
        level_enum = UserLevel(level) if isinstance(level, str) else level
        
        # 创建用户
        user = User(
            username=user_data.get("username") or f"user_{secrets.token_hex(4)}",
            password_hash=user_data.get("password_hash"),
            openid=user_data.get("openid"),
            unionid=user_data.get("unionid"),
            phone=user_data.get("phone"),
            nickname=user_data.get("nickname"),
            avatar=user_data.get("avatar"),
            level=level_enum,
            parent_id=user_data.get("parent_id"),
            is_active=user_data.get("is_active", True),
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        logger.info(f"User created from dict: {user.username} (openid: {user.openid})")
        
        return user