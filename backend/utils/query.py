"""
通用查询工具函数
提供统一的数据库查询辅助函数，减少重复代码
"""
from typing import TypeVar, Optional, Type, List, Dict, Any, Callable
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from utils.exceptions import NotFoundException, BadRequestException

T = TypeVar("T", bound=DeclarativeBase)


async def get_by_id(
    db: AsyncSession,
    model: Type[T],
    obj_id: int,
    error_msg: str = "资源不存在",
    check_soft_delete: bool = False,
    exclude_id: Optional[int] = None,
) -> Optional[T]:
    """
    根据ID获取模型对象
    
    Args:
        db: 数据库会话
        model: 模型类
        obj_id: 对象ID
        error_msg: 不存在时的错误消息
        check_soft_delete: 是否检查软删除标记（要求模型有 is_deleted 字段）
        exclude_id: 排除的ID（用于更新时的唯一性检查）
    
    Returns:
        模型对象，如果不存在且未指定错误消息则返回 None
    
    Raises:
        NotFoundException: 对象不存在时抛出
    """
    query = select(model).where(model.id == obj_id)
    
    # 检查软删除
    if check_soft_delete and hasattr(model, "is_deleted"):
        query = query.where(model.is_deleted == False)
    
    # 排除指定ID（用于更新时的冲突检查）
    if exclude_id is not None:
        query = query.where(model.id != exclude_id)
    
    result = await db.execute(query)
    obj = result.scalar_one_or_none()
    
    if obj is None and error_msg:
        raise NotFoundException(msg=error_msg)
    
    return obj


async def check_unique(
    db: AsyncSession,
    model: Type[T],
    field_name: str,
    value: Any,
    error_msg: str,
    exclude_id: Optional[int] = None,
    check_soft_delete: bool = False,
) -> None:
    """
    检查字段唯一性
    
    Args:
        db: 数据库会话
        model: 模型类
        field_name: 字段名
        value: 字段值
        error_msg: 冲突时的错误消息
        exclude_id: 排除的ID（用于更新时的检查）
        check_soft_delete: 是否检查软删除标记
    
    Raises:
        BadRequestException: 字段值已存在时抛出
    """
    if value is None:
        return
    
    if not hasattr(model, field_name):
        raise ValueError(f"Model {model.__name__} has no field '{field_name}'")
    
    field = getattr(model, field_name)
    query = select(model).where(field == value)
    
    # 检查软删除
    if check_soft_delete and hasattr(model, "is_deleted"):
        query = query.where(model.is_deleted == False)
    
    # 排除指定ID
    if exclude_id is not None:
        query = query.where(model.id != exclude_id)
    
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise BadRequestException(msg=error_msg)


def build_soft_delete_condition(model: Type[T]) -> List:
    """
    构建软删除查询条件
    
    Args:
        model: 模型类
    
    Returns:
        条件列表，如果模型没有 is_deleted 字段则返回空列表
    """
    if hasattr(model, "is_deleted"):
        return [model.is_deleted == False]
    return []


def apply_conditions(
    query,
    conditions: List,
) -> Any:
    """
    应用查询条件到查询对象
    
    Args:
        query: SQLAlchemy 查询对象
        conditions: 条件列表
    
    Returns:
        应用条件后的查询对象
    """
    if conditions:
        return query.where(and_(*conditions))
    return query


async def check_multiple_unique(
    db: AsyncSession,
    model: Type[T],
    field_checks: Dict[str, Dict[str, Any]],
    exclude_id: Optional[int] = None,
    check_soft_delete: bool = False,
) -> None:
    """
    批量检查多个字段的唯一性
    
    Args:
        db: 数据库会话
        model: 模型类
        field_checks: 字段检查字典，格式: {
            "field_name": {"value": value, "error_msg": "错误消息"}
        }
        exclude_id: 排除的ID
        check_soft_delete: 是否检查软删除标记
    
    Raises:
        BadRequestException: 任一字段冲突时抛出
    
    Example:
        ```python
        await check_multiple_unique(
            db=db,
            model=User,
            field_checks={
                "username": {"value": "test", "error_msg": "用户名已存在"},
                "email": {"value": "test@example.com", "error_msg": "邮箱已被注册"},
            },
            exclude_id=current_user_id,
        )
        ```
    """
    for field_name, check_info in field_checks.items():
        value = check_info.get("value")
        error_msg = check_info.get("error_msg", f"{field_name}已存在")
        
        await check_unique(
            db=db,
            model=model,
            field_name=field_name,
            value=value,
            error_msg=error_msg,
            exclude_id=exclude_id,
            check_soft_delete=check_soft_delete,
        )































