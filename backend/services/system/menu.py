"""
Menu Service
菜单服务层
"""
from collections import defaultdict
from typing import List, Optional, Dict, Any, Set
from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.menu import Menu
from schemas.menu import MenuCreate, MenuUpdate, MenuResponse
from utils.exceptions import NotFoundException, BadRequestException


class MenuService:
    """
    菜单服务类
    
    提供菜单的 CRUD 操作和树形结构生成
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _expand_to_ancestor_ids(self, seed_ids: Set[int]) -> Set[int]:
        """从若干菜单 id 沿 parent_id 走到根，得到路径上全部 id（用于把禁用父级也载入内存以便建树）。"""
        if not seed_ids:
            return set()
        result = await self.db.execute(select(Menu.id, Menu.parent_id))
        parent_map: Dict[int, Optional[int]] = {}
        for mid, pid in result.all():
            parent_map[int(mid)] = int(pid) if pid is not None else None
        out: Set[int] = set()
        for mid in seed_ids:
            cur: Optional[int] = int(mid)
            depth = 0
            while cur is not None and depth < 64:
                out.add(cur)
                cur = parent_map.get(cur)
                depth += 1
        return out

    async def _expand_allowed_with_hidden_routes(self, allowed: Set[int]) -> Set[int]:
        """
        角色仅勾选可见子菜单时，同父级下的「隐藏路由页」（如 tool-kit/run）不会进入 menu_ids，
        导致前端动态路由未注册、跳转 name 报 No match。此处自动并入：
        - 与已授权项同父级的隐藏菜单；
        - 已授权菜单下的隐藏子菜单（仅勾选父级时也能补全）。
        """
        if not allowed:
            return allowed
        out = set(allowed)
        r1 = await self.db.execute(
            select(Menu.parent_id).where(Menu.id.in_(allowed), Menu.parent_id.isnot(None))
        )
        parent_ids = {int(x) for x in r1.scalars().all() if x is not None}
        if parent_ids:
            r2 = await self.db.execute(
                select(Menu.id).where(
                    Menu.parent_id.in_(parent_ids),
                    Menu.is_hide == True,
                )
            )
            out.update(int(x) for x in r2.scalars().all())
        r3 = await self.db.execute(
            select(Menu.id).where(
                Menu.parent_id.in_(allowed),
                Menu.is_hide == True,
            )
        )
        out.update(int(x) for x in r3.scalars().all())
        return out
    
    async def get_menu_tree(
        self,
        include_hidden: bool = False,
        allowed_menu_ids: Optional[Set[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取菜单树形结构
        
        递归生成前端需要的树形菜单
        
        Args:
            include_hidden: 是否包含隐藏菜单
            allowed_menu_ids: 若传入集合，则只保留这些菜单 ID 及其为展示子节点所必需的父级；
                传入 None 表示不限制（超级管理员或未启用按角色过滤时）
        
        Returns:
            List[Dict]: 树形菜单列表
        """
        if allowed_menu_ids is not None:
            allowed_menu_ids = {int(x) for x in allowed_menu_ids}
            if len(allowed_menu_ids) > 0:
                allowed_menu_ids = await self._expand_allowed_with_hidden_routes(allowed_menu_ids)

        # 一次查出菜单并在内存建树（任意深度）
        # 按角色过滤时：必须把「授权菜单及其全部祖先」一并载入；若某级父菜单 is_enabled=false，
        # 仅查启用菜单会导致子菜单从根不可达，整棵树为空（例如 menu_ids 含 [25,26] 仍无菜单）
        if allowed_menu_ids is not None and len(allowed_menu_ids) > 0:
            chain_ids = await self._expand_to_ancestor_ids(allowed_menu_ids)
            q = (
                select(Menu)
                .where(or_(Menu.is_enabled == True, Menu.id.in_(chain_ids)))
                .order_by(Menu.sort_order)
            )
        else:
            q = select(Menu).where(Menu.is_enabled == True).order_by(Menu.sort_order)

        result = await self.db.execute(q)
        all_menus = list(result.scalars().all())

        children_by_parent: Dict[Optional[int], List[Menu]] = defaultdict(list)
        for m in all_menus:
            children_by_parent[m.parent_id].append(m)
        for pid in children_by_parent:
            children_by_parent[pid].sort(key=lambda x: x.sort_order)

        roots = children_by_parent.get(None, [])
        if not include_hidden:
            roots = [m for m in roots if not m.is_hide]

        menu_list: List[Dict[str, Any]] = []
        for menu in roots:
            menu_dict = self._build_menu_tree_from_map(
                menu, children_by_parent, include_hidden, allowed_menu_ids
            )
            if menu_dict:
                menu_list.append(menu_dict)

        return menu_list

    def _build_menu_tree_from_map(
        self,
        menu: Menu,
        children_by_parent: Dict[Optional[int], List[Menu]],
        include_hidden: bool = False,
        allowed_menu_ids: Optional[Set[int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """在内存中的父子映射上递归构建路由树（任意深度）。"""
        if not include_hidden and menu.is_hide:
            return None

        filtered_children: List[Dict[str, Any]] = []
        for child in children_by_parent.get(menu.id, []):
            child_dict = self._build_menu_tree_from_map(
                child, children_by_parent, include_hidden, allowed_menu_ids
            )
            if child_dict:
                filtered_children.append(child_dict)

        if allowed_menu_ids is not None:
            self_allowed = menu.id in allowed_menu_ids
            if not filtered_children and not self_allowed:
                return None
        else:
            if not menu.is_enabled:
                return None

        menu_dict = {
            "path": menu.path,
            "name": menu.name,
            "meta": menu.to_meta_dict(),
        }

        if menu.component:
            menu_dict["component"] = menu.component
        if menu.redirect:
            menu_dict["redirect"] = menu.redirect

        if filtered_children:
            menu_dict["children"] = filtered_children

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


