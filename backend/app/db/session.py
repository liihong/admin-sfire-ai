"""
Database Session Management
"""
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

from app.core.config import settings


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
    
    engine = create_async_engine(
        settings.MYSQL_DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool if settings.APP_ENV == "testing" else None,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    logger.info("Database connection initialized successfully")


async def create_tables() -> None:
    """
    创建所有数据库表
    仅在开发环境使用，生产环境请使用 Alembic 迁移
    """
    global engine
    
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    # 导入所有模型确保它们被注册
    from app.models import User, ComputeLog, Menu  # noqa: F401
    
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

