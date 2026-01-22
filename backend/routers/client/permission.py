"""
客户端权限接口
提供用户权限快照查询
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from services.system.permission import PermissionService
from schemas.permission import UserPermissionResponse
from utils.response import success

router = APIRouter()


@router.get("", summary="获取当前用户权限快照")
async def get_user_permission(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户权限快照
    
    返回用户的所有权限配置，包括：
    - IP数量限制
    - AI能量限制
    - 高级功能权限
    - VIP状态
    """
    permission_service = PermissionService(db)
    permission = await permission_service.get_user_permission(current_user.id)
    
    return success(
        data=UserPermissionResponse(**permission),
        msg="获取成功"
    )

