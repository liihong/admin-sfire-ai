"""
User Service
用户管理服务
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple, Optional, Dict, Any
import secrets
import string
import hashlib

from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.user import User
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




class UserService(BaseService):
    """用户管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User, "用户", check_soft_delete=True)
    
    
    def _format_response(self, user: User) -> dict:
        """格式化用户响应数据"""
        level_code = user.level_code or "normal"
        level_name = user.user_level.name if user.user_level else None
        
        return {
            "id": str(user.id),
            "username": user.username,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "levelCode": level_code,
            "levelName": level_name,
            "computePower": {
                "balance": float(user.balance),
                "frozen": float(user.frozen_balance),
                "totalConsumed": 0,  # TODO: 从 compute_logs 统计
                "totalRecharged": 0,  # TODO: 从 compute_logs 统计
                "lastRechargeTime": None,
            },
            "role": "admin" if level_code in ["svip", "max"] else "user",
            "inviteCode": None,  # TODO: 生成邀请码逻辑
            "inviterId": str(user.parent_id) if user.parent_id else None,
            "inviterName": user.parent.username if user.parent else None,
            "createTime": user.created_at.isoformat() if user.created_at else None,
            "lastLoginTime": user.updated_at.isoformat() if user.updated_at else None,
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
            # 按level_code查询
            conditions.append(User.level_code == params.level)
        
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
        
        # 查询数据 - 使用 selectinload 预加载 parent 和 user_level 关系以避免 N+1 查询
        from sqlalchemy.orm import selectinload
        query = (
            select(User)
            .options(
                selectinload(User.parent),
                selectinload(User.user_level)  # 预加载用户等级配置
            )
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
            # 设置level_code
            user.level_code = data.level_code or "normal"
        
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
            # 特殊处理等级字段 - 优先使用level_code（新系统）
            update_data = data.model_dump(exclude_unset=True)
            
            # 优先使用level_code（新系统）
            if "level_code" in update_data and update_data["level_code"]:
                user.level_code = update_data["level_code"]
        
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
        vip_expire_date: Optional[datetime] = None,
        remark: Optional[str] = None
    ) -> None:
        """
        修改用户等级（集成升级/降级处理）
        
        Args:
            user_id: 用户ID
            level: 等级代码 (normal/vip/svip/max)
            vip_expire_date: VIP到期时间（可选）
            remark: 备注
        """
        from services.system.membership import MembershipService
        
        user = await super().get_by_id(user_id)
        
        old_level_code = user.level_code or "normal"
        
        # 更新level_code
        user.level_code = level
        
        # 更新VIP到期时间
        if vip_expire_date is not None:
            user.vip_expire_date = vip_expire_date
        
        await self.db.flush()
        
        # 处理升级/降级逻辑
        membership_service = MembershipService(self.db)
        
        # 判断是升级、降级还是续费
        level_order = {"normal": 1, "vip": 2, "svip": 3, "max": 4}
        old_order = level_order.get(old_level_code, 1)
        new_order = level_order.get(level, 1)
        
        if new_order > old_order:
            # 升级：立即解冻IP
            logger.info(f"用户升级: user_id={user_id}, {old_level_code} -> {level}")
            upgrade_result = await membership_service.handle_user_upgrade(user_id)
            logger.info(f"升级处理结果: {upgrade_result}")
        elif new_order < old_order:
            # 降级：冻结超出权限的IP
            logger.info(f"用户降级: user_id={user_id}, {old_level_code} -> {level}")
            downgrade_result = await membership_service.handle_user_downgrade(user_id)
            logger.info(f"降级处理结果: {downgrade_result}")
        elif new_order == old_order and vip_expire_date is not None:
            # 同等级续费：如果设置了VIP到期时间，也触发升级处理（解冻IP）
            logger.info(f"用户续费: user_id={user_id}, level={level}, vip_expire_date={vip_expire_date}")
            upgrade_result = await membership_service.handle_user_upgrade(user_id)
            logger.info(f"续费处理结果: {upgrade_result}")
        
        logger.info(
            f"User level changed: {user.username}, "
            f"{old_level_code} -> {level}, remark: {remark}"
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
    
    async def get_user_by_unionid(self, unionid: str) -> Optional[User]:
        """
        通过 unionid 查找用户
        
        Args:
            unionid: 微信 unionid（跨平台用户识别）
        
        Returns:
            用户对象，如果不存在则返回 None
        """
        result = await self.db.execute(
            select(User).where(
                User.unionid == unionid,
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
    
    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        通过手机号查找用户
        
        Args:
            phone: 手机号
        
        Returns:
            用户对象，如果不存在则返回 None
        """
        result = await self.db.execute(
            select(User).where(
                User.phone == phone,
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
        
        # 创建用户
        user = User(
            username=user_data.get("username") or f"user_{secrets.token_hex(4)}",
            password_hash=user_data.get("password_hash"),
            openid=user_data.get("openid"),
            unionid=user_data.get("unionid"),
            phone=user_data.get("phone"),
            nickname=user_data.get("nickname"),
            avatar=user_data.get("avatar"),
            level_code=user_data.get("level_code", "normal"),
            parent_id=user_data.get("parent_id"),
            is_active=user_data.get("is_active", True),
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        logger.info(f"User created from dict: {user.username} (openid: {user.openid})")

        return user

    async def reset_password(self, user_id: int, new_password: str = "123456") -> None:
        """
        重置用户密码

        密码处理流程:
        1. 前端使用 MD5 加密密码 (如 "123456" → "e10adc3949ba59abbe56e057f20f883e")
        2. 后端接收 MD5 密码后，使用 bcrypt 进行哈希存储

        Args:
            user_id: 用户ID
            new_password: 新密码（明文，默认为 "123456"）
        """
        user = await super().get_by_id(user_id)

        # 1. 先对明文密码进行 MD5 加密（模拟前端行为）
        md5_password = hashlib.md5(new_password.encode('utf-8')).hexdigest()

        # 2. 对 MD5 密码进行 bcrypt 哈希存储
        user.password_hash = hash_password(md5_password)

        await self.db.flush()

        logger.info(
            f"User password reset: {user.username}, "
            f"new password (MD5): {md5_password}"
        )
