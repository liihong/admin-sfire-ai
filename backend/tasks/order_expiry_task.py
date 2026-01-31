"""
订单过期清理定时任务Worker
每小时执行一次订单过期清理
"""
import asyncio
from datetime import datetime, timezone
from loguru import logger

from db.session import async_session_maker
from services.coin.order_expiry import cleanup_expired_orders


async def order_expiry_worker(stop_event: asyncio.Event):
    """
    订单过期清理定时任务Worker
    
    每小时执行一次订单过期清理
    
    Args:
        stop_event: 停止事件
    """
    logger.info("🚀 [订单过期清理任务] 启动")
    
    while not stop_event.is_set():
        try:
            # 等待1小时（3600秒）
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=3600
                )
                # 如果stop_event被设置，退出循环
                break
            except asyncio.TimeoutError:
                # 超时，执行清理任务
                pass
            
            # 执行订单过期清理
            logger.info("🔍 [订单过期清理任务] 开始执行订单过期清理...")
            
            async with async_session_maker() as db:
                try:
                    processed_count = await cleanup_expired_orders(db)
                    await db.commit()
                    logger.info(
                        f"✅ [订单过期清理任务] 执行完成，清理了 {processed_count} 个过期订单"
                    )
                except Exception as e:
                    logger.error(f"❌ [订单过期清理任务] 执行失败: {e}")
                    await db.rollback()
            
        except Exception as e:
            logger.error(f"❌ [订单过期清理任务] Worker异常: {e}")
            # 发生异常时等待1小时后重试
            await asyncio.sleep(3600)
    
    logger.info("🛑 [订单过期清理任务] 已停止")





