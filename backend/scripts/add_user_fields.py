"""
添加用户表新字段的迁移脚本
添加 partner_balance 和 vip_expire_date 字段
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from db.session import init_db, async_session_maker, close_db


async def add_user_fields():
    """
    添加用户表新字段
    """
    await init_db()
    
    async with async_session_maker() as session:
        try:
            # 检查字段是否已存在
            check_sql = text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME IN ('partner_balance', 'vip_expire_date')
            """)
            
            result = await session.execute(check_sql)
            existing_columns = {row[0] for row in result.fetchall()}
            
            # 添加 partner_balance 字段
            if 'partner_balance' not in existing_columns:
                logger.info("Adding partner_balance field...")
                alter_sql = text("""
                    ALTER TABLE users 
                    ADD COLUMN partner_balance DECIMAL(16,4) NOT NULL DEFAULT 0.0000 
                    COMMENT '合伙人资产余额'
                    AFTER frozen_balance
                """)
                await session.execute(alter_sql)
                logger.info("partner_balance field added successfully")
            else:
                logger.info("partner_balance field already exists, skipping")
            
            # 添加 vip_expire_date 字段
            if 'vip_expire_date' not in existing_columns:
                logger.info("Adding vip_expire_date field...")
                alter_sql = text("""
                    ALTER TABLE users 
                    ADD COLUMN vip_expire_date DATETIME NULL 
                    COMMENT '会员到期时间'
                    AFTER partner_balance
                """)
                await session.execute(alter_sql)
                logger.info("vip_expire_date field added successfully")
            else:
                logger.info("vip_expire_date field already exists, skipping")
            
            await session.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await session.rollback()
            raise
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(add_user_fields())

