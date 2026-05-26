"""
全局常量（与业务约定相关）
"""
from typing import Optional

# 后台「系统管理员」角色主键
SYSTEM_ADMIN_ROLE_ID = 1

# 仅平台超级管理员可见的菜单根节点 name（menus.name）
PLATFORM_MENU_ROOT_NAME = "system"


def is_full_menu_role(role_id: Optional[int]) -> bool:
    """未绑定角色或系统管理员角色（用于判断是否按「全量业务菜单」策略处理）"""
    return role_id is None or role_id == SYSTEM_ADMIN_ROLE_ID


def admin_gets_unfiltered_menu_tree(*, tenant_id: Optional[int], role_id: Optional[int]) -> bool:
    """
    是否不经 menu_ids 过滤、直接加载全部启用菜单。

    仅平台超级管理员（tenant_id 为空）且为系统管理员角色时为 True。
    已绑定租户的管理员即使 role_id=1，也不得看到「系统管理」等平台级菜单模块。
    """
    return admin_has_platform_privilege(tenant_id=tenant_id, role_id=role_id) and is_full_menu_role(
        role_id
    )


def admin_has_platform_privilege(*, tenant_id: Optional[int], role_id: Optional[int]) -> bool:
    """
    是否具备「平台级」后台权限（跨租户管理租户、查看全量数据等）。

    仅当 admin_users.tenant_id 为空时视为平台超级管理员。
    已绑定任意租户（含主租户、dingma 等）的管理员，无论角色是否为「系统管理员」，
    数据范围均以该 tenant_id 为准，不会看到其它租户或全平台数据。
    """
    _ = role_id  # 保留签名兼容调用方，不再参与判定
    return tenant_id is None


def admin_data_scope_tenant_id(*, tenant_id: Optional[int], role_id: Optional[int]) -> Optional[int]:
    """
    B 端传给 Service 的 scoped_tenant_id（列表过滤 / 创建写入归属 / 更新校验）。

    - 返回 None：平台视角 —— 不按租户过滤列表；创建管理员/C 端用户时可使用请求体中的 tenant_id。
    - 返回具体 id：租户管理员 —— 仅能访问、写入该租户。
    """
    if admin_has_platform_privilege(tenant_id=tenant_id, role_id=role_id):
        return None
    return tenant_id
