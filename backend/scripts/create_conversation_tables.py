"""
创建对话相关的数据库表
直接使用 SQL 语句创建，避免循环导入问题
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
import aiomysql

from core.config import settings


async def create_tables_with_sql():
    """使用 SQL 语句直接创建表"""
    # 读取 SQL 文件
    sql_file = Path(__file__).parent / "create_conversation_tables.sql"
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # 连接到数据库
    conn = await aiomysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        db=settings.MYSQL_DATABASE,
        charset="utf8mb4",
    )
    
    try:
        cursor = await conn.cursor()
        
        # 执行 SQL 语句（分割为单独的语句）
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]
        
        for statement in statements:
            if statement:
                logger.info(f"执行 SQL: {statement[:100]}...")
                await cursor.execute(statement)
        
        await conn.commit()
        logger.info("数据库表创建成功！")
        
        # 验证表是否创建成功
        await cursor.execute("SHOW TABLES LIKE 'conversations'")
        if await cursor.fetchone():
            logger.info("✓ 表 conversations 创建成功")
        else:
            logger.error("✗ 表 conversations 创建失败")
        
        await cursor.execute("SHOW TABLES LIKE 'conversation_messages'")
        if await cursor.fetchone():
            logger.info("✓ 表 conversation_messages 创建成功")
        else:
            logger.error("✗ 表 conversation_messages 创建失败")
        
        await cursor.execute("SHOW TABLES LIKE 'conversation_chunks'")
        if await cursor.fetchone():
            logger.info("✓ 表 conversation_chunks 创建成功")
        else:
            logger.error("✗ 表 conversation_chunks 创建失败")
        
    except Exception as e:
        await conn.rollback()
        logger.error(f"创建表失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


async def main():
    """
    主函数：创建对话相关的数据库表
    """
    logger.info("=" * 60)
    logger.info("开始创建对话相关的数据库表...")
    logger.info("=" * 60)
    
    try:
        await create_tables_with_sql()
        logger.info("=" * 60)
        logger.info("数据库表创建完成！")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"数据库表创建过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
