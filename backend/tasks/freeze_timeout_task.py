"""
冻结算力超时退还定时任务Worker
每30分钟执行一次，自动退还超时未解冻的算力
"""
import asyncio
from loguru import logger

from db.session import async_session_maker
from services.coin.freeze_timeout import refund_stale_frozen_compute


# 执行间隔：每天一次（后期使用频率高了可改为更短间隔，如 30 分钟）
EXECUTION_INTERVAL_SECONDS = 24 * 60 * 60


async def freeze_timeout_worker(stop_event: asyncio.Event):
    """
    冻结算力超时退还定时任务Worker

    每天执行一次，扫描超时未解冻的算力并自动退还。
    适用于用户中途断开、异常退出等导致预冻结算力未能正常结算/退款的场景。

    Args:
        stop_event: 停止事件
    """
    logger.info("🚀 [冻结算力超时任务] 启动")

    while not stop_event.is_set():
        try:
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=EXECUTION_INTERVAL_SECONDS
                )
                break
            except asyncio.TimeoutError:
                pass

            logger.info("🔍 [冻结算力超时任务] 开始执行超时冻结算力退还...")

            async with async_session_maker() as db:
                try:
                    refunded_count = await refund_stale_frozen_compute(db)
                    logger.info(
                        f"✅ [冻结算力超时任务] 执行完成，退还 {refunded_count} 条冻结记录"
                    )
                except Exception as e:
                    logger.error(f"❌ [冻结算力超时任务] 执行失败: {e}")

        except Exception as e:
            logger.error(f"❌ [冻结算力超时任务] Worker异常: {e}")
            await asyncio.sleep(3600)

    logger.info("🛑 [冻结算力超时任务] 已停止")
