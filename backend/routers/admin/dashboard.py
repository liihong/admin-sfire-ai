"""
Dashboard Statistics Endpoints
Dashboard 统计接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services.dashboard import DashboardService
from utils.response import success

router = APIRouter()


@router.get("/stats", summary="获取 Dashboard 统计数据")
async def get_dashboard_stats(
    refresh: bool = Query(False, description="是否强制刷新缓存"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取 Dashboard 统计数据
    
    返回数据包括:
    - **overview**: 概览统计
        - total_users: 总用户数
        - new_users_today: 今日新增用户
        - active_users_today: 今日活跃用户
        - total_balance: 平台总算力余额
    
    - **api_monitoring**: API 监控
        - tikhub_balance: Tikhub 账户余额
        - openai_balance: OpenAI 账户余额
        - today_cost: 今日已消耗成本
        - today_api_calls: 今日 API 调用次数
    
    - **charts**: 图表数据
        - user_trend: 过去 7 天每天的新增用户数
        - call_trend: 过去 24 小时每小时的 API 请求数
    
    - **abnormal_users**: 最近异常用户列表（最多 5 条）
        - user_id: 用户 ID
        - call_count: 调用次数
        - endpoint: 触发异常的接口
        - ip_address: 客户端 IP
        - reason: 异常原因
        - detected_at: 检测时间
    
    注意:
    - 默认启用 5 分钟 Redis 缓存
    - 设置 refresh=true 可强制刷新缓存
    - 异常用户: 1 分钟内调用 API 超过 60 次的用户
    """
    dashboard_service = DashboardService(db)
    
    if refresh:
        # 强制刷新缓存
        stats = await dashboard_service.refresh_cache()
    else:
        # 使用缓存
        stats = await dashboard_service.get_dashboard_stats(use_cache=True)
    
    return success(data=stats.model_dump())


@router.get("/overview", summary="获取概览统计")
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取概览统计数据
    
    仅返回 overview 部分的数据:
    - total_users: 总用户数
    - new_users_today: 今日新增用户
    - active_users_today: 今日活跃用户
    - total_balance: 平台总算力余额
    """
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_dashboard_stats(use_cache=True)
    
    return success(data=stats.overview.model_dump())


@router.get("/api-monitoring", summary="获取 API 监控数据")
async def get_api_monitoring_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取 API 监控统计数据
    
    仅返回 api_monitoring 部分的数据:
    - tikhub_balance: Tikhub 账户余额
    - openai_balance: OpenAI 账户余额
    - today_cost: 今日已消耗成本
    - today_api_calls: 今日 API 调用次数
    """
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_dashboard_stats(use_cache=True)
    
    return success(data=stats.api_monitoring.model_dump())


@router.get("/charts", summary="获取图表数据")
async def get_chart_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取图表统计数据
    
    仅返回 charts 部分的数据:
    - user_trend: 过去 7 天每天的新增用户数
    - call_trend: 过去 24 小时每小时的 API 请求数
    """
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_dashboard_stats(use_cache=True)
    
    return success(data=stats.charts.model_dump())


@router.post("/refresh", summary="刷新统计缓存")
async def refresh_dashboard_cache(
    db: AsyncSession = Depends(get_db),
):
    """
    强制刷新 Dashboard 统计缓存
    
    删除现有缓存并重新获取最新数据
    """
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.refresh_cache()
    
    return success(data=stats.model_dump(), msg="缓存已刷新")


@router.get("/user-trend", summary="获取用户增长趋势")
async def get_user_trend(
    days: int = Query(7, ge=1, le=365, description="查询天数，默认7天，最大365天"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户增长趋势数据
    
    返回指定天数内每天的新增用户数
    
    Args:
        days: 查询天数，默认 7 天，最大 365 天
    
    Returns:
        用户趋势数据列表，每个元素包含:
        - date: 日期 (YYYY-MM-DD)
        - count: 新增用户数
    """
    dashboard_service = DashboardService(db)
    trend_data = await dashboard_service.get_user_trend(days=days)
    
    return success(data=[item.model_dump() for item in trend_data])


@router.get("/abnormal-users", summary="获取异常用户列表")
async def get_abnormal_users(
    limit: int = Query(5, ge=1, le=100, description="返回记录数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取最近的异常用户记录
    
    异常用户: 1 分钟内调用 API 超过 60 次的用户
    
    返回字段:
    - user_id: 用户 ID
    - call_count: 调用次数
    - endpoint: 触发异常的接口路径
    - ip_address: 客户端 IP 地址
    - reason: 异常原因
    - detected_at: 检测时间
    """
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_dashboard_stats(use_cache=True)
    
    # 如果需要更多记录，直接从 Redis 获取
    if limit > 5:
        from middleware.rate_limiter import RateLimiter
        records = await RateLimiter.get_abnormal_users(limit=limit)
        return success(data=records)
    
    return success(data=[u.model_dump() for u in stats.abnormal_users[:limit]])


@router.delete("/abnormal-users", summary="清空异常用户记录")
async def clear_abnormal_users(
    db: AsyncSession = Depends(get_db),
):
    """
    清空所有异常用户记录

    注意: 此操作不可逆
    """
    dashboard_service = DashboardService(db)
    result = await dashboard_service.clear_abnormal_records()

    if result:
        return success(msg="异常记录已清空")
    else:
        return success(msg="清空失败，Redis 可能不可用", code=500)


@router.get("/agent-rank", summary="获取智能体调用排行")
async def get_agent_rank(
    limit: int = Query(5, ge=1, le=100, description="返回记录数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取智能体调用排行（Top N）

    统计每个智能体的调用次数（基于关联的会话数量），返回最受欢迎的智能体

    返回字段:
    - id: 智能体 ID
    - name: 智能体名称
    - icon: 智能体图标
    - call_count: 调用次数（会话数量）

    Args:
        limit: 返回记录数量，默认 5 条，最多 100 条
    """
    dashboard_service = DashboardService(db)
    agent_rank = await dashboard_service.get_agent_rank(limit=limit)

    return success(data=[item.model_dump() for item in agent_rank])

