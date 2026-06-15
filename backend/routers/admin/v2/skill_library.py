"""
技能库管理路由（v2版本）
后台管理接口
"""
import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.deps import _get_db
from schemas.v2.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListItemResponse,
    SkillCategoryResponse,
)
from services.skill import SkillService
from utils.response import success, page_response, ResponseMsg
from utils.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/skills", tags=["技能库管理"])


async def _sync_skill_embedding(skill_id: int):
    """后台任务：将技能同步到向量库（启用则更新，禁用则删除）"""
    try:
        from db import session as db_session
        from services.skill.embedding import get_skill_embedding_service

        if db_session.async_session_maker is None:
            await db_session.init_db()
        async with db_session.async_session_maker() as db:
            service = get_skill_embedding_service()
            skill = await SkillService.get_by_id(db, skill_id)
            if skill:
                if skill.status == 1:
                    await service.update_skill_embedding(db, skill_id)
                else:
                    await service.delete_skill_embedding(skill_id)
    except Exception as e:
        logger.warning(f"技能 {skill_id} 向量库同步失败（可稍后手动执行导入脚本）: {e}")


async def _delete_skill_embedding(skill_id: int):
    """后台任务：从向量库删除技能（物理删除技能时调用）"""
    try:
        from services.skill.embedding import get_skill_embedding_service

        service = get_skill_embedding_service()
        await service.delete_skill_embedding(skill_id)
    except Exception as e:
        logger.warning(f"技能 {skill_id} 向量库删除失败: {e}")


def _schedule_sync_embedding(skill_id: int) -> None:
    """调度向量库同步，与 HTTP 请求生命周期解耦"""
    try:
        asyncio.get_running_loop().create_task(_sync_skill_embedding(skill_id))
    except RuntimeError:
        logger.warning(f"技能 {skill_id} 向量同步调度失败：无运行中的事件循环")


def _schedule_delete_embedding(skill_id: int) -> None:
    """调度向量库删除，与 HTTP 请求生命周期解耦"""
    try:
        asyncio.get_running_loop().create_task(_delete_skill_embedding(skill_id))
    except RuntimeError:
        logger.warning(f"技能 {skill_id} 向量删除调度失败：无运行中的事件循环")


@router.get("/list")
async def get_skill_list(
    page: int = 1,
    size: int = 20,
    category: str = None,
    status: int = None,
    db: AsyncSession = Depends(_get_db),
):
    """
    获取技能列表

    支持按分类、状态筛选
    """
    try:
        skills, total = await SkillService.get_list(
            db,
            page=page,
            size=size,
            category=category,
            status=status,
        )

        items = [SkillListItemResponse.model_validate(s).model_dump() for s in skills]
        return page_response(
            items=items,
            total=total,
            page_num=page,
            page_size=size,
            msg="获取成功"
        )
    except Exception as e:
        logger.error(f"获取技能列表失败: {e}")
        raise BadRequestException(msg="获取技能列表失败")


@router.get("/categories")
async def get_skill_categories(db: AsyncSession = Depends(_get_db)):
    """
    获取所有分类及其数量
    """
    try:
        categories = await SkillService.get_categories_with_count(db)
        data = [
            SkillCategoryResponse(category=c["category"], count=c["count"]).model_dump()
            for c in categories
        ]
        return success(data=data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise BadRequestException(msg="获取分类失败")


@router.get("/{skill_id}")
async def get_skill(skill_id: int, db: AsyncSession = Depends(_get_db)):
    """
    获取技能详情
    """
    skill = await SkillService.get_by_id(db, skill_id)
    if not skill:
        raise NotFoundException(msg="技能不存在")
    return success(data=SkillResponse.model_validate(skill).model_dump(), msg="获取成功")


@router.post("/")
async def create_skill(
    skill_data: SkillCreate,
    db: AsyncSession = Depends(_get_db),
):
    """
    创建技能
    """
    try:
        skill = await SkillService.create(db, skill_data.model_dump())
        logger.info(f"创建技能成功: {skill.name} (ID={skill.id})")
        # 异步同步到向量库（仅启用技能需同步）
        if skill.status == 1:
            _schedule_sync_embedding(skill.id)
        return success(data=SkillResponse.model_validate(skill).model_dump(), msg="创建成功")
    except Exception as e:
        logger.error(f"创建技能失败: {e}")
        raise BadRequestException(msg="创建技能失败")


@router.put("/{skill_id}")
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    db: AsyncSession = Depends(_get_db),
):
    """
    更新技能
    """
    skill = await SkillService.update(db, skill_id, skill_data.model_dump(exclude_unset=True))
    if not skill:
        raise NotFoundException(msg="技能不存在")
    logger.info(f"更新技能成功: {skill.name} (ID={skill_id})")
    # 异步同步到向量库（启用则更新，禁用则删除）
    _schedule_sync_embedding(skill.id)
    return success(data=SkillResponse.model_validate(skill).model_dump(), msg="更新成功")


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(_get_db),
):
    """
    删除技能（物理删除）

    注意：
        - 此接口会直接从数据库中移除技能记录
        - 如果只是希望在页面上不展示，请使用单独的禁用接口
    """
    result = await SkillService.delete(db, skill_id)
    if not result:
        raise NotFoundException(msg="技能不存在")
    logger.info(f"删除技能成功: ID={skill_id}")
    # 从向量库移除
    _schedule_delete_embedding(skill_id)
    return success(msg="删除成功")


@router.put("/{skill_id}/status")
async def update_skill_status(
    skill_id: int,
    status: int,
    db: AsyncSession = Depends(_get_db),
):
    """
    更新技能状态（启用/禁用）

    前端可以通过该接口实现“禁用/启用”功能，而不是复用删除接口：
        - status = 1: 启用
        - status = 0: 禁用
    """
    skill = await SkillService.update_status(db, skill_id, status)
    if not skill:
        raise NotFoundException(msg="技能不存在")

    action = "启用" if skill.status == 1 else "禁用"
    logger.info(f"{action}技能成功: ID={skill_id}")
    return success(
        data=SkillResponse.model_validate(skill).model_dump(),
        msg=f"{action}成功",
    )
