"""
冻结算力超时退还服务
定期检查并退还超时未解冻的算力（如用户中途断开、异常退出等场景）
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from models.compute_freeze import ComputeFreezeLog, FreezeStatus
from services.coin.factory import CoinServiceFactory


# 默认超时时间：30分钟未结算/退款的冻结记录视为异常，自动退还
DEFAULT_FREEZE_TIMEOUT_MINUTES = 30


async def refund_stale_frozen_compute(
    db: AsyncSession,
    timeout_minutes: int = DEFAULT_FREEZE_TIMEOUT_MINUTES
) -> int:
    """
    退还超时未解冻的算力

    场景：用户发起对话后预冻结算力，但因网络断开、关闭应用等原因
    未能完成结算或退款，导致冻结记录一直处于 FROZEN 状态。
    本任务定期扫描并自动退还此类异常冻结。

    建议每15-30分钟执行一次

    Args:
        db: 数据库会话
        timeout_minutes: 超时分钟数，超过此时间的冻结记录将被退还

    Returns:
        成功退还的冻结记录数量
    """
    cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)

    # 查询超时且仍为冻结状态的记录
    query = select(ComputeFreezeLog).where(
        and_(
            ComputeFreezeLog.status == FreezeStatus.FROZEN.value,
            ComputeFreezeLog.frozen_at < cutoff_time
        )
    ).order_by(ComputeFreezeLog.frozen_at.asc())

    result = await db.execute(query)
    stale_logs = result.scalars().all()

    if not stale_logs:
        logger.debug("没有找到超时的冻结算力记录")
        return 0

    # 提取需要退还的记录信息（避免 commit 后 ORM 对象过期）
    items_to_refund = [
        (log.request_id, log.user_id, float(log.amount))
        for log in stale_logs
    ]

    coin_service = CoinServiceFactory(db)
    success_count = 0

    for request_id, user_id, amount in items_to_refund:
        try:
            refund_result = await coin_service.refund_amount_atomic(
                user_id=user_id,
                request_id=request_id,
                reason="冻结算力超时自动退还（任务未完成或异常断开）"
            )
            if refund_result.get("success"):
                success_count += 1
                logger.info(
                    f"✅ [冻结算力超时] 自动退还: user_id={user_id}, "
                    f"request_id={request_id}, amount={amount}"
                )
            else:
                logger.warning(
                    f"⚠️ [冻结算力超时] 退还失败: user_id={user_id}, "
                    f"request_id={request_id}, msg={refund_result.get('message')}"
                )
        except Exception as e:
            logger.error(
                f"❌ [冻结算力超时] 退还异常: user_id={user_id}, "
                f"request_id={request_id}, error={e}"
            )

    if success_count > 0:
        logger.info(
            f"冻结算力超时退还完成: 扫描 {len(stale_logs)} 条, "
            f"成功退还 {success_count} 条"
        )

    return success_count
