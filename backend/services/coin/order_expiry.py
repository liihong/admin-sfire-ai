"""
订单过期清理服务
定期清理过期的待支付订单
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from models.compute import ComputeLog, ComputeType


async def cleanup_expired_orders(db: AsyncSession) -> int:
    """
    清理过期的待支付订单
    
    将超过过期时间的pending订单状态更新为cancelled
    
    建议每小时执行一次
    
    Args:
        db: 数据库会话
        
    Returns:
        处理的订单数量
    """
    now = datetime.now()
    
    # 查询所有过期的pending订单
    query = select(ComputeLog).where(
        and_(
            ComputeLog.type == ComputeType.RECHARGE,
            ComputeLog.payment_status == "pending",
            ComputeLog.order_expire_at.isnot(None),
            ComputeLog.order_expire_at < now
        )
    )
    
    result = await db.execute(query)
    expired_orders = result.scalars().all()
    
    if not expired_orders:
        logger.debug("没有找到过期的订单")
        return 0
    
    # 批量更新订单状态和备注
    # 逐个更新订单（因为需要更新remark字段，批量更新字符串拼接在不同数据库中语法不同）
    for order in expired_orders:
        order.payment_status = "cancelled"
        if order.remark:
            order.remark = f"{order.remark}（订单已过期）"
        else:
            order.remark = "订单已过期"
    
    await db.flush()
    
    # 提取订单ID列表用于日志记录
    order_ids = [order.id for order in expired_orders]
    
    logger.info(
        f"订单过期清理完成: 清理了 {len(expired_orders)} 个过期订单, "
        f"订单号列表={order_ids[:10]}{'...' if len(order_ids) > 10 else ''}"
    )
    
    return len(expired_orders)

