"""
Database module - Session and connection management
"""
from .session import (
    get_db,
    init_db,
    close_db,
    create_tables,
    async_session_maker,
    Base,
)

# 导入所有模型以便 Alembic 能够检测到
# 这也确保了在 init_db() 时所有表都会被创建
from app.models import (  # noqa: F401
    User,
    UserLevel,
    ComputeLog,
    ComputeType,
)

__all__ = [
    "get_db",
    "init_db",
    "close_db",
    "create_tables",
    "async_session_maker",
    "Base",
    "User",
    "UserLevel",
    "ComputeLog",
    "ComputeType",
]

