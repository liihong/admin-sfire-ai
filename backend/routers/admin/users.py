"""
User Management Endpoints
用户管理相关接口
"""
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserQueryParams,
    RechargeRequest,
    DeductRequest,
    ChangeLevelRequest,
)
from services.user import UserService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


@router.get("", summary="获取用户列表")
async def get_users(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名"),
    phone: Optional[str] = Query(None, description="手机号"),
    level: Optional[str] = Query(None, description="用户等级"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    minBalance: Optional[Decimal] = Query(None, description="最小算力余额"),
    maxBalance: Optional[Decimal] = Query(None, description="最大算力余额"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户列表（分页）
    
    支持按用户名、手机号、等级、状态、算力余额筛选
    """
    user_service = UserService(db)
    
    params = UserQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        username=username,
        phone=phone,
        level=level,
        is_active=is_active,
        minBalance=minBalance,
        maxBalance=maxBalance,
    )
    
    users, total = await user_service.get_users(params)
    
    return page_response(
        items=users,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/status/options", summary="获取状态选项")
async def get_status_options():
    """获取用户状态选项"""
    options = [
        {"userLabel": "正常", "userValue": 1},
        {"userLabel": "封禁", "userValue": 0},
    ]
    return success(data=options)


@router.get("/level/options", summary="获取等级选项")
async def get_level_options():
    """获取用户等级选项"""
    options = [
        {"label": "普通用户", "value": 0, "color": "#909399"},
        {"label": "会员", "value": 1, "color": "#E6A23C"},
        {"label": "合伙人", "value": 2, "color": "#F56C6C"},
    ]
    return success(data=options)


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取用户详情"""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    return success(data=user)


@router.post("", summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新用户"""
    user_service = UserService(db)
    user = await user_service.create_user(user_data)
    return success(data=user, msg=ResponseMsg.CREATED)


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息"""
    user_service = UserService(db)
    user = await user_service.update_user(user_id, user_data)
    return success(data=user, msg=ResponseMsg.UPDATED)


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除用户（软删除）"""
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return success(msg=ResponseMsg.DELETED)


@router.patch("/{user_id}/status", summary="修改用户状态")
async def change_user_status(
    user_id: int,
    status: int = Query(..., ge=0, le=1, description="状态: 0-封禁, 1-正常"),
    db: AsyncSession = Depends(get_db),
):
    """修改用户状态"""
    user_service = UserService(db)
    await user_service.change_status(user_id, status)
    return success(msg=ResponseMsg.UPDATED)


@router.post("/recharge", summary="用户充值")
async def recharge_user(
    request: RechargeRequest,
    db: AsyncSession = Depends(get_db),
):
    """为用户充值算力"""
    user_service = UserService(db)
    await user_service.recharge(
        user_id=int(request.userId),
        amount=request.amount,
        remark=request.remark,
    )
    return success(msg="充值成功")


@router.post("/deduct", summary="用户扣费")
async def deduct_user(
    request: DeductRequest,
    db: AsyncSession = Depends(get_db),
):
    """扣除用户算力"""
    user_service = UserService(db)
    await user_service.deduct(
        user_id=int(request.userId),
        amount=request.amount,
        reason=request.reason,
    )
    return success(msg="扣费成功")


@router.post("/change-level", summary="修改用户等级")
async def change_user_level(
    request: ChangeLevelRequest,
    db: AsyncSession = Depends(get_db),
):
    """修改用户等级"""
    user_service = UserService(db)
    await user_service.change_level(
        user_id=int(request.userId),
        level=request.level,
        remark=request.remark,
    )
    return success(msg="等级修改成功")


@router.post("/{user_id}/reset-password", summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    重置用户密码为默认密码 123456

    密码处理流程:
    1. 明文密码 "123456" → MD5加密 → "e10adc3949ba59abbe56e057f20f883e"
    2. MD5密码 → bcrypt哈希 → 存储到数据库

    用户可以使用新密码 123456 登录
    """
    user_service = UserService(db)
    await user_service.reset_password(user_id)
    return success(msg="密码重置成功，新密码为：123456")

