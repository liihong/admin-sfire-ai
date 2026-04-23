"""
C 端：项目对标抖音账号（列表、拉取作品）
"""
import uuid

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from constants.coin_config import CoinConfig
from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from schemas.project_benchmark import (
    BenchmarkAccountCreate,
    BenchmarkAccountResponse,
    BenchmarkVideoItem,
    BenchmarkVideoListResponse,
)
from services.resource.project_benchmark import ProjectBenchmarkService
from services.coin import CoinServiceFactory
from utils.response import success

router = APIRouter()


# 路径挂载在 /api/v1/client/projects 下，见 client/__init__.py
def _account_to_response(row) -> BenchmarkAccountResponse:
    return BenchmarkAccountResponse(
        id=row.id,
        project_id=row.project_id,
        sec_uid=row.sec_uid,
        profile_url=row.profile_url,
        nickname=row.nickname or "",
        avatar_url=row.avatar_url or "",
        signature=row.signature or "",
        follower_count=int(row.follower_count or 0),
        following_count=int(row.following_count or 0),
        total_favorited=int(row.total_favorited or 0),
        aweme_count=int(row.aweme_count or 0),
        remark=row.remark,
        is_enabled=row.is_enabled,
    )


@router.post("/{project_id}/benchmark-accounts", summary="添加对标抖音账号")
async def add_benchmark_account(
    project_id: int,
    body: BenchmarkAccountCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectBenchmarkService(db)
    row = await svc.create(
        current_user.id,
        project_id,
        body.url,
        remark=body.remark,
    )
    data = _account_to_response(row).model_dump()
    return success(data=data, msg="添加成功")


@router.get("/{project_id}/benchmark-accounts", summary="对标账号列表")
async def list_benchmark_accounts(
    project_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectBenchmarkService(db)
    rows = await svc.list_by_project(current_user.id, project_id)
    items = [_account_to_response(r).model_dump() for r in rows]
    return success(data={"items": items}, msg="获取成功")


@router.delete(
    "/{project_id}/benchmark-accounts/{account_id}",
    summary="删除对标账号",
)
async def delete_benchmark_account(
    project_id: int,
    account_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectBenchmarkService(db)
    await svc.delete(current_user.id, project_id, account_id)
    return success(data=None, msg="删除成功")


@router.post(
    "/{project_id}/benchmark-accounts/{account_id}/refresh-profile",
    summary="手动刷新（账号资料+视频缓存）",
)
async def refresh_benchmark_account_profile(
    project_id: int,
    account_id: int,
    count: int = Query(40, ge=1, le=40, description="刷新视频数量（固定上限 40）"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    cost = CoinConfig.BENCHMARK_MONITOR_REFRESH_COST
    task_id = f"benchmark_refresh_{uuid.uuid4().hex}"
    coin = CoinServiceFactory(db)

    await coin.consume_fixed_tool_fee(
        user_id=current_user.id,
        amount=cost,
        remark="对标账号监控-手动刷新",
        task_id=task_id,
        source="miniapp",
    )

    svc = ProjectBenchmarkService(db)
    try:
        row, n = await svc.refresh_account_and_videos(
            current_user.id,
            project_id,
            account_id,
            limit=count,
        )
    except Exception:
        try:
            await coin.refund_fixed_tool_fee(
                user_id=current_user.id,
                amount=cost,
                remark="对标账号监控-刷新失败退还",
                task_id=task_id,
                source="miniapp",
            )
        except Exception as re:
            logger.error(
                "对标账号刷新失败后退费异常: user_id={} task_id={} err={}",
                current_user.id,
                task_id,
                re,
            )
        raise

    return success(
        data={
            "account": _account_to_response(row).model_dump(),
            "refreshed_count": n,
            "coin_cost": int(cost),
        },
        msg="刷新成功",
    )


@router.get(
    "/{project_id}/benchmark-accounts/{account_id}/videos",
    summary="查询对标账号视频缓存列表（仅MySQL）",
)
async def list_benchmark_videos(
    project_id: int,
    account_id: int,
    max_cursor: int = Query(0, ge=0, description="分页游标，首次传 0"),
    count: int = Query(20, ge=1, le=40, description="每页条数"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectBenchmarkService(db)
    account = await svc.get_account(current_user.id, project_id, account_id)
    raw_items, next_cursor, has_more = await svc.fetch_videos(
        current_user.id,
        project_id,
        account_id,
        max_cursor=max_cursor,
        count=count,
    )
    items = [BenchmarkVideoItem(**x) for x in raw_items]
    payload = BenchmarkVideoListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )
    return success(
        data={
            "account": _account_to_response(account).model_dump(),
            **payload.model_dump(),
        },
        msg="获取成功",
    )
