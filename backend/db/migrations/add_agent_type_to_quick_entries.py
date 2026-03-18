"""
数据库迁移：为 quick_entries 表添加 agent_type 字段

执行方式：
    cd backend && python -m db.migrations.add_agent_type_to_quick_entries
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text
from loguru import logger

from db.session import init_db, close_db


async def upgrade():
    """添加 agent_type 列"""
    from db.session import engine

    if engine is None:
        raise RuntimeError("Database not initialized")
    async with engine.begin() as conn:
        # 检查列是否已存在（MySQL）
        result = await conn.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'quick_entries'
                AND COLUMN_NAME = 'agent_type'
            """)
        )
        exists = result.scalar() > 0

        if exists:
            logger.info("agent_type 列已存在，跳过迁移")
            return

        logger.info("正在添加 agent_type 列到 quick_entries 表...")
        await conn.execute(
            text("""
                ALTER TABLE quick_entries
                ADD COLUMN agent_type VARCHAR(64) NULL
                COMMENT 'Agent类型分类（关联sys_dict id=3的字典项）'
                AFTER instructions
            """)
        )
        logger.info("迁移完成：agent_type 列已添加")


async def main():
    await init_db()
    try:
        await upgrade()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
