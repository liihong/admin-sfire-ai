"""
Database Session Management
"""
import json
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from loguru import logger

from core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy ORM 基类"""
    pass


# 异步数据库引擎
engine: AsyncEngine | None = None

# 异步会话工厂
async_session_maker: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    初始化数据库连接
    在应用启动时调用
    """
    global engine, async_session_maker

    logger.info("Initializing database connection...")

    try:
        # 构建连接URL,添加锁超时配置 - 使用安全的URL解析
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        db_url = settings.MYSQL_DATABASE_URL

        # 添加锁超时配置
        # 注意：charset=utf8mb4 已在 MYSQL_DATABASE_URL 中配置，支持 emoji 等 4 字节 UTF-8 字符
        parsed = urlparse(db_url)
        query_params = parse_qs(parsed.query)

        if "init_command" not in query_params:
            query_params["init_command"] = ["SET SESSION lock_wait_timeout=120"]
            new_query = urlencode(query_params, doseq=True)
            db_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))

        engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            poolclass=NullPool if settings.APP_ENV == "testing" else None,
            pool_pre_ping=True,  # 连接健康检查
            pool_recycle=3600,   # 1小时回收连接
            pool_size=10,        # 连接池大小
            max_overflow=20,     # 最大溢出连接数
            connect_args={
                "connect_timeout": 10,
            },
        )

        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database connection initialized successfully with lock_wait_timeout=120s")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def create_tables() -> None:
    """
    创建所有数据库表
    仅在开发环境使用，生产环境请使用 Alembic 迁移
    """
    global engine
    
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    # 导入所有模型确保它们被注册
    from models import (
        User, ComputeLog, Menu, Agent, Role, AdminUser, LLMModel, Project,
        Conversation, ConversationMessage, ConversationChunk,
        Dictionary, DictionaryItem, UserLevelModel, QuickEntry, Inspiration,
        RechargePackage  # noqa: F401
    )
    
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    关闭数据库连接
    在应用关闭时调用
    """
    global engine
    
    if engine:
        logger.info("Closing database connection...")
        await engine.dispose()
        logger.info("Database connection closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖项
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

