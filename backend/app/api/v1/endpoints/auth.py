"""
Authentication Endpoints
认证相关接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import LoginRequest, LoginResponse
from app.services.auth import AuthService
from app.services.menu import MenuService
from app.utils.response import success, ResponseMsg

router = APIRouter()


@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回访问令牌
    """
    auth_service = AuthService(db)
    token = await auth_service.login(request.username, request.password)
    
    return success(
        data={"access_token": token},
        msg=ResponseMsg.LOGIN_SUCCESS
    )


@router.post("/logout", summary="用户退出")
async def logout():
    """
    用户退出
    
    前端清除本地 token 即可
    """
    return success(msg=ResponseMsg.LOGOUT_SUCCESS)


@router.get("/buttons", summary="获取按钮权限")
async def get_auth_buttons(
    db: AsyncSession = Depends(get_db),
):
    """
    获取按钮权限列表
    
    返回用户的按钮级别权限
    
    格式: { "pageName": ["add", "edit", "delete"] }
    """
    menu_service = MenuService(db)
    buttons = await menu_service.get_auth_buttons()
    return success(data=buttons)


@router.get("/menus", summary="获取菜单权限")
async def get_auth_menus(
    db: AsyncSession = Depends(get_db),
):
    """
    获取菜单权限列表
    
    返回用户可访问的菜单（树形结构）
    """
    menu_service = MenuService(db)
    menus = await menu_service.get_menu_tree(include_hidden=True)
    return success(data=menus)


