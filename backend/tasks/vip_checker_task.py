"""
VIP过期检查定时任务Worker
每天00:00执行一次VIP过期检查
"""
import asyncio
from datetime import datetime, time, timezone, timedelta
from loguru import logger

from db.session import async_session_maker
from services.system.vip_checker import check_expired_vips


async def vip_checker_worker(stop_event: asyncio.Event):
    """
    VIP过期检查定时任务Worker
    
    每天00:00执行一次VIP过期检查
    
    Args:
        stop_event: 停止事件
    """
    logger.info("🚀 [VIP检查任务] 启动")
    
    while not stop_event.is_set():
        try:
            # 计算到下一个00:00的时间
            now = datetime.now(timezone.utc)
            next_midnight = datetime.combine(
                now.date() + timedelta(days=1),
                time(0, 0, 0)
            ).replace(tzinfo=timezone.utc)
            
            # 计算等待时间
            # 如果当前时间已经过了00:00但还没到00:05，立即执行
            # 否则等待到下一个00:00
            if now.hour == 0 and now.minute < 5:
                # 刚过00:00，立即执行
                wait_seconds = 0
            else:
                # 计算到下一个00:00的等待时间
                wait_seconds = (next_midnight - now).total_seconds()
                # 确保等待时间不为负数
                if wait_seconds < 0:
                    wait_seconds = 0
            
            logger.info(
                f"⏰ [VIP检查任务] 下次执行时间: {next_midnight}, "
                f"等待 {wait_seconds:.0f} 秒"
            )
            
            # 等待到指定时间（或停止事件）
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=wait_seconds
                )
                # 如果stop_event被设置，退出循环
                break
            except asyncio.TimeoutError:
                # 超时，执行检查任务
                pass
            
            # 执行VIP过期检查
            logger.info("🔍 [VIP检查任务] 开始执行VIP过期检查...")
            
            async with async_session_maker() as db:
                try:
                    processed_count = await check_expired_vips(db)
                    logger.info(
                        f"✅ [VIP检查任务] 执行完成，处理了 {processed_count} 个过期用户"
                    )
                except Exception as e:
                    logger.error(f"❌ [VIP检查任务] 执行失败: {e}")
            
            # 执行完成后，等待一小段时间再进入下一轮循环
            # 避免在00:00:00-00:00:05之间重复执行
            await asyncio.sleep(300)  # 等待5分钟
            
        except Exception as e:
            logger.error(f"❌ [VIP检查任务] Worker异常: {e}")
            # 发生异常时等待1小时后重试
            await asyncio.sleep(3600)
    
    logger.info("🛑 [VIP检查任务] 已停止")

