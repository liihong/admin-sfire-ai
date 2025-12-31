"""
通用分页查询工具
适配 Geeker-Admin ProTable 分页格式
"""
from typing import Any, TypeVar, Generic, List, Tuple, Optional, Callable
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, Field

T = TypeVar("T", bound=DeclarativeBase)


class PaginationParams(BaseModel):
    """分页参数"""
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.pageNum - 1) * self.pageSize


class SortParams(BaseModel):
    """排序参数"""
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[str] = Field(default="desc", description="排序方向: asc/desc")


class PageResult(BaseModel, Generic[T]):
    """
    分页结果
    
    适配 Geeker-Admin ProTable 格式：
    {
        "list": [...],
        "total": 100,
        "pageNum": 1,
        "pageSize": 10
    }
    """
    list: List[Any] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数量")
    pageNum: int = Field(default=1, description="当前页码")
    pageSize: int = Field(default=10, description="每页数量")
    
    @property
    def pages(self) -> int:
        """计算总页数"""
        if self.pageSize <= 0:
            return 0
        return (self.total + self.pageSize - 1) // self.pageSize
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.pageNum < self.pages
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.pageNum > 1


async def paginate(
    db: AsyncSession,
    model: type[T],
    conditions: List = None,
    order_by: Any = None,
    page_num: int = 1,
    page_size: int = 10,
    formatter: Optional[Callable[[T], dict]] = None,
) -> PageResult:
    """
    通用分页查询函数
    
    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        conditions: 查询条件列表
        order_by: 排序字段（如 Model.created_at.desc()）
        page_num: 页码
        page_size: 每页数量
        formatter: 数据格式化函数
    
    Returns:
        PageResult: 分页结果
    
    Example:
        ```python
        # 基本使用
        result = await paginate(
            db=db,
            model=User,
            conditions=[User.is_deleted == False],
            order_by=User.created_at.desc(),
            page_num=1,
            page_size=10,
        )
        
        # 带格式化函数
        result = await paginate(
            db=db,
            model=User,
            conditions=[User.is_active == True],
            order_by=User.id.desc(),
            page_num=1,
            page_size=10,
            formatter=lambda u: {"id": u.id, "name": u.username}
        )
        ```
    """
    conditions = conditions or []
    
    # 查询总数
    count_query = select(func.count(model.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 查询数据
    query = select(model)
    if conditions:
        query = query.where(and_(*conditions))
    
    # 排序
    if order_by is not None:
        query = query.order_by(order_by)
    
    # 分页
    offset = (page_num - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # 格式化数据
    if formatter:
        item_list = [formatter(item) for item in items]
    else:
        item_list = list(items)
    
    return PageResult(
        list=item_list,
        total=total,
        pageNum=page_num,
        pageSize=page_size,
    )


async def paginate_query(
    db: AsyncSession,
    query,
    count_query,
    page_num: int = 1,
    page_size: int = 10,
    formatter: Optional[Callable] = None,
) -> PageResult:
    """
    自定义查询的分页函数
    
    用于复杂查询场景，允许传入自定义的查询和计数查询
    
    Args:
        db: 数据库会话
        query: 主查询（select 语句）
        count_query: 计数查询
        page_num: 页码
        page_size: 每页数量
        formatter: 数据格式化函数
    
    Returns:
        PageResult: 分页结果
    """
    # 查询总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    offset = (page_num - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # 格式化数据
    if formatter:
        item_list = [formatter(item) for item in items]
    else:
        item_list = list(items)
    
    return PageResult(
        list=item_list,
        total=total,
        pageNum=page_num,
        pageSize=page_size,
    )


def build_order_by(
    model: type,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    default_field: str = "created_at",
):
    """
    构建排序条件
    
    Args:
        model: SQLAlchemy 模型类
        sort_by: 排序字段名
        sort_order: 排序方向 (asc/desc)
        default_field: 默认排序字段
    
    Returns:
        排序表达式
    """
    field_name = sort_by if sort_by and hasattr(model, sort_by) else default_field
    field = getattr(model, field_name, None)
    
    if field is None:
        return None
    
    if sort_order.lower() == "asc":
        return asc(field)
    return desc(field)


def build_like_conditions(
    model: type,
    field_mappings: dict[str, Any],
) -> List:
    """
    构建模糊查询条件
    
    Args:
        model: SQLAlchemy 模型类
        field_mappings: {字段名: 查询值} 映射
    
    Returns:
        条件列表
    
    Example:
        ```python
        conditions = build_like_conditions(
            model=User,
            field_mappings={"username": "test", "phone": "138"}
        )
        # 返回: [User.username.like("%test%"), User.phone.like("%138%")]
        ```
    """
    conditions = []
    for field_name, value in field_mappings.items():
        if value is not None and hasattr(model, field_name):
            field = getattr(model, field_name)
            conditions.append(field.like(f"%{value}%"))
    return conditions


def build_exact_conditions(
    model: type,
    field_mappings: dict[str, Any],
) -> List:
    """
    构建精确匹配条件
    
    Args:
        model: SQLAlchemy 模型类
        field_mappings: {字段名: 查询值} 映射
    
    Returns:
        条件列表
    """
    conditions = []
    for field_name, value in field_mappings.items():
        if value is not None and hasattr(model, field_name):
            field = getattr(model, field_name)
            conditions.append(field == value)
    return conditions


