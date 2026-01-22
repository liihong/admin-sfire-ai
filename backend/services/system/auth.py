"""
Authentication Service
认证服务
"""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.admin_user import AdminUser
from core.security import verify_password, create_access_token, create_refresh_token
from core.config import settings
from utils.exceptions import UnauthorizedException
from typing import Dict


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def login(self, username: str, password: str) -> Dict[str, any]:
        """
        管理员用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            包含 access_token 和 refresh_token 的字典

        Raises:
            UnauthorizedException: 用户名或密码错误
        """
        # 查找管理员用户（支持用户名或邮箱登录）
        result = await self.db.execute(
            select(AdminUser).where(
                ((AdminUser.username == username) | (AdminUser.email == username)) &
                (AdminUser.is_deleted == False)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Login failed: admin user not found - {username}")
            raise UnauthorizedException(msg="用户名或密码错误")

        # 验证密码
        if not user.password_hash or not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: wrong password - {username}")
            raise UnauthorizedException(msg="用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            logger.warning(f"Login failed: admin user disabled - {username}")
            raise UnauthorizedException(msg="用户已被封禁")

        # 创建访问令牌和刷新令牌
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        logger.info(f"AdminUser logged in successfully: {username}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 秒数
        }
    
    async def get_user_by_token(self, user_id: int) -> AdminUser:
        """
        根据用户ID获取管理员用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            管理员用户对象
        """
        result = await self.db.execute(
            select(AdminUser).where(
                AdminUser.id == user_id,
                AdminUser.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UnauthorizedException(msg="用户不存在")
        
        return user
