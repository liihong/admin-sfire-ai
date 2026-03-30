"""
Role Service
角色管理服务（基于roles表和admin_users表的role_id字段）
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.admin_user import AdminUser
from models.menu import Menu
from models.role import Role
from schemas.role import RoleCreate, RoleUpdate, RoleResponse
from utils.exceptions import NotFoundException, BadRequestException
from services.base import BaseService


class RoleService(BaseService):
    """角色管理服务类（后台管理员角色）"""
    
    # 允许的角色代码
    ALLOWED_CODES = {"normal", "member", "partner"}
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Role, "角色", check_soft_delete=False)
    
    async def _get_admin_user_count_by_role(self, role_id: int) -> int:
        """
        统计指定角色的管理员用户数量
        
        Args:
            role_id: 角色ID
            
        Returns:
            管理员用户数量
        """
        count_query = select(func.count(AdminUser.id)).where(
            and_(
                AdminUser.role_id == role_id,
                AdminUser.is_deleted == False
            )
        )
        result = await self.db.execute(count_query)
        return result.scalar() or 0
    
    async def _role_to_dict(self, role: Role) -> Dict[str, Any]:
        """
        将Role模型转换为字典，包含管理员用户数量统计
        
        Args:
            role: Role模型实例
            
        Returns:
            角色信息字典
        """
        # 统计该角色的管理员用户数量
        user_count = await self._get_admin_user_count_by_role(role.id)
        
        return {
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "sort_order": role.sort_order,
            "user_count": user_count,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }
    
    async def get_roles(self) -> List[Dict[str, Any]]:
        """
        获取所有角色列表
        
        统计每个角色的用户数量
        """
        # 从数据库查询所有角色
        query = select(Role).order_by(Role.sort_order, Role.id)
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        # 转换为字典并统计用户数量
        role_list = []
        for role in roles:
            role_dict = await self._role_to_dict(role)
            role_list.append(role_dict)
        
        return role_list
    
    async def get_role_by_id(self, role_id: int) -> Dict[str, Any]:
        """
        根据ID获取角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            角色信息
        """
        role = await super().get_by_id(role_id, error_msg="角色不存在")
        return await self._role_to_dict(role)
    
    async def get_role_by_code(self, code: str) -> Dict[str, Any]:
        """
        根据代码获取角色
        
        Args:
            code: 角色代码（normal/member/partner）
            
        Returns:
            角色信息
        """
        query = select(Role).where(Role.code == code)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundException(msg="角色不存在")
        
        return await self._role_to_dict(role)
    
    async def create_role(self, role_data: RoleCreate) -> Dict[str, Any]:
        """
        创建角色
        
        注意：角色代码必须是normal/member/partner之一
        如果角色代码已存在，则更新现有角色
        
        Args:
            role_data: 角色创建数据
            
        Returns:
            新创建或更新的角色信息
        """
        # 验证角色代码是否允许
        if role_data.code not in self.ALLOWED_CODES:
            raise BadRequestException(
                msg=f"角色代码 '{role_data.code}' 无效，系统仅支持：normal、member、partner"
            )
        
        # 检查角色代码是否已存在
        query = select(Role).where(Role.code == role_data.code)
        result = await self.db.execute(query)
        existing_role = result.scalar_one_or_none()
        
        if existing_role:
            # 如果角色已存在，更新它
            logger.info(f"角色代码 {role_data.code} 已存在，更新角色信息")
            existing_role.name = role_data.name
            existing_role.description = role_data.description
            existing_role.sort_order = role_data.sort_order
            await self.db.flush()
            await self.db.refresh(existing_role)
            return await self._role_to_dict(existing_role)
        
        # 创建新角色
        role = Role(
            code=role_data.code,
            name=role_data.name,
            description=role_data.description,
            sort_order=role_data.sort_order,
        )
        
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        
        logger.info(f"创建角色: {role.name} (code={role.code})")
        
        return await self._role_to_dict(role)
    
    async def update_role(self, role_id: int, role_data: RoleUpdate) -> Dict[str, Any]:
        """
        更新角色信息
        
        注意：不能修改角色代码（code），只能更新名称、描述、排序等信息
        
        Args:
            role_id: 角色ID
            role_data: 更新数据
            
        Returns:
            更新后的角色信息
        """
        role = await super().update(
            obj_id=role_id,
            data=role_data,
            exclude_fields=["code"],  # 不允许修改 code 字段
        )
        
        await self.db.flush()
        await self.db.refresh(role)
        
        return await self._role_to_dict(role)
    
    async def delete_role(self, role_id: int) -> None:
        """
        删除角色
        
        注意：删除角色前需要先检查是否有用户使用该角色
        如果有用户使用，则不能删除
        
        Args:
            role_id: 角色ID
        """
        async def check_users_before_delete(role: Role):
            """删除前的钩子函数：检查是否有管理员用户使用该角色"""
            # 检查是否有管理员用户使用该角色
            user_count = await self._get_admin_user_count_by_role(role.id)
            
            if user_count > 0:
                raise BadRequestException(
                    msg=f"该角色下有 {user_count} 个管理员用户，无法删除。请先将这些用户的角色修改为其他角色后再删除"
                )
        
        await super().delete(role_id, hard_delete=True, before_delete=check_users_before_delete)
        await self.db.flush()

    async def _expand_menu_ids_with_ancestors(self, menu_ids: List[int]) -> List[int]:
        """
        将前端勾选的菜单 ID 扩展为「选中项 + 全部祖先」，再写入 roles.menu_ids。
        避免只存子级 ID 时与权限数据含义不一致。
        """
        raw = {int(mid) for mid in menu_ids if mid is not None}
        if not raw:
            return []

        result = await self.db.execute(select(Menu.id, Menu.parent_id))
        parent_by_id: Dict[int, Optional[int]] = {}
        for mid, pid in result.all():
            parent_by_id[int(mid)] = int(pid) if pid is not None else None

        expanded: set[int] = set()
        for mid in raw:
            if mid not in parent_by_id:
                logger.warning(f"菜单 id={mid} 不存在，已忽略")
                continue
            cur: Optional[int] = mid
            depth = 0
            while cur is not None and depth < 64:
                expanded.add(cur)
                cur = parent_by_id.get(cur)
                depth += 1

        return sorted(expanded)
    
    async def get_role_permissions(self, role_id: int) -> List[int]:
        """获取角色的菜单权限 ID 列表（roles.menu_ids JSON 字段）"""
        role = await super().get_by_id(role_id, error_msg="角色不存在")
        raw = role.menu_ids
        if not raw:
            return []
        return [int(x) for x in raw]
    
    async def set_role_permissions(self, role_id: int, menu_ids: List[int]) -> None:
        """设置角色的菜单权限（写入 roles.menu_ids，并自动并入所选菜单的全部父级 ID）"""
        role = await super().get_by_id(role_id, error_msg="角色不存在")
        unique_ids = await self._expand_menu_ids_with_ancestors(menu_ids)
        role.menu_ids = unique_ids
        await self.db.flush()
        logger.info(f"角色 {role.name} (id={role_id}) 的菜单权限已更新，共 {len(unique_ids)} 项（含父级）")
