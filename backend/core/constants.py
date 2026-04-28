"""
全局常量（与业务约定相关）
"""
from typing import Optional

# 后台「系统管理员」角色主键：与未绑定 role_id 一样，加载全部菜单
SYSTEM_ADMIN_ROLE_ID = 1


def is_full_menu_role(role_id: Optional[int]) -> bool:
    """未绑定角色或系统管理员角色时返回全部菜单树"""
    return role_id is None or role_id == SYSTEM_ADMIN_ROLE_ID


def admin_has_platform_privilege(*, tenant_id: Optional[int], role_id: Optional[int]) -> bool:
    """
    是否具备「平台级」后台权限（跨租户管理租户、全局配置等）。

    - tenant_id 为空：显式平台管理员；
    - tenant_id 非空但 role_id 为系统管理员（SYSTEM_ADMIN_ROLE_ID）：兼容迁移后主租户 id 被回填的情况，
      与 is_full_menu_role 约定一致，仍视为平台超级管理员。
    """
    if tenant_id is None:
        return True
    if role_id == SYSTEM_ADMIN_ROLE_ID:
        return True
    return False
