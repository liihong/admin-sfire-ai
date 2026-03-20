"""
数据库迁移：为 compute_logs 表添加 (type, created_at) 复合索引

用于优化 Dashboard 统计接口中按类型+时间范围的查询性能。

执行方式：
    cd backend && python -m db.migrations.add_compute_logs_type_created_at_index
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text
from loguru import logger

from db.session import init_db, close_db


async def upgrade():
    """添加 (type, created_at) 复合索引"""
    from db.session import engine

    if engine is None:
        raise RuntimeError("Database not initialized")
    async with engine.begin() as conn:
        # 检查索引是否已存在（MySQL）
        result = await conn.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'compute_logs'
                AND INDEX_NAME = 'ix_compute_logs_type_created_at'
            """)
        )
        exists = result.scalar() > 0

        if exists:
            logger.info("ix_compute_logs_type_created_at 索引已存在，跳过迁移")
            return

        logger.info("正在添加 ix_compute_logs_type_created_at 索引到 compute_logs 表...")
        await conn.execute(
            text("""
                CREATE INDEX ix_compute_logs_type_created_at
                ON compute_logs (type, created_at)
            """)
        )
        logger.info("迁移完成：ix_compute_logs_type_created_at 索引已添加")


async def main():
    await init_db()
    try:
        await upgrade()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
