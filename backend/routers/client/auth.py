"""
Client Authentication Endpoints
C端认证接口（小程序）
仅保留与小程序相关的登录与用户信息接口，PC端能力已拆分到 web_auth.py
"""
import secrets
import string
import httpx
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from pydantic import BaseModel, Field
from loguru import logger

from db import get_db
from models.user import User
from core.security import create_access_token, create_refresh_token, decode_token
from core.config import settings
from core.deps import get_current_miniprogram_user
from services.user import UserService
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException

router = APIRouter()


# ============== Request/Response Models ==============

class LoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., description="微信登录 code，从 uni.login() 获取")
    phone_code: Optional[str] = Field(default=None, description="手机号授权 code，从 getPhoneNumber 获取")


class UserLevelInfo(BaseModel):
    """用户等级信息模型"""
    code: str = Field(..., description="等级代码：normal/vip/svip/max")
    name: str = Field(..., description="等级名称（中文显示）")
    max_ip_count: Optional[int] = Field(default=None, description="最大IP数量（NULL表示不限制）")
    ip_type: str = Field(default="permanent", description="IP类型：temporary/permanent")
    daily_tokens_limit: Optional[int] = Field(default=None, description="每日AI能量限制（NULL表示无限制）")
    can_use_advanced_agent: bool = Field(default=False, description="是否可使用高级智能体")
    unlimited_conversations: bool = Field(default=False, description="是否无限制对话")


class UserInfo(BaseModel):
    """用户信息模型（完整信息）"""
    openid: str = Field(..., description="用户 openid")
    nickname: str = Field(default="", description="用户昵称")
    avatar: str = Field(default="", description="头像URL")
    phone: Optional[str] = Field(default="", description="手机号")
    gender: Optional[int] = Field(default=0, description="性别: 0-未知, 1-男, 2-女")
    city: Optional[str] = Field(default="", description="城市")
    province: Optional[str] = Field(default="", description="省份")
    country: Optional[str] = Field(default="", description="国家")
    # 等级相关字段
    level: str = Field(default="normal", description="用户等级代码（兼容旧字段）")
    level_code: Optional[str] = Field(default=None, description="用户等级代码：normal/vip/svip/max")
    level_name: str = Field(default="普通用户", description="等级名称（中文显示）")
    level_info: Optional[UserLevelInfo] = Field(default=None, description="等级详细信息")
    levelInfo: Optional[UserLevelInfo] = Field(default=None, description="等级详细信息（兼容字段，与level_info相同）")
    # 余额相关字段
    power: str = Field(default="0", description="算力可用余额（总余额-冻结余额）")
    total_balance: str = Field(default="0", description="算力总余额")
    frozen_balance: str = Field(default="0", description="冻结算力余额")
    partner_balance: str = Field(default="0.00", description="合伙人资产余额")
    partnerBalance: Optional[str] = Field(default=None, description="合伙人资产余额（兼容字段，与partner_balance相同）")
    # 状态相关字段
    partner_status: str = Field(default="普通用户", description="合伙人状态：普通用户/VIP会员/合伙人")
    partnerStatus: Optional[str] = Field(default=None, description="合伙人状态（兼容字段，与partner_status相同）")
    vip_expire_date: Optional[str] = Field(default=None, description="会员到期时间 YYYY-MM-DD")
    expireDate: Optional[str] = Field(default=None, description="会员到期时间（兼容字段，与vip_expire_date相同）")


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
        logger.warning("WECHAT_APP_ID or WECHAT_APP_SECRET not configured, using mock openid")
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


