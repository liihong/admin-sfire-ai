"""
Dashboard Statistics Service
Dashboard 统计服务
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
import httpx
from loguru import logger
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import RedisCache
from app.models.user import User
from app.models.compute import ComputeLog, ComputeType
from app.schemas.dashboard import (
    DashboardStats,
    OverviewStats,
    ApiMonitoringStats,
    ChartStats,
    UserTrendItem,
    CallTrendItem,
    AbnormalUserRecord,
)
from app.core.config import settings
from app.middleware.rate_limiter import RateLimiter


# 缓存键前缀
CACHE_KEY_DASHBOARD_STATS = "dashboard:stats"
# 缓存时间（秒）: 5 分钟
CACHE_TTL = 300


class DashboardService:
    """
    Dashboard 统计服务类
    
    提供以下功能:
    - 获取用户概览统计
    - 获取 API 监控数据（调用 Tikhub/OpenAI 接口）
    - 获取图表数据（用户趋势、调用趋势）
    - Redis 缓存支持
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_stats(self, use_cache: bool = True) -> DashboardStats:
        """
        获取 Dashboard 完整统计数据
        
        Args:
            use_cache: 是否使用缓存，默认为 True
        
        Returns:
            DashboardStats: 完整的统计数据
        """
        # 尝试从缓存获取
        if use_cache:
            cached_data = await RedisCache.get(CACHE_KEY_DASHBOARD_STATS)
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    logger.debug("Dashboard stats loaded from cache")
                    return DashboardStats(**data)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Failed to parse cached dashboard stats: {e}")
        
        # 从数据库获取新数据
        overview = await self._get_overview_stats()
        api_monitoring = await self._get_api_monitoring_stats()
        charts = await self._get_chart_stats()
        abnormal_users = await self._get_abnormal_users()
        
        stats = DashboardStats(
            overview=overview,
            api_monitoring=api_monitoring,
            charts=charts,
            abnormal_users=abnormal_users,
        )
        
        # 存入缓存
        try:
            await RedisCache.set(
                CACHE_KEY_DASHBOARD_STATS,
                stats.model_dump_json(),
                expire=CACHE_TTL,
            )
            logger.debug("Dashboard stats saved to cache")
        except Exception as e:
            logger.warning(f"Failed to cache dashboard stats: {e}")
        
        return stats
    
    async def _get_overview_stats(self) -> OverviewStats:
        """
        获取概览统计数据
        
        Returns:
            OverviewStats: 概览统计
        """
        # 今天的日期范围
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 1. 总用户数
        total_users_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.is_deleted == False
            )
        )
        total_users = total_users_result.scalar() or 0
        
        # 2. 今日新增用户
        new_users_result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_deleted == False,
                    User.created_at >= today_start,
                    User.created_at < today_end,
                )
            )
        )
        new_users_today = new_users_result.scalar() or 0
        
        # 3. 今日活跃用户（根据 updated_at 作为最后活跃时间的代理）
        # 注意：实际项目中可能需要一个专门的 last_login_at 字段
        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_deleted == False,
                    User.is_active == True,
                    User.updated_at >= today_start,
                    User.updated_at < today_end,
                )
            )
        )
        active_users_today = active_users_result.scalar() or 0
        
        # 4. 平台总算力余额
        total_balance_result = await self.db.execute(
            select(func.sum(User.balance)).where(
                User.is_deleted == False
            )
        )
        total_balance = total_balance_result.scalar() or Decimal("0.0000")
        
        return OverviewStats(
            total_users=total_users,
            new_users_today=new_users_today,
            active_users_today=active_users_today,
            total_balance=total_balance,
        )
    
    async def _get_api_monitoring_stats(self) -> ApiMonitoringStats:
        """
        获取 API 监控统计数据
        
        包括调用外部 API 获取账户余额
        
        Returns:
            ApiMonitoringStats: API 监控统计
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 1. 获取外部 API 余额（Tikhub/OpenAI）
        tikhub_balance = await self._get_tikhub_balance()
        openai_balance = await self._get_openai_balance()
        
        # 2. 计算今日已消耗成本（从 ComputeLog 中统计 CONSUME 类型的记录）
        today_cost_result = await self.db.execute(
            select(func.sum(func.abs(ComputeLog.amount))).where(
                and_(
                    ComputeLog.type == ComputeType.CONSUME,
                    ComputeLog.created_at >= today_start,
                    ComputeLog.created_at < today_end,
                )
            )
        )
        today_cost = today_cost_result.scalar() or Decimal("0.0000")
        
        # 3. 今日 API 调用次数（统计 ComputeLog 中的消费记录数量）
        today_calls_result = await self.db.execute(
            select(func.count(ComputeLog.id)).where(
                and_(
                    ComputeLog.type == ComputeType.CONSUME,
                    ComputeLog.created_at >= today_start,
                    ComputeLog.created_at < today_end,
                )
            )
        )
        today_api_calls = today_calls_result.scalar() or 0
        
        return ApiMonitoringStats(
            tikhub_balance=tikhub_balance,
            openai_balance=openai_balance,
            today_cost=today_cost,
            today_api_calls=today_api_calls,
        )
    
    async def _get_tikhub_balance(self) -> Optional[Decimal]:
        """
        获取 Tikhub 账户余额
        
        调用 Tikhub API 获取当前账户余额
        
        Returns:
            Optional[Decimal]: 账户余额，获取失败返回 None
        """
        tikhub_api_key = getattr(settings, 'TIKHUB_API_KEY', None)
        if not tikhub_api_key:
            logger.debug("TIKHUB_API_KEY not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.tikhub.io/api/v1/users/me",
                    headers={"Authorization": f"Bearer {tikhub_api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # 根据 Tikhub API 响应结构提取余额
                    balance = data.get("data", {}).get("balance", 0)
                    return Decimal(str(balance))
                else:
                    logger.warning(f"Tikhub API returned status {response.status_code}")
                    return None
        except Exception as e:
            logger.warning(f"Failed to get Tikhub balance: {e}")
            return None
    
    async def _get_openai_balance(self) -> Optional[Decimal]:
        """
        获取 OpenAI 账户余额
        
        调用 OpenAI API 获取当前账户余额
        注意: OpenAI 官方 API 目前不直接提供余额查询，
        这里使用 billing API（需要有效的 API Key）
        
        Returns:
            Optional[Decimal]: 账户余额，获取失败返回 None
        """
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key:
            logger.debug("OPENAI_API_KEY not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 获取订阅信息
                response = await client.get(
                    "https://api.openai.com/dashboard/billing/credit_grants",
                    headers={"Authorization": f"Bearer {openai_api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # 计算剩余额度
                    total_granted = Decimal(str(data.get("total_granted", 0)))
                    total_used = Decimal(str(data.get("total_used", 0)))
                    balance = total_granted - total_used
                    return balance
                else:
                    logger.warning(f"OpenAI API returned status {response.status_code}")
                    return None
        except Exception as e:
            logger.warning(f"Failed to get OpenAI balance: {e}")
            return None
    
    async def _get_chart_stats(self) -> ChartStats:
        """
        获取图表统计数据
        
        Returns:
            ChartStats: 图表统计数据
        """
        user_trend = await self._get_user_trend()
        call_trend = await self._get_call_trend()
        
        return ChartStats(
            user_trend=user_trend,
            call_trend=call_trend,
        )
    
    async def _get_user_trend(self) -> List[UserTrendItem]:
        """
        获取过去 7 天每天的新增用户数
        
        使用 SQLAlchemy func.count 和 group_by 进行聚合
        
        Returns:
            List[UserTrendItem]: 用户趋势数据列表
        """
        # 过去 7 天的日期范围
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        
        # 按日期分组统计新增用户数
        result = await self.db.execute(
            select(
                func.date(User.created_at).label("date"),
                func.count(User.id).label("count")
            ).where(
                and_(
                    User.is_deleted == False,
                    User.created_at >= start_date,
                    User.created_at < end_date,
                )
            ).group_by(
                func.date(User.created_at)
            ).order_by(
                func.date(User.created_at)
            )
        )
        
        # 转换为字典方便查找
        daily_counts: Dict[str, int] = {}
        for row in result.fetchall():
            date_str = row.date.strftime("%Y-%m-%d") if hasattr(row.date, 'strftime') else str(row.date)
            daily_counts[date_str] = row.count
        
        # 构建完整的 7 天数据（包括没有新增用户的日期）
        trend_data: List[UserTrendItem] = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            count = daily_counts.get(date_str, 0)
            trend_data.append(UserTrendItem(date=date_str, count=count))
        
        return trend_data
    
    async def _get_call_trend(self) -> List[CallTrendItem]:
        """
        获取过去 24 小时每小时的 API 请求数统计
        
        使用 SQLAlchemy func.count 和 group_by 进行聚合
        
        Returns:
            List[CallTrendItem]: 调用趋势数据列表
        """
        # 过去 24 小时的时间范围
        now = datetime.now()
        start_time = now - timedelta(hours=24)
        
        # 按小时分组统计 API 调用数（使用 ComputeLog 的 CONSUME 类型作为 API 调用的代理）
        result = await self.db.execute(
            select(
                func.date_format(ComputeLog.created_at, '%Y-%m-%d %H:00').label("hour"),
                func.count(ComputeLog.id).label("count")
            ).where(
                and_(
                    ComputeLog.type == ComputeType.CONSUME,
                    ComputeLog.created_at >= start_time,
                    ComputeLog.created_at <= now,
                )
            ).group_by(
                func.date_format(ComputeLog.created_at, '%Y-%m-%d %H:00')
            ).order_by(
                func.date_format(ComputeLog.created_at, '%Y-%m-%d %H:00')
            )
        )
        
        # 转换为字典方便查找
        hourly_counts: Dict[str, int] = {}
        for row in result.fetchall():
            hourly_counts[row.hour] = row.count
        
        # 构建完整的 24 小时数据（包括没有调用的小时）
        trend_data: List[CallTrendItem] = []
        for i in range(24):
            hour_time = start_time + timedelta(hours=i)
            hour_str = hour_time.strftime("%Y-%m-%d %H:00")
            display_hour = hour_time.strftime("%H:00")
            count = hourly_counts.get(hour_str, 0)
            trend_data.append(CallTrendItem(hour=display_hour, count=count))
        
        return trend_data
    
    async def _get_abnormal_users(self, limit: int = 5) -> List[AbnormalUserRecord]:
        """
        获取最近的异常用户记录
        
        Args:
            limit: 返回的记录数量，默认 5 条
        
        Returns:
            List[AbnormalUserRecord]: 异常用户记录列表
        """
        try:
            # 从 RateLimiter 获取异常用户记录
            records = await RateLimiter.get_abnormal_users(limit=limit)
            
            # 转换为 Pydantic 模型
            abnormal_users = []
            for record in records:
                abnormal_users.append(AbnormalUserRecord(
                    user_id=record.get("user_id", 0),
                    call_count=record.get("call_count", 0),
                    endpoint=record.get("endpoint", ""),
                    ip_address=record.get("ip_address", ""),
                    reason=record.get("reason", ""),
                    detected_at=record.get("detected_at", ""),
                    timestamp=record.get("timestamp"),
                ))
            
            return abnormal_users
            
        except Exception as e:
            logger.warning(f"Failed to get abnormal users: {e}")
            return []
    
    async def refresh_cache(self) -> DashboardStats:
        """
        强制刷新缓存
        
        删除现有缓存并重新获取数据
        
        Returns:
            DashboardStats: 新的统计数据
        """
        # 删除现有缓存
        await RedisCache.delete(CACHE_KEY_DASHBOARD_STATS)
        
        # 重新获取数据（不使用缓存）
        return await self.get_dashboard_stats(use_cache=False)
    
    async def clear_abnormal_records(self) -> bool:
        """
        清空异常用户记录
        
        Returns:
            bool: 是否成功
        """
        return await RateLimiter.clear_abnormal_records()

