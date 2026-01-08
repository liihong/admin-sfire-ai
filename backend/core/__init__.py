"""
Core module - Configuration and Security
"""
from .config import settings

# 注意：不在这里导入 deps 模块，以避免循环导入
# db 模块在初始化时会导入 core.config，如果在 core/__init__.py 中导入 core.deps
# 而 core.deps 需要从 db 导入 get_db，会形成循环依赖
# 如果需要使用这些依赖项，请直接从 core.deps 导入：
#   from core.deps import get_current_user, get_current_admin, etc.

__all__ = [
    "settings",
]






