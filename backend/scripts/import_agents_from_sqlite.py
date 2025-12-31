"""
从 SQLite prompts.db 导入智能体数据到 MySQL agents 表
"""
import asyncio
import sys
from pathlib import Path
import sqlite3

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, close_db
from app.models.agent import Agent
from app.schemas.agent import AgentConfig

# SQLite 数据库路径
SQLITE_DB_PATH = Path("E:/project/sfire-ai/database/prompts.db")


async def import_agents_from_sqlite(session: AsyncSession) -> None:
    """
    从 SQLite 导入智能体数据到 MySQL
    """
    if not SQLITE_DB_PATH.exists():
        logger.error(f"SQLite 数据库文件不存在: {SQLITE_DB_PATH}")
        return
    
    # 连接 SQLite 数据库
    sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
    sqlite_cursor = sqlite_conn.cursor()
    
    # 查询所有激活的提示词
    sqlite_cursor.execute("""
        SELECT id, key, name, description, system_prompt, category, is_active
        FROM prompts
        WHERE is_active = 1
        ORDER BY id
    """)
    
    prompts = sqlite_cursor.fetchall()
    logger.info(f"从 SQLite 读取到 {len(prompts)} 条提示词数据")
    
    imported_count = 0
    updated_count = 0
    
    for prompt_data in prompts:
        sqlite_id, key, name, description, system_prompt, category, is_active = prompt_data
        
        # 检查是否已存在（通过 name 或 key 判断）
        result = await session.execute(
            select(Agent).where(
                (Agent.name == name) | (Agent.icon == key)
            )
        )
        existing_agent = result.scalar_one_or_none()
        
        # 默认配置
        default_config = AgentConfig(
            temperature=0.7,
            maxTokens=2000,
            topP=1.0,
            frequencyPenalty=0.0,
            presencePenalty=0.0,
        )
        
        # 根据分类设置不同的配置
        if category == "script":
            # 视频脚本类，需要更多token
            default_config.maxTokens = 4000
            default_config.temperature = 0.8
        elif category == "copywriting":
            # 文案类，需要更多创意
            default_config.temperature = 0.9
        
        if existing_agent:
            # 更新现有智能体
            existing_agent.name = name
            existing_agent.icon = key  # 使用key作为图标标识
            existing_agent.description = description or ""
            existing_agent.system_prompt = system_prompt
            existing_agent.model = "gpt-3.5-turbo"  # 默认模型
            existing_agent.config = default_config.model_dump()
            existing_agent.status = 1 if is_active else 0
            existing_agent.sort_order = sqlite_id  # 使用原ID作为排序
            
            await session.flush()
            updated_count += 1
            logger.info(f"更新智能体: {name} (key: {key})")
        else:
            # 创建新智能体
            agent = Agent(
                name=name,
                icon=key,  # 使用key作为图标标识
                description=description or "",
                system_prompt=system_prompt,
                model="gpt-3.5-turbo",  # 默认模型
                config=default_config.model_dump(),
                sort_order=sqlite_id,  # 使用原ID作为排序
                status=1 if is_active else 0,
                usage_count=0,
            )
            
            session.add(agent)
            await session.flush()
            await session.refresh(agent)
            imported_count += 1
            logger.info(f"导入智能体: {name} (key: {key}, ID: {agent.id})")
    
    sqlite_conn.close()
    
    logger.info(f"导入完成: 新增 {imported_count} 条, 更新 {updated_count} 条")


async def main():
    """
    主函数：执行数据导入
    """
    logger.info("=" * 60)
    logger.info("开始从 SQLite 导入智能体数据...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        await init_db()
        
        # 创建数据库表（如果不存在）
        from app.db.session import create_tables
        await create_tables()
        
        # 导入 async_session_maker（在 init_db 之后）
        from app.db.session import async_session_maker
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 导入智能体数据
                await import_agents_from_sqlite(session)
                
                # 提交事务
                await session.commit()
                
                logger.info("=" * 60)
                logger.info("智能体数据导入完成！")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"导入失败: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

