"""
Menu Endpoints
菜单管理接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.menu import MenuService
from app.schemas.menu import MenuCreate, MenuUpdate
from app.utils.response import success, ResponseMsg

router = APIRouter()


@router.get("/list", summary="获取菜单列表")
async def get_menu_list(
    db: AsyncSession = Depends(get_db),
):
    """
    获取菜单列表（树形结构）
    
    返回格式匹配 Geeker Admin 前端 Menu.MenuOptions 接口
    
    用于动态路由和菜单渲染
    """
    menu_service = MenuService(db)
    menus = await menu_service.get_menu_tree(include_hidden=True)
    
    return success(data=menus)


@router.get("/all", summary="获取所有菜单（管理用）")
async def get_all_menus(
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有菜单（用于管理后台）
    
    包含所有字段和状态信息
    """
    menu_service = MenuService(db)
    menus = await menu_service.get_all_menus()
    
    return success(data=menus)


@router.get("/{menu_id}", summary="获取菜单详情")
async def get_menu_detail(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取菜单详情
    """
    menu_service = MenuService(db)
    menu = await menu_service.get_menu_by_id(menu_id)
    
    return success(data={
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
        "activeMenu": menu.active_menu,
        "perms": menu.perms,
        "requiredLevel": menu.required_level,
        "requiredComputePower": menu.required_compute_power,
        "consumeComputePower": menu.consume_compute_power,
        "isEnabled": menu.is_enabled,
    })


@router.post("", summary="创建菜单")
async def create_menu(
    data: MenuCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新菜单
    """
    menu_service = MenuService(db)
    menu = await menu_service.create_menu(data)
    
    return success(data={"id": menu.id}, msg=ResponseMsg.CREATED)


@router.put("/{menu_id}", summary="更新菜单")
async def update_menu(
    menu_id: int,
    data: MenuUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新菜单信息
    """
    menu_service = MenuService(db)
    menu = await menu_service.update_menu(menu_id, data)
    
    return success(data={"id": menu.id}, msg=ResponseMsg.UPDATED)


@router.delete("/{menu_id}", summary="删除菜单")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    删除菜单
    
    会级联删除所有子菜单
    """
    menu_service = MenuService(db)
    await menu_service.delete_menu(menu_id)
    
    return success(msg=ResponseMsg.DELETED)


