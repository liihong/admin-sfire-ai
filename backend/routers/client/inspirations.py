"""
Client Inspiration Endpoints
C端灵感管理接口（小程序 & PC官网）
支持灵感的创建、查询、更新、删除、生成等功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from models.inspiration import Inspiration
from core.deps import get_current_miniprogram_user
from services.inspiration.inspiration_service import InspirationService
from services.inspiration.generate_service import InspirationGenerateService
from services.system.security import SecurityService
from schemas.inspiration import (
    InspirationCreate,
    InspirationUpdate,
    InspirationQueryParams,
    InspirationResponse,
    InspirationGenerateRequest,
    InspirationGenerateResponse,
    InspirationPinRequest,
    InspirationArchiveRequest,
)
from utils.response import success, page_response
from utils.exceptions import BadRequestException, NotFoundException

router = APIRouter()


@router.post("", response_model=dict)
async def create_inspiration(
    data: InspirationCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建灵感
    
    - **content**: 灵感内容（必填，限制500字符）
    - **tags**: 标签列表（可选）
    - **project_id**: 项目ID（可选）
    
    需要内容安全检测
    """
    # 内容安全检测
    security_result = await SecurityService.msg_sec_check(content=data.content)
    if not security_result['pass']:
        raise BadRequestException("内容包含违规信息，请修改后重试")
    
    # 创建灵感
    inspiration_service = InspirationService(db)
    inspiration = await inspiration_service.create_inspiration(
        user_id=current_user.id,
        data=data
    )
    
    # 提交事务以确保数据已保存
    await db.commit()
    
    # 重新加载以获取关联对象（如果需要project信息）
    if inspiration.project_id:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        result = await db.execute(
            select(Inspiration)
            .options(selectinload(Inspiration.project))
            .where(Inspiration.id == inspiration.id)
        )
        inspiration = result.scalar_one()
    
    # 转换为响应格式
    response_data = InspirationResponse.from_orm_with_project(inspiration)
    
    return success(data=response_data.model_dump(), msg="创建成功")


@router.get("", response_model=dict)
async def get_inspiration_list(
    pageNum: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=10, ge=1, le=1000, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选：active/archived/deleted"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_pinned: Optional[bool] = Query(None, description="是否置顶筛选"),
    sort_by: Optional[str] = Query(default="created_at", description="排序字段"),
    sort_order: Optional[str] = Query(default="desc", description="排序方向"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取灵感列表
    
    支持分页、筛选、搜索、排序
    """
    params = InspirationQueryParams(
        pageNum=pageNum,
        pageSize=pageSize,
        status=status,
        project_id=project_id,
        tag=tag,
        keyword=keyword,
        is_pinned=is_pinned,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    inspiration_service = InspirationService(db)
    result = await inspiration_service.get_inspiration_list(
        user_id=current_user.id,
        params=params
    )
    
    # 转换为响应格式
    items = [
        InspirationResponse.from_orm_with_project(item).model_dump()
        for item in result.list
    ]
    
    return page_response(
        items=items,
        total=result.total,
        page_num=result.pageNum,
        page_size=result.pageSize,
        msg="获取成功"
    )


@router.get("/{inspiration_id}", response_model=dict)
async def get_inspiration_detail(
    inspiration_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取灵感详情
    """
    inspiration_service = InspirationService(db)
    inspiration = await inspiration_service.get_inspiration_by_id(
        inspiration_id,
        current_user.id
    )
    
    response_data = InspirationResponse.from_orm_with_project(inspiration)
    
    return success(data=response_data.model_dump(), msg="获取成功")


@router.put("/{inspiration_id}", response_model=dict)
async def update_inspiration(
    inspiration_id: int,
    data: InspirationUpdate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新灵感
    
    如果更新内容，需要进行内容安全检测
    """
    # 如果更新内容，进行内容安全检测
    if data.content:
        security_result = await SecurityService.msg_sec_check(content=data.content)
        if not security_result['pass']:
            raise BadRequestException("内容包含违规信息，请修改后重试")
    
    inspiration_service = InspirationService(db)
    inspiration = await inspiration_service.update_inspiration(
        inspiration_id=inspiration_id,
        user_id=current_user.id,
        data=data
    )
    
    response_data = InspirationResponse.from_orm_with_project(inspiration)
    
    return success(data=response_data.model_dump(), msg="更新成功")


@router.delete("/{inspiration_id}", response_model=dict)
async def delete_inspiration(
    inspiration_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除灵感（软删除）
    """
    inspiration_service = InspirationService(db)
    await inspiration_service.delete_inspiration(
        inspiration_id=inspiration_id,
        user_id=current_user.id
    )
    
    return success(msg="删除成功")


@router.post("/{inspiration_id}/pin", response_model=dict)
async def pin_inspiration(
    inspiration_id: int,
    data: InspirationPinRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    置顶/取消置顶灵感
    """
    inspiration_service = InspirationService(db)
    inspiration = await inspiration_service.pin_inspiration(
        inspiration_id=inspiration_id,
        user_id=current_user.id,
        is_pinned=data.is_pinned
    )
    
    response_data = InspirationResponse.from_orm_with_project(inspiration)
    
    return success(data=response_data.model_dump(), msg="操作成功")


@router.post("/{inspiration_id}/archive", response_model=dict)
async def archive_inspiration(
    inspiration_id: int,
    data: InspirationArchiveRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    归档/取消归档灵感
    """
    inspiration_service = InspirationService(db)
    inspiration = await inspiration_service.archive_inspiration(
        inspiration_id=inspiration_id,
        user_id=current_user.id,
        status=data.status
    )
    
    response_data = InspirationResponse.from_orm_with_project(inspiration)
    
    return success(data=response_data.model_dump(), msg="操作成功")


@router.post("/{inspiration_id}/generate", response_model=dict)
async def generate_script(
    inspiration_id: int,
    request: InspirationGenerateRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    一键生成口播文案
    
    需要消耗算力，生成失败会自动退款
    """
    # 确保inspiration_id一致
    request.inspiration_id = inspiration_id
    
    generate_service = InspirationGenerateService(db)
    result = await generate_service.generate_script(
        user_id=current_user.id,
        request=request
    )
    
    return success(
        data=InspirationGenerateResponse(**result).model_dump(),
        msg="生成成功"
    )


@router.get("/{inspiration_id}/generated", response_model=dict)
async def get_generated_content(
    inspiration_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取已生成的内容
    """
    inspiration_service = InspirationService(db)
    inspiration = await inspiration_service.get_inspiration_by_id(
        inspiration_id,
        current_user.id
    )
    
    if not inspiration.has_generated_content:
        raise NotFoundException("该灵感尚未生成内容")
    
    return success(
        data={
            "content": inspiration.generated_content,
            "generated_at": inspiration.generated_at.isoformat() if inspiration.generated_at else None,
        },
        msg="获取成功"
    )

