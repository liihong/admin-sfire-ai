"""
AdminUser Service
管理员用户管理服务
"""
from typing import List, Tuple, Optional
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.admin_user import AdminUser
from models.role import Role
from schemas.admin_user import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserQueryParams,
)
from core.security import hash_password
from utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from utils.pagination import paginate, build_order_by, PageResult
from services.base import BaseService


class AdminUserService(BaseService):
    """管理员用户管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminUser, "管理员用户", check_soft_delete=True)
    
    def _format_response(self, user: AdminUser) -> dict:
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
        user_list = [self._format_response(user) for user in users]
        
        return user_list, total
    
    async def get_user_by_id(self, user_id: int) -> dict:
        """
        根据ID获取管理员用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息
        """
        user = await super().get_by_id(user_id, include_relations=[AdminUser.role])
        return self._format_response(user)
    
    async def create_user(self, user_data: AdminUserCreate) -> dict:
        """
        创建管理员用户
        
        Args:
            user_data: 用户创建数据
        
        Returns:
            新用户信息
        """
        # 定义唯一性检查字段
        unique_fields = {
            "username": {"error_msg": "用户名已存在"},
        }
        if user_data.email:
            unique_fields["email"] = {"error_msg": "邮箱已被注册"}
        
        # 验证角色是否存在
        if user_data.role_id:
            from utils.query import get_by_id
            role = await get_by_id(self.db, Role, user_data.role_id, error_msg="角色不存在")
            if not role:
                raise BadRequestException(msg="角色不存在")
        
        def before_create(user: AdminUser, data: AdminUserCreate):
            """创建前的钩子函数"""
            # 处理密码哈希
            user.password_hash = hash_password(data.password)
        
        def after_create(user: AdminUser):
            """创建后的钩子函数"""
            # 重新加载角色关系
            pass  # 在外部处理
        user = await super().create(
            data=user_data,
            unique_fields=unique_fields,
            before_create=before_create,
            after_create=after_create,
            exclude_fields=["password"],  # 密码字段需要在钩子中处理为 password_hash
        )
        
        await self.db.commit()
        await self.db.refresh(user, ["role"])
        
        return self._format_response(user)
    
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
        # 定义唯一性检查字段
        unique_fields = {
            "username": {"error_msg": "用户名已存在"},
            "email": {"error_msg": "邮箱已被注册"},
        }
        
        # 验证角色是否存在
        update_data = user_data.model_dump(exclude_unset=True)
        if "role_id" in update_data and update_data["role_id"]:
            from utils.query import get_by_id
            role = await get_by_id(self.db, Role, update_data["role_id"], error_msg="角色不存在")
            if not role:
                raise BadRequestException(msg="角色不存在")
        
        def before_update(user: AdminUser, data: AdminUserUpdate):
            """更新前的钩子函数"""
            # 处理密码更新
            update_data = data.model_dump(exclude_unset=True)
            if "password" in update_data and update_data["password"]:
                user.password_hash = hash_password(update_data["password"])
        
        def after_update(user: AdminUser):
            """更新后的钩子函数"""
            # 重新加载角色关系
            pass  # 在外部处理
        
        user = await super().update(
            obj_id=user_id,
            data=user_data,
            unique_fields=unique_fields,
            before_update=before_update,
            after_update=after_update,
            exclude_fields=["password"],  # 密码已经在钩子中处理
        )
        
        await self.db.commit()
        await self.db.refresh(user, ["role"])
        
        return self._format_response(user)
    
    async def delete_user(self, user_id: int) -> None:
        """
        删除管理员用户（软删除）
        
        Args:
            user_id: 用户ID
        """
        await super().delete(user_id, hard_delete=False)
        await self.db.commit()
    
    async def change_status(self, user_id: int, status: int) -> None:
        """
        修改管理员用户状态
        
        Args:
            user_id: 用户ID
            status: 状态 (0-封禁, 1-正常)
        """
        await super().change_status(user_id, status)
        await self.db.commit()

