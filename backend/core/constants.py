"""
全局常量（与业务约定相关）
"""
from typing import Optional

# 后台「系统管理员」角色主键：与未绑定 role_id 一样，加载全部菜单
SYSTEM_ADMIN_ROLE_ID = 1


def is_full_menu_role(role_id: Optional[int]) -> bool:
    """未绑定角色或系统管理员角色时返回全部菜单树"""
    return role_id is None or role_id == SYSTEM_ADMIN_ROLE_ID
