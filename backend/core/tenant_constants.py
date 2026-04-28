"""
多租户常量：默认主租户 ID 与运行时解析

迁移后存量数据回填为 tenant_id = DEFAULT_TENANT_ID，
与 tenants 表中 is_default=true 的记录 id 保持一致（约定为 1）。
"""
from typing import Optional

DEFAULT_TENANT_ID: int = 1


def effective_tenant_id(value: Optional[int]) -> int:
    """
    将库中可能为空的 tenant_id（迁移前遗留）规整为主租户，
    读路径在未完成迁移的环境中也可容错。
    """
    if value is None:
        return DEFAULT_TENANT_ID
    return value
