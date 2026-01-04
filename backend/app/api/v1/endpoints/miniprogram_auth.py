"""
MiniProgram Authentication Endpoints
微信小程序认证接口
"""
import secrets
import string
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db import get_db
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings
from app.api.deps import get_current_miniprogram_user
from app.services.user import UserService
from app.utils.response import success, fail, ResponseCode
from app.utils.exceptions import BadRequestException, ServerErrorException

router = APIRouter()


# ============== Request/Response Models ==============

class LoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., description="微信登录 code，从 uni.login() 获取")


class UserInfo(BaseModel):
    """用户信息模型"""
    openid: str = Field(..., description="用户 openid")
    nickname: str = Field(default="", description="用户昵称")
    avatarUrl: str = Field(default="", description="头像URL")
    gender: Optional[int] = Field(default=0, description="性别: 0-未知, 1-男, 2-女")
    city: Optional[str] = Field(default="", description="城市")
    province: Optional[str] = Field(default="", description="省份")
    country: Optional[str] = Field(default="", description="国家")


class LoginResponse(BaseModel):
    """登录响应模型（兼容小程序端）"""
    success: bool = True
    token: str = Field(..., description="JWT token")
    userInfo: UserInfo = Field(..., description="用户信息")


# ============== Helper Functions ==============

async def get_wechat_openid(code: str) -> tuple[str, Optional[str]]:
    """
    调用微信 API 获取 openid 和 session_key
    
    Args:
        code: 微信登录 code
    
    Returns:
        (openid, unionid) 元组
    
    Raises:
        BadRequestException: 微信 API 调用失败
    """
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        # 开发环境：使用 Mock 数据
        import hashlib
        code_hash = hashlib.md5(code.encode()).hexdigest()[:16]
        mock_openid = f"o_mock_{code_hash}"
        return mock_openid, None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                    "js_code": code,
                    "grant_type": "authorization_code"
                }
            )
            
            data = response.json()
            
            # 检查错误
            if "errcode" in data:
                errcode = data.get("errcode")
                errmsg = data.get("errmsg", "未知错误")
                raise BadRequestException(f"微信登录失败: {errmsg} (错误码: {errcode})")
            
            openid = data.get("openid")
            unionid = data.get("unionid")
            session_key = data.get("session_key")
            
            if not openid:
                raise BadRequestException("微信登录失败: 未获取到 openid")
            
            return openid, unionid
            
    except httpx.TimeoutException:
        raise ServerErrorException("微信 API 请求超时，请稍后重试")
    except Exception as e:
        if isinstance(e, (BadRequestException, ServerErrorException)):
            raise
        raise ServerErrorException(f"微信登录失败: {str(e)}")


def generate_username() -> str:
    """生成随机用户名"""
    random_str = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"user_{random_str}"


# ============== API Endpoints ==============

@router.post("/login", response_model=LoginResponse)
async def miniprogram_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    微信小程序登录
    
    接收微信 code，调用微信 API 获取 openid，创建或获取用户，返回 JWT token
    
    - **code**: 微信登录 code，从小程序端 uni.login() 获取
    """
    try:
        # 1. 调用微信 API 获取 openid
        openid, unionid = await get_wechat_openid(request.code)
        
        # 2. 查找或创建用户
        user_service = UserService(db)
        
        # 先通过 openid 查找用户
        user = await user_service.get_user_by_openid(openid)
        
        if not user:
            # 创建新用户
            username = generate_username()
            
            # 检查用户名是否已存在（理论上不太可能，但确保唯一性）
            while await user_service.get_user_by_username(username):
                username = generate_username()
            
            user_data = {
                "username": username,
                "openid": openid,
                "unionid": unionid,
                "nickname": "微信用户",
                "is_active": True,
            }
            
            user = await user_service.create_user_from_dict(user_data)
        
        # 3. 生成 JWT token
        token = create_access_token(data={"sub": str(user.id)})
        
        # 4. 构建用户信息
        user_info = UserInfo(
            openid=user.openid or openid,
            nickname=user.nickname or "微信用户",
            avatarUrl=user.avatar or "",
            gender=0,
            city="",
            province="",
            country="",
        )
        
        return LoginResponse(
            success=True,
            token=token,
            userInfo=user_info
        )
        
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        raise ServerErrorException(f"登录失败: {str(e)}")


@router.get("/user")
async def get_current_user_info(
    current_user: User = Depends(get_current_miniprogram_user)
):
    """
    获取当前用户信息
    
    需要 Authorization header 携带 Bearer token
    """
    user_info = UserInfo(
        openid=current_user.openid or "",
        nickname=current_user.nickname or "微信用户",
        avatarUrl=current_user.avatar or "",
        gender=0,
        city="",
        province="",
        country="",
    )
    
    return success(
        data={
            "success": True,
            "userInfo": user_info.model_dump()
        },
        msg="获取成功"
    )

