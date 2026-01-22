"""
Role Endpoints
角色管理接口（基于roles表和users表的level字段）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services.system import RoleService
from schemas.role import RoleCreate, RoleUpdate
from utils.response import success, ResponseMsg

router = APIRouter()


@router.get("/list", summary="获取角色列表")
async def get_role_list(
    db: AsyncSession = Depends(get_db),
):
    """
    获取角色列表
    
    返回所有角色及其用户数量统计
    """
    role_service = RoleService(db)
    roles = await role_service.get_roles()
    
    return success(data={
        "list": roles,
        "total": len(roles),
    })


@router.get("/{role_id}", summary="获取角色详情")
async def get_role_detail(
    role_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取角色详情
    
    Args:
        role_id: 角色ID（数据库主键）
    """
    role_service = RoleService(db)
    role = await role_service.get_role_by_id(role_id)
    
    return success(data=role)


@router.post("", summary="创建角色")
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新角色
    
    注意：角色代码（code）必须是normal/member/partner之一，对应UserLevel枚举
    如果角色代码已存在，则更新现有角色
    """
    role_service = RoleService(db)
    role = await role_service.create_role(data)
    await db.commit()
    
    return success(data=role, msg=ResponseMsg.CREATED)


@router.put("/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新角色信息
    
    可以更新角色名称、描述、排序等信息
    注意：不能修改角色代码（code）
    """
    role_service = RoleService(db)
    role = await role_service.update_role(role_id, data)
    await db.commit()
    
    return success(data=role, msg=ResponseMsg.UPDATED)


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    删除角色
    
    删除前会检查是否有用户使用该角色
    如果有用户使用，则不允许删除
    """
    role_service = RoleService(db)
    await role_service.delete_role(role_id)
    await db.commit()
    
    return success(msg=ResponseMsg.DELETED)


@router.get("/{role_id}/permissions", summary="获取角色权限")
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取角色的菜单权限列表
    
    Args:
        role_id: 角色ID
    
    Returns:
        包含菜单ID数组的响应
    """
    role_service = RoleService(db)
    menu_ids = await role_service.get_role_permissions(role_id)
    
    return success(data={
        "role_id": role_id,
        "menu_ids": menu_ids
    })


@router.put("/{role_id}/permissions", summary="设置角色权限")
async def set_role_permissions(
    role_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    设置角色的菜单权限
    
    Args:
        role_id: 角色ID
        data: 包含 menu_ids 字段的字典，menu_ids 为菜单ID数组
    
    Returns:
        操作结果
    """
    menu_ids = data.get("menu_ids", [])
    if not isinstance(menu_ids, list):
        from utils.exceptions import BadRequestException
        raise BadRequestException(msg="menu_ids 必须是数组格式")
    
    role_service = RoleService(db)
    await role_service.set_role_permissions(role_id, menu_ids)
    await db.commit()
    
    return success(msg="权限分配成功")
