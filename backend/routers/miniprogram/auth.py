"""
MiniProgram Authentication Endpoints
微信小程序认证接口
"""
import secrets
import string
import httpx
import json
import base64
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from db import get_db
from db.redis import RedisCache
from models.user import User
from core.security import create_access_token, verify_password
from core.config import settings
from core.deps import get_current_miniprogram_user
from services.user import UserService
from utils.response import success, fail, ResponseCode
from utils.exceptions import BadRequestException, ServerErrorException

router = APIRouter()


# ============== Request/Response Models ==============

class LoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str = Field(..., description="微信登录 code，从 uni.login() 获取")
    phone_code: Optional[str] = Field(default=None, description="手机号授权 code，从 getPhoneNumber 获取")


class AccountLoginRequest(BaseModel):
    """账号密码登录请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


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


# ============== API Endpoints ==============

@router.post("/account/login")
async def account_login(
    request: AccountLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    手机号+密码登录
    
    接收手机号和密码，验证后返回 JWT token
    """
    try:
        # 1. 通过手机号查找用户
        user_service = UserService(db)
        user = await user_service.get_user_by_phone(request.phone)
        
        if not user:
            raise BadRequestException("手机号或密码错误")
        
        # 2. 验证密码
        if not user.password_hash:
            raise BadRequestException("该账号未设置密码，请使用微信扫码登录")
        
        if not verify_password(request.password, user.password_hash):
            raise BadRequestException("手机号或密码错误")
        
        # 3. 检查用户状态
        if not user.is_active:
            raise BadRequestException("账号已被禁用，请联系管理员")
        
        # 4. 生成 JWT token
        token = create_access_token(data={"sub": str(user.id)})
        
        # 5. 构建用户信息
        user_info = UserInfo(
            openid=user.openid or "",
            nickname=user.nickname or "用户",
            avatarUrl=user.avatar or "",
            gender=0,
            city="",
            province="",
            country="",
        )
        
        return success(
            data={
                "success": True,
                "token": token,
                "userInfo": user_info.model_dump()
            },
            msg="登录成功"
        )
        
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        logger.error(f"账号登录失败: {str(e)}", exc_info=True)
        raise ServerErrorException(f"登录失败: {str(e)}")


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
                "phone": phone_number,  # 保存手机号
                "is_active": True,
            }
            logger.info(f"Creating new user with phone: {phone_number}, openid: {openid}")
            
            user = await user_service.create_user_from_dict(user_data)
            logger.info(f"User created: id={user.id}, phone={user.phone}, openid={user.openid}")
            is_new_user = True
        else:
            # 用户已存在，如果获取到手机号且用户没有手机号，则更新
            logger.info(f"User exists: id={user.id}, current phone={user.phone}, new phone={phone_number}")
            if phone_number and not user.phone:
                logger.info(f"Updating user phone from {user.phone} to {phone_number}")
                user.phone = phone_number
                await db.commit()
                await db.refresh(user)
                logger.info(f"User phone updated successfully: {user.phone}")
            elif phone_number and user.phone:
                logger.info(f"User already has phone number, skipping update")
            elif not phone_number:
                logger.warning(f"No phone number obtained, cannot update")
        
        # 4. 生成 JWT token
        token = create_access_token(data={"sub": str(user.id)})
        
        # 5. 构建用户信息
        user_info = UserInfo(
            openid=user.openid or openid,
            nickname=user.nickname or "微信用户",
            avatarUrl=user.avatar or "",
            gender=0,
            city="",
            province="",
            country="",
        )
        
        # 返回统一格式的响应，兼容前端期望的格式
        return success(
            data={
                "success": True,
                "token": token,
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


class UserDetailInfo(BaseModel):
    """用户详细信息模型（我的页面使用）"""
    phone: Optional[str] = Field(default="", description="手机号")
    avatar: Optional[str] = Field(default="", description="头像URL")
    nickname: Optional[str] = Field(default="", description="昵称")
    power: str = Field(default="0", description="算力余额")
    partnerBalance: str = Field(default="0.00", description="合伙人资产余额")
    partnerStatus: str = Field(default="普通用户", description="合伙人状态")
    expireDate: Optional[str] = Field(default=None, description="会员到期时间 YYYY-MM-DD")


@router.get("/user/info")
async def get_user_detail_info(
    current_user: User = Depends(get_current_miniprogram_user)
):
    """
    获取用户详细信息（我的页面使用）
    
    需要 Authorization header 携带 Bearer token
    返回字段：phone、avatar、nickname、power（算力余额）、partnerBalance（合伙人资产余额）、partnerStatus（合伙人状态）、expireDate（会员到期时间）
    """
    from models.user import UserLevel
    from decimal import Decimal
    
    # 合伙人状态映射
    level_status_map = {
        UserLevel.NORMAL: "普通用户",
        UserLevel.MEMBER: "VIP会员",
        UserLevel.PARTNER: "合伙人",
    }
    partner_status = level_status_map.get(current_user.level, "普通用户")
    
    # 格式化算力余额
    power = str(int(current_user.balance)) if current_user.balance else "0"
    
    # 格式化合伙人资产余额
    partner_balance = current_user.partner_balance if current_user.partner_balance else Decimal("0.0000")
    partner_balance_str = f"{float(partner_balance):.2f}"
    
    # 格式化会员到期时间
    expire_date = None
    if current_user.vip_expire_date:
        expire_date = current_user.vip_expire_date.strftime("%Y-%m-%d")
    
    user_detail = UserDetailInfo(
        phone=current_user.phone or "",
        avatar=current_user.avatar or "",
        nickname=current_user.nickname or "微信用户",
        power=power,
        partnerBalance=partner_balance_str,
        partnerStatus=partner_status,
        expireDate=expire_date,
    )
    
    return success(
        data=user_detail.model_dump(),
        msg="获取成功"
    )


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
    await db.refresh(current_user)
    
    # 构建响应
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
        msg="更新成功"
    )


# ============== 小程序码登录相关接口 ==============

class QrcodeGenerateResponse(BaseModel):
    """生成小程序码响应"""
    scene_str: str = Field(..., description="场景值")
    qrcode_url: str = Field(..., description="小程序码图片的base64数据URL")


class QrcodeLoginRequest(BaseModel):
    """小程序码登录请求（小程序端调用）"""
    code: str = Field(..., description="微信登录 code，从 uni.login() 获取")
    scene: str = Field(..., description="场景值（scene_str）")


class QrcodeLoginResponse(BaseModel):
    """小程序码登录响应"""
    success: bool = True
    message: str = Field(default="登录成功", description="提示信息")


class QrcodeStatusResponse(BaseModel):
    """检查登录状态响应"""
    status: str = Field(..., description="状态: waiting-等待授权, authorized-已授权, expired-已过期")
    token: Optional[str] = Field(default=None, description="JWT token（仅当status为authorized时返回）")
    userInfo: Optional[UserInfo] = Field(default=None, description="用户信息（仅当status为authorized时返回）")


@router.post("/qrcode/generate")
async def generate_qrcode():
    """
    生成小程序码用于PC端登录
    
    生成唯一的小程序码，用户扫码后跳转到小程序完成授权登录
    """
    try:
        # 1. 生成场景值
        scene_str = generate_scene_str()
        
        # 2. 生成小程序码
        # 注意：微信小程序码API的page参数：
        # - 如果为空字符串，则使用小程序首页
        # - 页面路径必须在app.json的pages数组中注册
        # - 页面路径不能以"/"开头
        # 暂时使用空字符串（首页），后续可以创建专门的扫码登录页面
        qrcode_bytes = await generate_miniprogram_qrcode(
            scene=scene_str,
            page=""  # 使用空字符串指向小程序首页
        )
        
        # 3. 将图片转换为base64数据URL
        qrcode_base64 = base64.b64encode(qrcode_bytes).decode('utf-8')
        qrcode_url = f"data:image/png;base64,{qrcode_base64}"
        
        # 4. 将场景值存储到Redis，状态为 waiting
        redis_key = f"mp:login:scene:{scene_str}"
        await RedisCache.set(redis_key, json.dumps({"status": "waiting"}), expire=300)  # 5分钟过期
        
        logger.info(f"Generated QR code with scene: {scene_str}")
        
        # 使用 success() 函数包装响应，确保与前端 axios 拦截器兼容
        return success(
            data={
                "scene_str": scene_str,
                "qrcode_url": qrcode_url
            },
            msg="生成成功"
        )
        
    except Exception as e:
        logger.error(f"生成小程序码失败: {str(e)}", exc_info=True)
        raise ServerErrorException(f"生成小程序码失败: {str(e)}")


@router.post("/qrcode/login", response_model=QrcodeLoginResponse)
async def qrcode_login(
    request: QrcodeLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    小程序端扫码登录接口
    
    小程序端调用此接口完成登录，将登录状态存储到Redis，PC端通过轮询获取
    """
    try:
        # 1. 调用微信 API 获取 openid 和 unionid
        openid, unionid = await get_wechat_openid(request.code)
        
        # 2. 查找或创建用户
        user_service = UserService(db)
        
        # 优先通过 unionid 查找用户（跨平台识别）
        user = None
        if unionid:
            user = await user_service.get_user_by_unionid(unionid)
        
        # 如果没有 unionid 或通过 unionid 没找到，通过 openid 查找
        if not user:
            user = await user_service.get_user_by_openid(openid)
        
        # 如果用户不存在，自动创建新用户
        if not user:
            username = generate_username()
            while await user_service.get_user_by_username(username):
                username = generate_username()
            
            user_data = {
                "username": username,
                "openid": openid,
                "unionid": unionid,
                "nickname": "微信用户",
                "is_active": True,
            }
            logger.info(f"Creating new user for QR code login: openid={openid}, unionid={unionid}")
            user = await user_service.create_user_from_dict(user_data)
            await db.commit()
            await db.refresh(user)
            logger.info(f"User created: id={user.id}, openid={user.openid}")
        else:
            logger.info(f"User exists for QR code login: id={user.id}, openid={user.openid}")
        
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
        
        # 5. 将登录状态和token存储到Redis
        redis_key = f"mp:login:scene:{request.scene}"
        login_data = {
            "status": "authorized",
            "token": token,
            "userInfo": user_info.model_dump()
        }
        await RedisCache.set(redis_key, json.dumps(login_data), expire=300)  # 5分钟过期
        
        logger.info(f"QR code login successful: scene={request.scene}, user_id={user.id}")
        
        return QrcodeLoginResponse(
            success=True,
            message="登录成功"
        )
        
    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        logger.error(f"小程序码登录失败: {str(e)}", exc_info=True)
        raise ServerErrorException(f"登录失败: {str(e)}")


@router.get("/qrcode/status", response_model=QrcodeStatusResponse)
async def check_qrcode_status(
    scene_str: str = Query(..., description="场景值")
):
    """
    检查小程序码登录状态
    
    PC端轮询此接口检查用户是否已完成授权登录
    """
    try:
        redis_key = f"mp:login:scene:{scene_str}"
        data_str = await RedisCache.get(redis_key)
        
        if not data_str:
            # Redis中没有数据，说明已过期或不存在
            return QrcodeStatusResponse(
                status="expired",
                token=None,
                userInfo=None
            )
        
        data = json.loads(data_str)
        status = data.get("status", "waiting")
        
        if status == "authorized":
            # 已授权，返回token和用户信息
            token = data.get("token")
            user_info_dict = data.get("userInfo", {})
            user_info = UserInfo(**user_info_dict)
            
            # 清除Redis中的临时数据
            await RedisCache.delete(redis_key)
            
            return QrcodeStatusResponse(
                status="authorized",
                token=token,
                userInfo=user_info
            )
        else:
            # 等待授权
            return QrcodeStatusResponse(
                status="waiting",
                token=None,
                userInfo=None
            )
        
    except json.JSONDecodeError:
        logger.error(f"解析Redis数据失败: scene_str={scene_str}")
        return QrcodeStatusResponse(
            status="expired",
            token=None,
            userInfo=None
        )
    except Exception as e:
        logger.error(f"检查登录状态失败: {str(e)}", exc_info=True)
        raise ServerErrorException(f"检查登录状态失败: {str(e)}")
