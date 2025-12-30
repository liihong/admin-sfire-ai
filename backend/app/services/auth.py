"""
Authentication Service
认证服务
"""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.utils.exceptions import UnauthorizedException


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def login(self, username: str, password: str) -> str:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            JWT 访问令牌
        
        Raises:
            UnauthorizedException: 用户名或密码错误
        """
        # 查找用户（支持用户名或手机号登录）
        result = await self.db.execute(
            select(User).where(
                ((User.username == username) | (User.phone == username)) &
                (User.is_deleted == False)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Login failed: user not found - {username}")
            raise UnauthorizedException(msg="用户名或密码错误")
        
        # 验证密码
        if not user.password_hash or not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: wrong password - {username}")
            raise UnauthorizedException(msg="用户名或密码错误")
        
        # 检查用户状态
        if not user.is_active:
            logger.warning(f"Login failed: user disabled - {username}")
            raise UnauthorizedException(msg="用户已被封禁")
        
        # 创建访问令牌
        token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"User logged in successfully: {username}")
        
        return token
    
    async def get_user_by_token(self, user_id: int) -> User:
        """
        根据用户ID获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户对象
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UnauthorizedException(msg="用户不存在")
        
        return user
