# -*- coding: utf-8 -*-
"""
仅创建 admin_users 表的脚本（不删除其他表）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from db.session import init_db, async_session_maker, close_db, create_tables


async def main():
    """
    主函数：仅创建 admin_users 表
    """
    logger.info("=" * 60)
    logger.info("开始创建 admin_users 表...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        logger.info("正在连接 MySQL 数据库...")
        await init_db()
        logger.info("数据库连接成功")
        
        # 创建所有表（SQLAlchemy 会自动跳过已存在的表）
        logger.info("正在创建数据库表（仅创建缺失的表）...")
        await create_tables()
        logger.info("数据库表创建完成")
        
        logger.info("=" * 60)
        logger.info("admin_users 表创建完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"创建表过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # 关闭数据库连接
        await close_db()
        logger.info("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())





















