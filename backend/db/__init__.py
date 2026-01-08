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

# 注意：不在这里导入 models，以避免循环导入
# models 模块在初始化时会导入 db.session.Base
# 如果在 db/__init__.py 中导入 models，会形成循环依赖
# Alembic 可以通过其他方式检测模型（通过 env.py 中的导入）
# 如果需要导入模型，请在函数内部进行延迟导入

__all__ = [
    "get_db",
    "init_db",
    "close_db",
    "create_tables",
    "async_session_maker",
    "Base",
]

