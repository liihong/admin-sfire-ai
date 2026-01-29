"""
VIP过期检查定时任务
定期检查并处理过期VIP用户的降级
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from loguru import logger

from models.user import User
from services.system.membership import MembershipService


async def check_expired_vips(db: AsyncSession) -> int:
    """
    检查所有过期VIP用户并处理降级
    
    建议每天00:00执行一次
    
    Args:
        db: 数据库会话
        
    Returns:
        处理的用户数量
    """
    membership_service = MembershipService(db)
    
    # 查询VIP/SVIP/MAX用户（使用level_code过滤）
    query = select(User).where(
        User.is_deleted == False,
        User.level_code.in_(["vip", "svip", "max"]),
        # 只查询有VIP到期时间的用户（没有到期时间的视为永久有效）
        User.vip_expire_date.isnot(None)
    )
    
    result = await db.execute(query)
    vip_users = result.scalars().all()
    
    now = datetime.now(timezone.utc)
    processed_count = 0
    
    for user in vip_users:
        # 检查VIP是否过期
        if user.vip_expire_date:
            # 处理时区问题：如果 vip_expire_date 是 naive datetime，假设它是 UTC 时间并转换为 aware
            expire_date = user.vip_expire_date
            if expire_date.tzinfo is None:
                # naive datetime，假设是 UTC 时间
                expire_date = expire_date.replace(tzinfo=timezone.utc)
            
            if expire_date < now:
                try:
                    result = await membership_service.handle_user_downgrade(user.id)
                    processed_count += 1
                    logger.info(
                        f"处理过期VIP用户: user_id={user.id}, "
                        f"username={user.username}, "
                        f"level_code={user.level_code}, "
                        f"expire_date={expire_date}, "
                        f"result={result}"
                    )
                except Exception as e:
                    logger.error(
                        f"处理过期VIP用户失败: user_id={user.id}, "
                        f"username={user.username}, error={e}"
                    )
    
    logger.info(
        f"VIP过期检查完成: 检查{len(vip_users)}个VIP用户, "
        f"处理{processed_count}个过期用户"
    )
    
    return processed_count