async def get_wechat_phone_number(phone_code: str) -> Optional[str]:
    """
    调用微信 API 获取手机号
    
    Args:
        phone_code: 手机号授权 code，从 getPhoneNumber 获取
    
    Returns:
        手机号字符串，如果获取失败返回 None
    
    Note:
        需要先获取 access_token，然后调用 getuserphonenumber API
        在开发环境中，如果没有配置微信APP信息，返回None
    """
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        # 开发环境：不处理手机号
        logger.warning("WECHAT_APP_ID or WECHAT_APP_SECRET not configured, cannot get phone number")
        return None
    
    try:
        # 1. 获取 access_token
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取 access_token
            token_response = await client.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET
                }
            )
            token_data = token_response.json()
            
            if "errcode" in token_data:
                # 获取 access_token 失败
                return None
            
            access_token = token_data.get("access_token")
            if not access_token:
                return None
            
            # 2. 使用 access_token 和 phone_code 获取手机号
            phone_response = await client.post(
                "https://api.weixin.qq.com/wxa/business/getuserphonenumber",
                params={"access_token": access_token},
                json={"code": phone_code}
            )
            
            phone_data = phone_response.json()
            logger.info(f"WeChat phone API response: {phone_data}")
            
            if phone_data.get("errcode") == 0:
                phone_info = phone_data.get("phone_info", {})
                phone_number = phone_info.get("phoneNumber")
                logger.info(f"Successfully got phone number: {phone_number}")
                return phone_number
            else:
                errcode = phone_data.get("errcode")
                errmsg = phone_data.get("errmsg", "未知错误")
                logger.error(f"Failed to get phone number: errcode={errcode}, errmsg={errmsg}")
            
            return None
            
    except Exception as e:
        # 获取手机号失败，不影响登录流程
        logger.error(f"Exception while getting phone number: {str(e)}", exc_info=True)
        return None


def generate_username() -> str:
    """生成随机用户名"""
    random_str = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"user_{random_str}"


