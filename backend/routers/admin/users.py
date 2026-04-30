"""
User Management Endpoints
用户管理相关接口
"""
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from core.deps import get_current_admin_user
from core.tenant_helpers import resolve_admin_agent_scope_tenant_id
from core.tenant_constants import effective_tenant_id
from models.admin_user import AdminUser
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
    pageSize: int = Query(10, ge=1, le=1000, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名"),
    phone: Optional[str] = Query(None, description="手机号"),
    level: Optional[str] = Query(None, description="用户等级"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    minBalance: Optional[Decimal] = Query(None, description="最小算力余额"),
    maxBalance: Optional[Decimal] = Query(None, description="最大算力余额"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    获取用户列表（分页）
    
    支持按用户名、手机号、等级、状态、算力余额筛选
    """
    user_service = UserService(db)

    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )

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
    
    users, total = await user_service.get_users(params, scoped_tenant_id=scope_tid)
    
    return page_response(
        items=users,
        total=total,
        page_num=pageNum,
        page_size=pageSize,
    )


@router.get("/options", summary="获取用户选项（状态和等级）")
async def get_user_options(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取用户相关的所有选项（状态和等级）"""
    from services.system.user_level import UserLevelService

    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )

    # 获取用户等级选项（从数据库查询）
    user_level_service = UserLevelService(db)
    levels = await user_level_service.get_all_enabled_levels(
        tenant_id=effective_tenant_id(scope_tid)
    )
    
    # 转换为前端需要的格式
    level_options = [
        {
            "label": level.name,
            "value": level.code,
            "code": level.code,
            "color": "#909399" if level.code == "normal" else "#E6A23C" if level.code == "vip" else "#F56C6C"
        }
        for level in levels
    ]
    
    # 状态选项（固定值）
    status_options = [
        {"userLabel": "正常", "userValue": 1},
        {"userLabel": "封禁", "userValue": 0},
    ]
    
    return success(data={
        "levels": level_options,
        "status": status_options
    })


@router.get("/statistics/unionid", summary="获取用户 unionid 统计信息")
async def get_unionid_statistics(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取用户 unionid 统计（租户管理员仅限本租户）。"""
    from sqlalchemy import select, func, and_
    from models.user import User

    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )

    base_conditions = [User.is_deleted == False]
    if scope_tid is not None:
        base_conditions.append(User.tenant_id == scope_tid)
    base_where = and_(*base_conditions)

    total_query = select(func.count(User.id)).where(base_where)
    total_result = await db.execute(total_query)
    total_users = total_result.scalar() or 0

    with_unionid_query = select(func.count(User.id)).where(
        User.unionid.isnot(None),
        base_where,
    )
    with_unionid_count = (await db.execute(with_unionid_query)).scalar() or 0

    openid_no_unionid_query = select(func.count(User.id)).where(
        User.openid.isnot(None),
        User.unionid.is_(None),
        base_where,
    )
    openid_no_unionid_count = (await db.execute(openid_no_unionid_query)).scalar() or 0

    phone_no_unionid_query = select(func.count(User.id)).where(
        User.phone.isnot(None),
        User.unionid.is_(None),
        base_where,
    )
    phone_no_unionid_count = (await db.execute(phone_no_unionid_query)).scalar() or 0

    return success(data={
        "total_users": total_users,
        "with_unionid": with_unionid_count,
        "without_unionid": total_users - with_unionid_count,
        "openid_no_unionid": openid_no_unionid_count,
        "phone_no_unionid": phone_no_unionid_count,
        "note": "unionid 会在用户重新登录小程序时自动更新",
    })


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """获取用户详情"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    user = await user_service.get_user_by_id(
        int(user_id),
        scoped_tenant_id=scope_tid,
    )
    return success(data=user)


@router.post("", summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """创建新用户"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    user = await user_service.create_user(
        user_data,
        scoped_tenant_id=scope_tid,
    )
    return success(data=user, msg=ResponseMsg.CREATED)


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """更新用户信息"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    user = await user_service.update_user(
        user_id,
        user_data,
        scoped_tenant_id=scope_tid,
    )
    return success(data=user, msg=ResponseMsg.UPDATED)


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """删除用户（软删除）"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    await user_service.delete_user(user_id, scoped_tenant_id=scope_tid)
    return success(msg=ResponseMsg.DELETED)


@router.patch("/{user_id}/status", summary="修改用户状态")
async def change_user_status(
    user_id: int,
    status: int = Query(..., ge=0, le=1, description="状态: 0-封禁, 1-正常"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """修改用户状态"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    await user_service.change_status(
        user_id,
        status,
        scoped_tenant_id=scope_tid,
    )
    return success(msg=ResponseMsg.UPDATED)


@router.post("/recharge", summary="用户充值")
async def recharge_user(
    request: RechargeRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """为用户充值算力"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    await user_service.recharge(
        user_id=int(request.userId),
        amount=request.amount,
        remark=request.remark,
        operator_id=current_admin.id,
        scoped_tenant_id=scope_tid,
    )
    return success(msg="充值成功")


@router.post("/deduct", summary="用户扣费")
async def deduct_user(
    request: DeductRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """扣除用户算力"""
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    await user_service.deduct(
        user_id=int(request.userId),
        amount=request.amount,
        reason=request.reason,
        scoped_tenant_id=scope_tid,
    )
    return success(msg="扣费成功")


@router.post("/change-level", summary="修改用户等级")
async def change_user_level(
    request: ChangeLevelRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """修改用户等级"""
    from datetime import datetime
    
    user_service = UserService(db)

    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )

    # 解析VIP到期时间（设置为UTC时区，时间设为23:59:59）
    vip_expire_date = None
    if request.vip_expire_date:
        try:
            from datetime import timezone
            # 解析日期并设置为当天的23:59:59 UTC
            date_obj = datetime.strptime(request.vip_expire_date, "%Y-%m-%d")
            vip_expire_date = datetime.combine(
                date_obj.date(),
                datetime.max.time()
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            from utils.exceptions import BadRequestException
            raise BadRequestException("VIP到期时间格式错误，请使用YYYY-MM-DD格式")
    
    await user_service.change_level(
        user_id=int(request.userId),
        level=request.level,
        vip_expire_date=vip_expire_date,
        remark=request.remark,
        operator_id=current_admin.id,
        scoped_tenant_id=scope_tid,
    )
    return success(msg="等级修改成功")


@router.post("/{user_id}/reset-password", summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    重置用户密码为默认密码 123456

    密码处理流程:
    1. 明文密码 "123456" → MD5加密 → "e10adc3949ba59abbe56e057f20f883e"
    2. MD5密码 → bcrypt哈希 → 存储到数据库

    用户可以使用新密码 123456 登录
    """
    user_service = UserService(db)
    scope_tid = await resolve_admin_agent_scope_tenant_id(
        db,
        admin_tenant_id=current_admin.tenant_id,
        admin_username=current_admin.username,
    )
    await user_service.reset_password(user_id, scoped_tenant_id=scope_tid)
    return success(msg="密码重置成功，新密码为：123456")

