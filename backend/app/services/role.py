"""
Role Service
角色管理服务（基于roles表和users表的level字段）
"""
from typing import List, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User, UserLevel
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.utils.exceptions import NotFoundException, BadRequestException


class RoleService:
    """角色管理服务类"""
    
    # 允许的角色代码（对应UserLevel枚举）
    ALLOWED_CODES = {"normal", "member", "partner"}
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_user_count_by_level(self, level: UserLevel) -> int:
        """
        统计指定等级的用户数量
        
        Args:
            level: 用户等级枚举
            
        Returns:
            用户数量
        """
        count_query = select(func.count(User.id)).where(
            and_(
                User.level == level,
                User.is_deleted == False
            )
        )
        result = await self.db.execute(count_query)
        return result.scalar() or 0
    
    async def _role_to_dict(self, role: Role) -> Dict[str, Any]:
        """
        将Role模型转换为字典，包含用户数量统计
        
        Args:
            role: Role模型实例
            
        Returns:
            角色信息字典
        """
        # 将角色代码转换为UserLevel枚举
        try:
            level_enum = UserLevel(role.code)
        except ValueError:
            logger.warning(f"角色代码 {role.code} 不是有效的UserLevel值")
            user_count = 0
        else:
            # 统计该角色的用户数量
            user_count = await self._get_user_count_by_level(level_enum)
        
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
        query = select(Role).where(Role.id == role_id)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundException(msg="角色不存在")
        
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
        
        注意：角色代码必须是normal/member/partner之一，对应UserLevel枚举
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
        query = select(Role).where(Role.id == role_id)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundException(msg="角色不存在")
        
        # 更新角色信息（仅更新允许的字段）
        if role_data.name is not None:
            role.name = role_data.name
        
        if role_data.description is not None:
            role.description = role_data.description
        
        if role_data.sort_order is not None:
            role.sort_order = role_data.sort_order
        
        await self.db.flush()
        await self.db.refresh(role)
        
        logger.info(f"更新角色: {role.name} (id={role_id})")
        
        return await self._role_to_dict(role)
    
    async def delete_role(self, role_id: int) -> None:
        """
        删除角色
        
        注意：删除角色前需要先检查是否有用户使用该角色
        如果有用户使用，则不能删除
        
        Args:
            role_id: 角色ID
        """
        query = select(Role).where(Role.id == role_id)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundException(msg="角色不存在")
        
        # 将角色代码转换为UserLevel枚举
        try:
            level_enum = UserLevel(role.code)
        except ValueError:
            logger.warning(f"角色代码 {role.code} 不是有效的UserLevel值，允许删除")
            user_count = 0
        else:
            # 检查是否有用户使用该角色
            user_count = await self._get_user_count_by_level(level_enum)
        
        if user_count > 0:
            raise BadRequestException(
                msg=f"该角色下有 {user_count} 个用户，无法删除。请先将这些用户的角色修改为其他角色后再删除"
            )
        
        # 删除角色
        await self.db.delete(role)
        await self.db.flush()
        
        logger.info(f"删除角色: {role.name} (id={role_id}, code={role.code})")
    
    async def get_role_permissions(self, role_id: int) -> List[int]:
        """
        获取角色的菜单权限ID列表
        
        注意：此方法目前返回空列表，因为角色权限关联表尚未实现
        实际项目中需要创建 role_menu 关联表来存储角色和菜单的多对多关系
        
        Args:
            role_id: 角色ID
            
        Returns:
            菜单ID列表
        """
        # TODO: 实现角色权限关联表的查询逻辑
        # 这里暂时返回空列表，需要根据实际的关联表实现
        logger.warning(f"get_role_permissions 方法尚未完全实现，返回空列表 (role_id={role_id})")
        return []
    
    async def set_role_permissions(self, role_id: int, menu_ids: List[int]) -> None:
        """
        设置角色的菜单权限
        
        注意：此方法目前仅做参数验证，实际的权限关联逻辑需要实现 role_menu 关联表
        
        Args:
            role_id: 角色ID
            menu_ids: 菜单ID列表
        """
        # 验证角色是否存在
        query = select(Role).where(Role.id == role_id)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise NotFoundException(msg="角色不存在")
        
        # TODO: 实现角色权限关联表的更新逻辑
        # 1. 删除该角色的所有现有权限关联
        # 2. 批量插入新的权限关联
        # 需要根据实际的关联表实现
        
        logger.warning(f"set_role_permissions 方法尚未完全实现 (role_id={role_id}, menu_ids={menu_ids})")
        logger.info(f"角色 {role.name} (id={role_id}) 的权限设置为: {menu_ids}")
