"""
Menu Service
菜单服务层
"""
from typing import List, Optional, Dict, Any
from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse
from app.utils.exceptions import NotFoundException, BadRequestException


class MenuService:
    """
    菜单服务类
    
    提供菜单的 CRUD 操作和树形结构生成
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_menu_tree(self, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """
        获取菜单树形结构
        
        递归生成前端需要的树形菜单
        
        Args:
            include_hidden: 是否包含隐藏菜单
        
        Returns:
            List[Dict]: 树形菜单列表
        """
        # 查询所有启用的顶级菜单
        query = select(Menu).where(
            and_(
                Menu.parent_id.is_(None),
                Menu.is_enabled == True,
            )
        ).order_by(Menu.sort_order)
        
        if not include_hidden:
            query = query.where(Menu.is_hide == False)
        
        # 使用 selectinload 预加载子菜单
        query = query.options(
            selectinload(Menu.children).selectinload(Menu.children).selectinload(Menu.children)
        )
        
        result = await self.db.execute(query)
        menus = result.scalars().all()
        
        # 转换为前端格式
        menu_list = []
        for menu in menus:
            menu_dict = self._build_menu_tree(menu, include_hidden)
            if menu_dict:
                menu_list.append(menu_dict)
        
        return menu_list
    
    def _build_menu_tree(self, menu: Menu, include_hidden: bool = False) -> Optional[Dict[str, Any]]:
        """
        递归构建单个菜单及其子菜单
        
        Args:
            menu: 菜单对象
            include_hidden: 是否包含隐藏菜单
        
        Returns:
            Dict: 菜单字典
        """
        if not menu.is_enabled:
            return None
        
        if not include_hidden and menu.is_hide:
            return None
        
        menu_dict = {
            "path": menu.path,
            "name": menu.name,
            "meta": menu.to_meta_dict(),
        }
        
        # 可选字段
        if menu.component:
            menu_dict["component"] = menu.component
        if menu.redirect:
            menu_dict["redirect"] = menu.redirect
        
        # 处理子菜单
        if menu.children:
            children = []
            for child in sorted(menu.children, key=lambda x: x.sort_order):
                child_dict = self._build_menu_tree(child, include_hidden)
                if child_dict:
                    children.append(child_dict)
            
            if children:
                menu_dict["children"] = children
        
        return menu_dict
    
    async def get_all_menus(self) -> List[Dict[str, Any]]:
        """
        获取所有菜单（用于管理后台）
        
        Returns:
            List[Dict]: 所有菜单列表（树形结构）
        """
        # 查询所有顶级菜单
        query = select(Menu).where(
            Menu.parent_id.is_(None)
        ).order_by(Menu.sort_order).options(
            selectinload(Menu.children).selectinload(Menu.children).selectinload(Menu.children)
        )
        
        result = await self.db.execute(query)
        menus = result.scalars().all()
        
        # 转换为管理格式
        return [self._menu_to_admin_dict(menu) for menu in menus]
    
    def _menu_to_admin_dict(self, menu: Menu) -> Dict[str, Any]:
        """
        转换菜单为管理后台格式
        """
        menu_dict = {
            "id": menu.id,
            "parentId": menu.parent_id,
            "name": menu.name,
            "path": menu.path,
            "component": menu.component,
            "redirect": menu.redirect,
            "sortOrder": menu.sort_order,
            "icon": menu.icon,
            "title": menu.title,
            "isLink": menu.is_link or "",
            "isHide": menu.is_hide,
            "isFull": menu.is_full,
            "isAffix": menu.is_affix,
            "isKeepAlive": menu.is_keep_alive,
            "isEnabled": menu.is_enabled,
            "createdAt": menu.created_at.isoformat() if menu.created_at else None,
            "updatedAt": menu.updated_at.isoformat() if menu.updated_at else None,
        }
        
        if menu.children:
            menu_dict["children"] = [
                self._menu_to_admin_dict(child)
                for child in sorted(menu.children, key=lambda x: x.sort_order)
            ]
        
        return menu_dict
    
    async def get_menu_by_id(self, menu_id: int) -> Menu:
        """
        根据 ID 获取菜单
        
        Args:
            menu_id: 菜单 ID
        
        Returns:
            Menu: 菜单对象
        
        Raises:
            NotFoundException: 菜单不存在
        """
        result = await self.db.execute(
            select(Menu).where(Menu.id == menu_id)
        )
        menu = result.scalar_one_or_none()
        
        if not menu:
            raise NotFoundException(msg="菜单不存在")
        
        return menu
    
    async def create_menu(self, data: MenuCreate) -> Menu:
        """
        创建菜单
        
        Args:
            data: 创建菜单数据
        
        Returns:
            Menu: 创建的菜单对象
        """
        # 检查父菜单是否存在
        if data.parent_id:
            await self.get_menu_by_id(data.parent_id)
        
        # 检查名称是否重复
        existing = await self.db.execute(
            select(Menu).where(Menu.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise BadRequestException(msg=f"菜单名称 '{data.name}' 已存在")
        
        # 创建菜单
        menu = Menu(**data.model_dump())
        self.db.add(menu)
        await self.db.flush()
        await self.db.refresh(menu)
        
        logger.info(f"Menu created: {menu.name}")
        return menu
    
    async def update_menu(self, menu_id: int, data: MenuUpdate) -> Menu:
        """
        更新菜单
        
        Args:
            menu_id: 菜单 ID
            data: 更新数据
        
        Returns:
            Menu: 更新后的菜单对象
        """
        menu = await self.get_menu_by_id(menu_id)
        
        # 检查父菜单是否存在
        if data.parent_id is not None and data.parent_id:
            if data.parent_id == menu_id:
                raise BadRequestException(msg="父菜单不能是自己")
            await self.get_menu_by_id(data.parent_id)
        
        # 检查名称是否重复
        if data.name and data.name != menu.name:
            existing = await self.db.execute(
                select(Menu).where(Menu.name == data.name)
            )
            if existing.scalar_one_or_none():
                raise BadRequestException(msg=f"菜单名称 '{data.name}' 已存在")
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(menu, field, value)
        
        await self.db.flush()
        await self.db.refresh(menu)
        
        logger.info(f"Menu updated: {menu.name}")
        return menu
    
    async def delete_menu(self, menu_id: int) -> None:
        """
        删除菜单
        
        会级联删除所有子菜单
        
        Args:
            menu_id: 菜单 ID
        """
        menu = await self.get_menu_by_id(menu_id)
        
        await self.db.delete(menu)
        await self.db.flush()
        
        logger.info(f"Menu deleted: {menu.name}")
    
    async def get_auth_buttons(self) -> Dict[str, List[str]]:
        """
        获取按钮权限
        
        TODO: 根据用户角色返回对应的按钮权限
        当前返回完整的按钮权限列表
        
        Returns:
            Dict[str, List[str]]: 按钮权限字典
        """
        # TODO: 根据用户角色从数据库获取权限
        # 当前返回完整权限
        return {
            "home": ["view"],
            "userManage": ["add", "edit", "delete", "export", "import", "recharge", "deduct", "changeLevel"],
            "adminUserManage": ["add", "edit", "delete", "changeStatus"],
            "computeLog": ["view", "export"],
            "appConfig": ["view", "edit"],
            "agentManage": ["add", "edit", "delete", "status"],
            "menuManage": ["add", "edit", "delete"],
            "roleManage": ["add", "edit", "delete"],
            "dictManage": ["add", "edit", "delete"],
        }


