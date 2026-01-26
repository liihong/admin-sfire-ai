"""
AdminUser Management Endpoints
管理员用户管理相关接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.admin_user import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserQueryParams,
)
from services.user import AdminUserService
from utils.response import success, page_response, ResponseMsg

router = APIRouter()


@router.get("", summary="获取管理员用户列表")
async def get_admin_users(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=1000, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名"),
    email: Optional[str] = Query(None, description="邮箱"),
    role_id: Optional[int] = Query(None, description="角色ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取管理员用户列表（分页）
    
    支持按用户名、邮箱、角色ID、状态筛选
    """
    admin_user_service = AdminUserService(db)
    
    params = AdminUserQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        username=username,
        email=email,
        role_id=role_id,
        is_active=is_active,
    )
    
    users, total = await admin_user_service.get_users(params)
    
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


@router.get("/{user_id}", summary="获取管理员用户详情")
async def get_admin_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取管理员用户详情"""
    admin_user_service = AdminUserService(db)
    user = await admin_user_service.get_user_by_id(user_id)
    return success(data=user)


@router.post("", summary="创建管理员用户")
async def create_admin_user(
    user_data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新管理员用户"""
    admin_user_service = AdminUserService(db)
    user = await admin_user_service.create_user(user_data)
    return success(data=user, msg=ResponseMsg.CREATED)


@router.put("/{user_id}", summary="更新管理员用户")
async def update_admin_user(
    user_id: int,
    user_data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新管理员用户信息"""
    admin_user_service = AdminUserService(db)
    user = await admin_user_service.update_user(user_id, user_data)
    return success(data=user, msg=ResponseMsg.UPDATED)


@router.delete("/{user_id}", summary="删除管理员用户")
async def delete_admin_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除管理员用户（软删除）"""
    admin_user_service = AdminUserService(db)
    await admin_user_service.delete_user(user_id)
    return success(msg=ResponseMsg.DELETED)


@router.patch("/{user_id}/status", summary="修改管理员用户状态")
async def change_admin_user_status(
    user_id: int,
    status: int = Query(..., ge=0, le=1, description="状态: 0-封禁, 1-正常"),
    db: AsyncSession = Depends(get_db),
):
    """修改管理员用户状态"""
    admin_user_service = AdminUserService(db)
    await admin_user_service.change_status(user_id, status)
    return success(msg=ResponseMsg.UPDATED)