def generate_scene_str() -> str:
    """生成场景值（用于小程序码）"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))


async def get_wechat_access_token() -> str:
    """
    获取微信小程序 access_token
    
    Returns:
        access_token 字符串
    
    Raises:
        ServerErrorException: 获取 access_token 失败
    """
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        raise ServerErrorException("微信小程序配置未设置")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET
                }
            )
            
            data = response.json()
            
            if "errcode" in data:
                errcode = data.get("errcode")
                errmsg = data.get("errmsg", "未知错误")
                raise ServerErrorException(f"获取 access_token 失败: {errmsg} (错误码: {errcode})")
            
            access_token = data.get("access_token")
            if not access_token:
                raise ServerErrorException("获取 access_token 失败: 未返回 token")
            
            return access_token
            
    except httpx.TimeoutException:
        raise ServerErrorException("微信 API 请求超时，请稍后重试")
    except Exception as e:
        if isinstance(e, ServerErrorException):
            raise
        raise ServerErrorException(f"获取 access_token 失败: {str(e)}")


async def generate_miniprogram_qrcode(scene: str, page: str = "") -> bytes:
    """
    生成小程序码
    
    Args:
        scene: 场景值（最大32个字符）
        page: 小程序页面路径，默认为空字符串（使用首页）
    
    Returns:
        小程序码图片的字节数据
    
    Raises:
        ServerErrorException: 生成小程序码失败
    """
    access_token = await get_wechat_access_token()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.weixin.qq.com/wxa/getwxacodeunlimit",
                params={"access_token": access_token},
                json={
                    "scene": scene,
                    "page": page,
                    "width": 280,
                    "auto_color": False,
                    "line_color": {"r": 0, "g": 0, "b": 0},
                    "is_hyaline": False
                }
            )
            
            # 检查是否是错误响应（JSON格式）
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                data = response.json()
                if "errcode" in data:
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    raise ServerErrorException(f"生成小程序码失败: {errmsg} (错误码: {errcode})")
            
            # 返回图片字节数据
            return response.content
            
    except httpx.TimeoutException:
        raise ServerErrorException("微信 API 请求超时，请稍后重试")
    except Exception as e:
        if isinstance(e, ServerErrorException):
            raise
        raise ServerErrorException(f"生成小程序码失败: {str(e)}")


# ============== Helper Functions for User Info ==============

def build_user_info(user: User) -> UserInfo:
    """
    构建用户信息对象（包含完整的等级信息）
    
    Args:
        user: User对象（需要已加载user_level关系）
    
    Returns:
        UserInfo对象
    """
    from decimal import Decimal
    
    # 获取等级信息
    level_code = user.level_code or "normal"
    level_name = user.level_name
    
    # 合伙人状态映射
    level_status_map = {
        "normal": "普通用户",
        "vip": "VIP会员",
        "svip": "合伙人",
        "max": "合伙人",
    }
    partner_status = level_status_map.get(level_code, "普通用户")
    
    # 构建等级详细信息
    level_info = None
    if user.user_level:
        level_info = UserLevelInfo(
            code=user.user_level.code,
            name=user.user_level.name,
            max_ip_count=user.user_level.max_ip_count,
            ip_type=user.user_level.ip_type,
            daily_tokens_limit=user.user_level.daily_tokens_limit,
            can_use_advanced_agent=user.user_level.can_use_advanced_agent,
            unlimited_conversations=user.user_level.unlimited_conversations,
        )
    
    # 格式化会员到期时间
    vip_expire_date = None
    if user.vip_expire_date:
        vip_expire_date = user.vip_expire_date.strftime("%Y-%m-%d")
    
    # 格式化合伙人资产余额
    partner_balance = user.partner_balance if user.partner_balance else Decimal("0.0000")
    partner_balance_str = f"{float(partner_balance):.2f}"
    
    # 格式化算力余额
    total_balance = user.balance if user.balance else Decimal("0")
    frozen_balance = user.frozen_balance if user.frozen_balance else Decimal("0")
    available_balance = total_balance - frozen_balance  # 可用余额 = 总余额 - 冻结余额
    
    # 转换为字符串格式（整数）
    total_balance_str = str(int(total_balance))
    frozen_balance_str = str(int(frozen_balance))
    power = str(int(available_balance))  # 可用余额
    
    # 获取头像URL
    avatar_url = user.avatar or ""
    
    return UserInfo(
        openid=user.openid or "",
        nickname=user.nickname or "微信用户",
        avatar=avatar_url,
        phone=user.phone or "",
        gender=0,
        city="",
        province="",
        country="",
        level=level_code,  # 兼容旧字段（保留用于前端兼容）
        level_code=level_code,
        level_name=level_name,
        level_info=level_info,
        levelInfo=level_info,  # 兼容字段
        partner_status=partner_status,
        partnerStatus=partner_status,  # 兼容字段
        vip_expire_date=vip_expire_date,
        expireDate=vip_expire_date,  # 兼容字段
        partner_balance=partner_balance_str,
        partnerBalance=partner_balance_str,  # 兼容字段
        power=power,
        total_balance=total_balance_str,
        frozen_balance=frozen_balance_str,
    )


# ============== API Endpoints ==============

@router.post("/login")
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
        
        # 2. 如果提供了 phone_code，获取手机号
        phone_number = None
        if request.phone_code:
            logger.info(f"Received phone_code, attempting to get phone number")
            phone_number = await get_wechat_phone_number(request.phone_code)
            logger.info(f"Phone number result: {phone_number if phone_number else 'None'}")
        
        # 3. 查找或创建用户
        user_service = UserService(db)
        
        # 先通过 openid 查找用户
        user = await user_service.get_user_by_openid(openid)
        is_new_user = False
        
        if not user:
            # 如果通过openid找不到，再通过手机号查找
            if phone_number:
                user = await user_service.get_user_by_phone(phone_number)
                if user:
                    # 如果通过手机号找到了用户，且openid一致（或为空），则更新用户
                    if not user.openid or user.openid == openid:
                        logger.info(f"User found by phone: id={user.id}, updating openid and unionid")
                        user.openid = openid
                        if unionid:
                            user.unionid = unionid
                        # 更新登录状态和时间（通过更新updated_at）
                        user.updated_at = datetime.now()
                        await db.commit()
                        await db.refresh(user)
                        logger.info(f"User updated: id={user.id}, openid={user.openid}, phone={user.phone}")
                        is_new_user = False
                    else:
                        # 手机号已存在但openid不一致，说明是不同用户，创建新用户
                        logger.warning(f"Phone {phone_number} exists but openid mismatch, creating new user")
                        user = None
            
            # 如果都找不到，创建新用户
            if not user:
                username = generate_username()
                
                # 检查用户名是否已存在（理论上不太可能，但确保唯一性）
                while await user_service.get_user_by_username(username):
                    username = generate_username()
                
                user_data = {
                    "username": username,
                    "openid": openid,
                    "unionid": unionid,
                    "nickname": "微信用户",
                    "phone": phone_number,  # 保存手机号
                    "is_active": True,
                }
                logger.info(f"Creating new user with phone: {phone_number}, openid: {openid}")
                
                user = await user_service.create_user_from_dict(user_data)
                logger.info(f"User created: id={user.id}, phone={user.phone}, openid={user.openid}")
                is_new_user = True
        else:
            # 用户已存在（通过openid找到），更新微信数据和登录状态
            logger.info(f"User exists by openid: id={user.id}, current phone={user.phone}, new phone={phone_number}")
            
            # 更新unionid（如果获取到）
            if unionid and user.unionid != unionid:
                user.unionid = unionid
                logger.info(f"Updating unionid: {user.unionid}")
            
            # 如果获取到手机号且用户没有手机号，则更新
            if phone_number and not user.phone:
                logger.info(f"Updating user phone from {user.phone} to {phone_number}")
                user.phone = phone_number
            elif phone_number and user.phone and user.phone != phone_number:
                # 手机号不一致，记录警告但不更新（保持原有手机号）
                logger.warning(f"Phone number mismatch: existing={user.phone}, new={phone_number}, keeping existing")
            
            # 更新登录状态和时间（通过更新updated_at）
            user.updated_at = datetime.now()
            await db.commit()
            await db.refresh(user)
            logger.info(f"User login updated: id={user.id}, phone={user.phone}, openid={user.openid}")
        
        # 4. 重新查询用户并加载等级关系（确保获取最新数据）
        query = select(User).where(
            User.id == user.id,
            User.is_deleted == False
        ).options(selectinload(User.user_level))
        
        result = await db.execute(query)
        user_with_level = result.scalar_one_or_none()
        
        if not user_with_level:
            raise ServerErrorException("用户数据异常")
        
        # 5. 生成 JWT token（包含 access_token 和 refresh_token）
        # 小程序登录使用长期有效的refresh_token（100年有效期，用户不删除小程序则永不过期）
        access_token = create_access_token(data={"sub": str(user_with_level.id)})
        refresh_token = create_refresh_token(data={"sub": str(user_with_level.id)}, long_lived=True)

        # 6. 构建用户信息（包含完整的等级信息）
        user_info = build_user_info(user_with_level)

        # 返回统一格式的响应，兼容前端期望的格式
        return success(
            data={
                "success": True,
                "token": access_token,
                "refreshToken": refresh_token,
                "expiresIn": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 秒数
                "userInfo": user_info.model_dump(),
                "is_new_user": is_new_user
            },
            msg="登录成功"
        )
        
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        raise ServerErrorException(f"登录失败: {str(e)}")


@router.get("/user")
async def get_current_user_info(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户完整信息
    
    需要 Authorization header 携带 Bearer token
    返回用户完整信息，包括：
    - 基础信息：openid、nickname、avatar、phone
    - 等级信息：level、level_code、level_name、level_info、levelInfo
    - 余额信息：power（算力可用余额）、total_balance（算力总余额）、frozen_balance（冻结算力）、partner_balance、partnerBalance
    - 状态信息：partner_status、partnerStatus、vip_expire_date、expireDate
    """
    try:
        # 重新查询用户并加载等级关系（确保获取最新数据）
        query = select(User).where(
            User.id == current_user.id,
            User.is_deleted == False
        ).options(selectinload(User.user_level))
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise BadRequestException("用户不存在")
        
        # 构建用户信息（包含完整的等级信息）
        user_info = build_user_info(user)
        
        return success(
            data={
                "success": True,
                "userInfo": user_info.model_dump()
            },
            msg="获取成功"
        )
    except LookupError as e:
        # 处理无效的枚举值（如数据库中存储了'vip'等无效值）
        logger.error(f"用户等级枚举值无效: {str(e)}, user_id={current_user.id}")
        # 尝试修复：将用户的level_code重置为默认值
        try:
            current_user.level_code = "normal"
            await db.commit()
            await db.refresh(current_user)
            # 重新查询
            query = select(User).where(
                User.id == current_user.id,
                User.is_deleted == False
            ).options(selectinload(User.user_level))
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            if user:
                user_info = build_user_info(user)
                return success(
                    data={
                        "success": True,
                        "userInfo": user_info.model_dump()
                    },
                    msg="获取成功"
                )
        except Exception as fix_error:
            logger.error(f"修复用户等级失败: {str(fix_error)}")
        raise ServerErrorException("用户数据异常，请联系管理员")




