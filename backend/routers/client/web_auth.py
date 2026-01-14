"""
PC Web Authentication Endpoints
PC官网认证接口（扫码登录、账号密码登录）
将与小程序无关的登录能力独立出来，避免与小程序授权逻辑混淆
"""
import json
import base64
import hashlib
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from db import get_db
from db.redis import RedisCache
from core.security import create_access_token, verify_password
from services.user import UserService
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException

# 复用小程序认证模块的能力，避免重复实现
from .auth import (
    UserInfo,
    get_wechat_openid,
    generate_username,
    generate_scene_str,
    generate_miniprogram_qrcode,
)

router = APIRouter()


# ============== Request/Response Models ==============

class AccountLoginRequest(BaseModel):
    """账号密码登录请求（PC端）"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


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


# ============== PC端认证接口 ==============

@router.post("/account/login")
async def account_login(
    request: AccountLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    PC端手机号+密码登录(C端用户)

    登录流程:
    1. 密码在前端使用MD5加密后传输
    2. 后端验证MD5密码与bcrypt哈希
    3. 检查账号是否激活(is_active)
    4. 检查会员是否过期(vip_expire_date)
    5. 返回token和用户信息(包含updated_at)
    """
    try:
        # 1. 通过手机号查找用户
        user_service = UserService(db)
        user = await user_service.get_user_by_phone(request.phone)

        if not user:
            raise BadRequestException("手机号或密码错误")

        # 2. 检查用户是否激活
        if not user.is_active:
            raise BadRequestException("账号已被封禁，请联系管理员")

        # 3. 验证密码(前端已MD5加密，后端验证MD5密码与bcrypt哈希)
        if not user.password_hash:
            raise BadRequestException("该账号未设置密码，请使用微信扫码登录")

        # 将前端传来的MD5密码与数据库中的bcrypt哈希进行验证
        if not verify_password(request.password, user.password_hash):
            raise BadRequestException("手机号或密码错误")

        # 4. 检查会员是否过期
        if user.vip_expire_date:
            now = datetime.now()
            if user.vip_expire_date < now:
                logger.warning(f"用户 {user.phone} 会员已过期: {user.vip_expire_date}")
                # 会员已过期，可以允许登录但需要提示续费
                # 这里我们选择在响应中添加提示信息
                pass

        # 5. 生成 JWT token
        token = create_access_token(data={"sub": str(user.id)})

        # 6. 构建用户信息
        user_info = UserInfo(
            openid=user.openid or "",
            nickname=user.nickname or "用户",
            avatarUrl=user.avatar or "",
            gender=0,
            city="",
            province="",
            country="",
        )

        # 7. 构建响应数据
        response_data = {
            "success": True,
            "token": token,
            "userInfo": user_info.model_dump(),
        }

        # 添加 updated_at 字段
        if user.updated_at:
            response_data["updated_at"] = user.updated_at.strftime("%Y-%m-%d %H:%M:%S")

        # 添加会员过期提示
        if user.vip_expire_date:
            now = datetime.now()
            if user.vip_expire_date < now:
                response_data["vip_expired"] = True
                response_data["vip_expire_date"] = user.vip_expire_date.strftime("%Y-%m-%d")
            else:
                response_data["vip_expired"] = False
                response_data["vip_expire_date"] = user.vip_expire_date.strftime("%Y-%m-%d")

        return success(
            data=response_data,
            msg="登录成功"
        )

    except (BadRequestException, ServerErrorException):
        raise
    except Exception as e:
        logger.error(f"账号登录失败: {str(e)}", exc_info=True)
        raise ServerErrorException(f"登录失败: {str(e)}")


@router.post("/qrcode/generate")
async def generate_qrcode():
    """
    生成小程序码用于PC端扫码登录
    """
    try:
        # 1. 生成场景值
        scene_str = generate_scene_str()

        # 2. 生成小程序码
        qrcode_bytes = await generate_miniprogram_qrcode(
            scene=scene_str,
            page=""  # 使用空字符串指向小程序首页
        )

        # 3. 将图片转换为base64数据URL
        qrcode_base64 = base64.b64encode(qrcode_bytes).decode("utf-8")
        qrcode_url = f"data:image/png;base64,{qrcode_base64}"

        # 4. 将场景值存储到Redis，状态为 waiting
        redis_key = f"mp:login:scene:{scene_str}"
        await RedisCache.set(redis_key, json.dumps({"status": "waiting"}), expire=300)  # 5分钟过期

        logger.info(f"Generated QR code with scene: {scene_str}")

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
    小程序端扫码登录接口（为PC端提供授权结果）
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
    检查小程序码登录状态（PC端轮询）
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

