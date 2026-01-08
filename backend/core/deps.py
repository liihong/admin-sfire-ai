"""
API Dependencies
API 依赖项
"""
from typing import Optional
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 延迟导入 get_db 以避免循环导入
# db 模块在初始化时会导入 core.config，而 core/__init__.py 会导入 core.deps
# 如果在模块级别导入 get_db，会形成循环依赖
from core.security import decode_token
from utils.exceptions import UnauthorizedException, ForbiddenException
from models.admin_user import AdminUser
from models.role import Role
from models.user import User


def _get_db_dependency():
    """
    延迟导入 get_db 以避免循环导入
    这个函数在运行时才会导入 db 模块
    返回 get_db 函数本身，供 Depends 使用
    """
    from db import get_db
    return get_db


# 创建一个异步生成器函数来延迟导入 get_db
async def _get_db():
    """延迟导入 get_db 的包装函数"""
    from db import get_db
    async for session in get_db():
        yield session


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer Token"),
    db: AsyncSession = Depends(_get_db),
) -> AdminUser:
    """
    获取当前登录的管理员用户
    
    从 Authorization header 中提取并验证 JWT token
    """
    if not authorization:
        raise UnauthorizedException(msg="未提供认证令牌")
    
    # 提取 Bearer token
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException(msg="无效的认证格式")
    
    # 解码 token
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException(msg="令牌无效或已过期")
    
    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(msg="令牌数据无效")
    
    # 从数据库获取管理员用户
    result = await db.execute(
        select(AdminUser).where(
            AdminUser.id == int(user_id),
            AdminUser.is_deleted == False
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException(msg="用户不存在")
    
    if not user.is_active:
        raise UnauthorizedException(msg="用户已被封禁")
    
    return user


async def get_current_active_user(
    current_user: AdminUser = Depends(get_current_user),
) -> AdminUser:
    """获取当前活跃用户（已验证状态）"""
    return current_user


async def get_current_admin(
    current_user: AdminUser = Depends(get_current_user),
) -> AdminUser:
    """获取当前管理员用户（需要角色权限）"""
    # 检查用户是否有角色
    if not current_user.role_id:
        raise ForbiddenException(msg="需要管理员权限")
    
    # 可以进一步检查角色代码，例如只有特定角色才能访问
    # 这里暂时只检查是否有角色
    return current_user


async def get_current_miniprogram_user(
    authorization: Optional[str] = Header(None, description="Bearer Token"),
    db: AsyncSession = Depends(_get_db),
) -> User:
    """
    获取当前登录的小程序用户
    
    从 Authorization header 中提取并验证 JWT token
    适用于微信小程序接口
    """
    if not authorization:
        raise UnauthorizedException(msg="未提供认证令牌")
    
    # 提取 Bearer token
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException(msg="无效的认证格式")
    
    # 解码 token
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException(msg="令牌无效或已过期")
    
    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(msg="令牌数据无效")
    
    # 从数据库获取用户（小程序用户使用 User 表，不是 AdminUser）
    result = await db.execute(
        select(User).where(
            User.id == int(user_id),
            User.is_deleted == False
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException(msg="用户不存在")
    
    if not user.is_active:
        raise UnauthorizedException(msg="用户已被封禁")
    
    return user