class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    nickname: Optional[str] = Field(default=None, description="用户昵称")
    avatar: Optional[str] = Field(default=None, description="头像（Base64 或 URL）")
    gender: Optional[int] = Field(default=None, description="性别: 0-未知, 1-男, 2-女")


@router.put("/user")
async def update_user_info(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息

    需要 Authorization header 携带 Bearer token
    """
    try:
        # 直接更新用户对象属性
        if request.nickname is not None:
            current_user.nickname = request.nickname
        if request.avatar is not None:
            current_user.avatar = request.avatar
        if request.gender is not None:
            # 注意：User模型可能没有gender字段，这里先不处理
            pass

        # 如果没有要更新的字段，返回错误
        update_fields = []
        if request.nickname is not None:
            update_fields.append("nickname")
        if request.avatar is not None:
            update_fields.append("avatar")

        if not update_fields:
            raise BadRequestException("请提供要更新的字段")

        # 提交更改
        await db.commit()
        
        # 重新查询用户并加载等级关系（确保获取最新数据）
        query = select(User).where(
            User.id == current_user.id,
            User.is_deleted == False
        ).options(selectinload(User.user_level))
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise BadRequestException("用户不存在")

        # 构建响应（包含完整的等级信息）
        user_info = build_user_info(user)

        return success(
            data={
                "success": True,
                "userInfo": user_info.model_dump()
            },
            msg="更新成功"
        )
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}, user_id={current_user.id}", exc_info=True)
        raise ServerErrorException(f"更新用户信息失败: {str(e)}")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码（MD5加密）")
    new_password: str = Field(..., description="新密码（MD5加密）")


@router.post("/user/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码

    流程:
    1. 验证原密码是否正确（前端已MD5加密，后端验证MD5密码与bcrypt哈希）
    2. 验证新密码格式
    3. 更新密码（将MD5密码转为bcrypt哈希存储）

    需要 Authorization header 携带 Bearer token
    """
    from core.security import get_password_hash, verify_password

    # 1. 检查用户是否已设置密码
    if not current_user.password_hash:
        raise BadRequestException("该账号未设置密码，无法修改密码")

    # 2. 验证原密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise BadRequestException("原密码错误")

    # 3. 检查新密码是否与原密码相同
    if request.old_password == request.new_password:
        raise BadRequestException("新密码不能与原密码相同")

    # 4. 从数据库重新获取用户对象(确保在当前会话中)
    from sqlalchemy import select
    stmt = select(User).where(User.id == current_user.id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise BadRequestException("用户不存在")

    # 5. 更新密码（将MD5密码转为bcrypt哈希存储）
    user.password_hash = get_password_hash(request.new_password)

    # 6. 提交更改
    await db.commit()

    logger.info(f"用户 {user.phone or user.id} 修改密码成功")

    return success(
        data={"success": True},
        msg="密码修改成功"
    )


# ============== Token Refresh ==============

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refreshToken: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    token: str = Field(..., description="新的访问令牌")
    refreshToken: str = Field(..., description="新的刷新令牌")
    expiresIn: int = Field(..., description="访问令牌过期时间（秒）")


@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    使用刷新令牌获取新的访问令牌

    - **refreshToken**: 刷新令牌（7天有效）

    流程:
    1. 验证refresh_token是否有效
    2. 提取用户ID并查询用户
    3. 生成新的access_token和refresh_token
    4. 返回新token
    """
    try:
        # 1. 解码并验证refresh_token
        payload = decode_token(request.refreshToken)
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

        # 4. 查询用户（直接查询 User 对象，不使用 get_user_by_id 因为返回的是字典）
        from sqlalchemy import select
        from models.user import User
        
        result = await db.execute(
            select(User).where(
                User.id == int(user_id),
                User.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise BadRequestException("用户不存在")

        if not user.is_active:
            raise BadRequestException("用户已被封禁")

        # 5. 生成新的access_token和refresh_token
        # 小程序刷新时也使用长期有效的refresh_token（100年有效期）
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)}, long_lived=True)

        logger.info(f"Token refreshed successfully for user: {user.id}")

        return success(
            data={
                "token": new_access_token,
                "refreshToken": new_refresh_token,
                "expiresIn": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            },
            msg="令牌刷新成功"
        )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
        raise ServerErrorException(f"令牌刷新失败: {str(e)}")

