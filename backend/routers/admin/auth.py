"""
Authentication Endpoints
认证相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db import get_db
from schemas import LoginRequest, LoginResponse
from services.auth import AuthService
from services.menu import MenuService
from utils.response import success, ResponseMsg
from core.security import decode_token, create_access_token, create_refresh_token
from core.config import settings
from utils.exceptions import BadRequestException

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
    tokens = await auth_service.login(request.username, request.password)

    return success(
        data={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"]
        },
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


# ============== Token Refresh ==============

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


@router.post("/refresh", summary="刷新令牌")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    使用刷新令牌获取新的访问令牌

    - **refresh_token**: 刷新令牌（7天有效）

    流程:
    1. 验证refresh_token是否有效
    2. 提取用户ID并查询管理员用户
    3. 生成新的access_token和refresh_token
    4. 返回新token
    """
    from models.admin_user import AdminUser
    from sqlalchemy import select
    from loguru import logger

    try:
        # 1. 解码并验证refresh_token
        payload = decode_token(request.refresh_token)
        if not payload:
            raise BadRequestException("刷新令牌无效或已过期")

        # 2. 验证token类型
        token_type = payload.get("type")
        if token_type != "refresh":
            raise BadRequestException("令牌类型错误")

        # 3. 提取用户ID
        user_id = payload.get("sub")
        if not user_id:
            raise BadRequestException("令牌数据无效")

        # 4. 查询管理员用户
        result = await db.execute(
            select(AdminUser).where(
                AdminUser.id == int(user_id),
                AdminUser.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise BadRequestException("用户不存在")

        if not user.is_active:
            raise BadRequestException("用户已被封禁")

        # 5. 生成新的access_token和refresh_token
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        logger.info(f"Admin token refreshed successfully for user: {user.id}")

        return success(
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            },
            msg="令牌刷新成功"
        )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Admin token refresh failed: {str(e)}", exc_info=True)
        raise BadRequestException(f"令牌刷新失败: {str(e)}")

