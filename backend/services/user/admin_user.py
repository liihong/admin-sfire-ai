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
from core.tenant_constants import DEFAULT_TENANT_ID
from core.tenant_helpers import tenant_names_by_ids, ensure_tenant_id_exists


class AdminUserService(BaseService):
    """管理员用户管理服务类"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminUser, "管理员用户", check_soft_delete=True)

    async def require_admin_accessible(
        self,
        user_id: int,
        scoped_tenant_id: Optional[int],
    ) -> AdminUser:
        """租户管理员仅能操作归属同一租户的其他管理员账号；平台超管不传 tenant 限制。"""
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.id == user_id, AdminUser.is_deleted == False)
        )
        u = result.scalar_one_or_none()
        if not u:
            raise NotFoundException(msg="管理员不存在")
        if scoped_tenant_id is not None and u.tenant_id != scoped_tenant_id:
            raise NotFoundException(msg="管理员不存在")
        return u
    
    def _format_response(self, user: AdminUser, *, tenant_name: Optional[str] = None) -> dict:
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
            "tenant_id": user.tenant_id,
            "tenant_name": tenant_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    
    async def get_users(
        self,
        params: AdminUserQueryParams,
        *,
        scoped_tenant_id: Optional[int] = None,
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

        if scoped_tenant_id is not None:
            conditions.append(AdminUser.tenant_id == scoped_tenant_id)
        
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

        tid_set = {u.tenant_id for u in users if u.tenant_id is not None}
        names_map = await tenant_names_by_ids(self.db, tid_set)

        user_list = [
            self._format_response(u, tenant_name=names_map.get(u.tenant_id) if u.tenant_id else None)
            for u in users
        ]

        return user_list, total
    
    async def get_user_by_id(self, user_id: int, *, scoped_tenant_id: Optional[int] = None) -> dict:
        """
        根据ID获取管理员用户
        """
        await self.require_admin_accessible(user_id, scoped_tenant_id)
        user = await super().get_by_id(user_id, include_relations=[AdminUser.role])
        tn = None
        if user.tenant_id is not None:
            nm = await tenant_names_by_ids(self.db, {user.tenant_id})
            tn = nm.get(user.tenant_id)
        return self._format_response(user, tenant_name=tn)
    
    async def create_user(self, user_data: AdminUserCreate, *, scoped_tenant_id: Optional[int] = None) -> dict:
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

        if scoped_tenant_id is not None:
            target_tid = scoped_tenant_id
        else:
            body_tid = getattr(user_data, "tenant_id", None)
            if body_tid is not None:
                await ensure_tenant_id_exists(self.db, body_tid)
                target_tid = body_tid
            else:
                target_tid = DEFAULT_TENANT_ID

        def before_create(user: AdminUser, data: AdminUserCreate):
            """创建前的钩子函数"""
            user.password_hash = hash_password(data.password)
            user.tenant_id = target_tid

        def after_create(user: AdminUser):
            """创建后的钩子函数"""
            # 重新加载角色关系
            pass  # 在外部处理
        user = await super().create(
            data=user_data,
            unique_fields=unique_fields,
            before_create=before_create,
            after_create=after_create,
            exclude_fields=["password", "tenant_id"],
        )
        
        await self.db.commit()
        await self.db.refresh(user, ["role"])

        tn = None
        if user.tenant_id is not None:
            nm = await tenant_names_by_ids(self.db, {user.tenant_id})
            tn = nm.get(user.tenant_id)
        return self._format_response(user, tenant_name=tn)

    async def update_user(
        self,
        user_id: int,
        user_data: AdminUserUpdate,
        *,
        scoped_tenant_id: Optional[int] = None,
    ) -> dict:
        """
        更新管理员用户信息
        """
        await self.require_admin_accessible(user_id, scoped_tenant_id)

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

        exclude_extra = ["password"]
        if scoped_tenant_id is not None:
            exclude_extra.append("tenant_id")
        elif update_data.get("tenant_id") is not None:
            await ensure_tenant_id_exists(self.db, update_data["tenant_id"])

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
            exclude_fields=exclude_extra,
        )
        
        await self.db.commit()
        await self.db.refresh(user, ["role"])

        tn = None
        if user.tenant_id is not None:
            nm = await tenant_names_by_ids(self.db, {user.tenant_id})
            tn = nm.get(user.tenant_id)
        return self._format_response(user, tenant_name=tn)

    async def delete_user(self, user_id: int, *, scoped_tenant_id: Optional[int] = None) -> None:
        """
        删除管理员用户（软删除）
        """
        await self.require_admin_accessible(user_id, scoped_tenant_id)
        await super().delete(user_id, hard_delete=False)
        await self.db.commit()
    
    async def change_status(self, user_id: int, status: int, *, scoped_tenant_id: Optional[int] = None) -> None:
        """
        修改管理员用户状态
        """
        await self.require_admin_accessible(user_id, scoped_tenant_id)
        await super().change_status(user_id, status)
        await self.db.commit()

