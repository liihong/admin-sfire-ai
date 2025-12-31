"""
AdminUser Service
管理员用户管理服务
"""
from typing import List, Tuple, Optional
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models.admin_user import AdminUser
from app.models.role import Role
from app.schemas.admin_user import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserQueryParams,
)
from app.core.security import hash_password
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from app.utils.pagination import paginate, build_order_by, PageResult


class AdminUserService:
    """管理员用户管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _format_user_response(self, user: AdminUser) -> dict:
        """格式化用户响应数据"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "role_code": user.role.code if user.role else None,
            "is_active": user.is_active,
            "remark": user.remark,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    
    async def get_users(
        self,
        params: AdminUserQueryParams
    ) -> Tuple[List[dict], int]:
        """
        获取管理员用户列表
        
        Args:
            params: 查询参数
        
        Returns:
            (用户列表, 总数量)
        """
        # 构建查询条件
        conditions = [AdminUser.is_deleted == False]
        
        if params.username:
            conditions.append(AdminUser.username.like(f"%{params.username}%"))
        
        if params.email:
            conditions.append(AdminUser.email.like(f"%{params.email}%"))
        
        if params.role_id:
            conditions.append(AdminUser.role_id == params.role_id)
        
        if params.is_active is not None:
            conditions.append(AdminUser.is_active == params.is_active)
        
        # 查询总数
        count_query = select(func.count(AdminUser.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据（包含角色信息）
        query = (
            select(AdminUser)
            .options(selectinload(AdminUser.role))
            .where(and_(*conditions))
            .order_by(AdminUser.created_at.desc())
            .offset(params.offset)
            .limit(params.pageSize)
        )
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # 格式化响应
        user_list = [self._format_user_response(user) for user in users]
        
        return user_list, total
    
    async def get_user_by_id(self, user_id: int) -> dict:
        """
        根据ID获取管理员用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息
        """
        result = await self.db.execute(
            select(AdminUser)
            .options(selectinload(AdminUser.role))
            .where(
                AdminUser.id == user_id,
                AdminUser.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(msg="用户不存在")
        
        return self._format_user_response(user)
    
    async def create_user(self, user_data: AdminUserCreate) -> dict:
        """
        创建管理员用户
        
        Args:
            user_data: 用户创建数据
        
        Returns:
            新用户信息
        """
        # 检查用户名是否已存在
        existing = await self.db.execute(
            select(AdminUser).where(
                AdminUser.username == user_data.username,
                AdminUser.is_deleted == False
            )
        )
        if existing.scalar_one_or_none():
            raise BadRequestException(msg="用户名已存在")
        
        # 检查邮箱是否已存在
        if user_data.email:
            existing = await self.db.execute(
                select(AdminUser).where(
                    AdminUser.email == user_data.email,
                    AdminUser.is_deleted == False
                )
            )
            if existing.scalar_one_or_none():
                raise BadRequestException(msg="邮箱已被注册")
        
        # 验证角色是否存在
        if user_data.role_id:
            role_result = await self.db.execute(
                select(Role).where(Role.id == user_data.role_id)
            )
            if not role_result.scalar_one_or_none():
                raise BadRequestException(msg="角色不存在")
        
        # 创建用户
        user = AdminUser(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            email=user_data.email,
            role_id=user_data.role_id,
            remark=user_data.remark,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # 重新加载角色关系
        await self.db.refresh(user, ["role"])
        
        logger.info(f"AdminUser created: {user.username}")
        
        return self._format_user_response(user)
    
    async def update_user(
        self,
        user_id: int,
        user_data: AdminUserUpdate
    ) -> dict:
        """
        更新管理员用户信息
        
        Args:
            user_id: 用户ID
            user_data: 更新数据
        
        Returns:
            更新后的用户信息
        """
        result = await self.db.execute(
            select(AdminUser).where(
                AdminUser.id == user_id,
                AdminUser.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(msg="用户不存在")
        
        # 更新非空字段
        update_data = user_data.model_dump(exclude_unset=True)
        
        # 检查用户名是否冲突
        if "username" in update_data:
            existing = await self.db.execute(
                select(AdminUser).where(
                    AdminUser.username == update_data["username"],
                    AdminUser.id != user_id,
                    AdminUser.is_deleted == False
                )
            )
            if existing.scalar_one_or_none():
                raise BadRequestException(msg="用户名已存在")
        
        # 检查邮箱是否冲突
        if "email" in update_data and update_data["email"]:
            existing = await self.db.execute(
                select(AdminUser).where(
                    AdminUser.email == update_data["email"],
                    AdminUser.id != user_id,
                    AdminUser.is_deleted == False
                )
            )
            if existing.scalar_one_or_none():
                raise BadRequestException(msg="邮箱已被注册")
        
        # 验证角色是否存在
        if "role_id" in update_data and update_data["role_id"]:
            role_result = await self.db.execute(
                select(Role).where(Role.id == update_data["role_id"])
            )
            if not role_result.scalar_one_or_none():
                raise BadRequestException(msg="角色不存在")
        
        # 处理密码更新
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = hash_password(update_data["password"])
            del update_data["password"]
        
        # 更新字段
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # 重新加载角色关系
        await self.db.refresh(user, ["role"])
        
        logger.info(f"AdminUser updated: {user.username}")
        
        return self._format_user_response(user)
    
    async def delete_user(self, user_id: int) -> None:
        """
        删除管理员用户（软删除）
        
        Args:
            user_id: 用户ID
        """
        result = await self.db.execute(
            select(AdminUser).where(
                AdminUser.id == user_id,
                AdminUser.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(msg="用户不存在")
        
        user.is_deleted = True
        await self.db.commit()
        
        logger.info(f"AdminUser deleted (soft): {user.username}")
    
    async def change_status(self, user_id: int, status: int) -> None:
        """
        修改管理员用户状态
        
        Args:
            user_id: 用户ID
            status: 状态 (0-封禁, 1-正常)
        """
        result = await self.db.execute(
            select(AdminUser).where(
                AdminUser.id == user_id,
                AdminUser.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(msg="用户不存在")
        
        user.is_active = (status == 1)
        await self.db.commit()
        
        status_text = "正常" if status == 1 else "封禁"
        logger.info(f"AdminUser status changed: {user.username} -> {status_text}")

