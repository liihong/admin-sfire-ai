"""
Base Service Class
通用服务基类，提供 CRUD 操作的通用实现
"""
from typing import TypeVar, Type, Optional, Dict, Any, List, Tuple, Callable
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel as PydanticBaseModel
from loguru import logger

from utils.exceptions import NotFoundException, BadRequestException
from utils.query import (
    get_by_id,
    check_unique,
    check_multiple_unique,
    build_soft_delete_condition,
    apply_conditions,
)

T = TypeVar("T", bound=DeclarativeBase)
CreateSchema = TypeVar("CreateSchema", bound=PydanticBaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=PydanticBaseModel)


class BaseService:
    """
    基础服务类
    
    提供通用的 CRUD 操作方法，子类可以覆盖以实现自定义逻辑
    
    使用示例:
        ```python
        class UserService(BaseService[User, UserCreate, UserUpdate]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, User, "用户")
                self.model = User
                self.check_soft_delete = True
            
            def _format_response(self, obj: User) -> dict:
                # 自定义响应格式化
                return {"id": obj.id, "username": obj.username}
        ```
    """
    
    def __init__(
        self,
        db: AsyncSession,
        model: Type[T],
        resource_name: str = "资源",
        check_soft_delete: bool = False,
    ):
        """
        初始化服务
        
        Args:
            db: 数据库会话
            model: 模型类
            resource_name: 资源名称（用于错误消息）
            check_soft_delete: 是否使用软删除
        """
        self.db = db
        self.model = model
        self.resource_name = resource_name
        self.check_soft_delete = check_soft_delete
    
    async def get_by_id(
        self,
        obj_id: int,
        error_msg: Optional[str] = None,
        include_relations: Optional[List] = None,
    ) -> T:
        """
        根据ID获取对象
        
        Args:
            obj_id: 对象ID
            error_msg: 自定义错误消息
            include_relations: 需要预加载的关系列表
        
        Returns:
            模型对象
        
        Raises:
            NotFoundException: 对象不存在时抛出
        """
        if error_msg is None:
            error_msg = f"{self.resource_name}不存在"
        
        query = select(self.model).where(self.model.id == obj_id)
        
        # 应用软删除条件
        if self.check_soft_delete:
            conditions = build_soft_delete_condition(self.model)
            query = apply_conditions(query, conditions)
        
        # 预加载关系
        if include_relations:
            from sqlalchemy.orm import selectinload
            for relation in include_relations:
                query = query.options(selectinload(relation))
        
        result = await self.db.execute(query)
        obj = result.scalar_one_or_none()
        
        if obj is None:
            raise NotFoundException(msg=error_msg)
        
        return obj
    
    async def create(
        self,
        data: CreateSchema,
        unique_fields: Optional[Dict[str, Dict[str, Any]]] = None,
        before_create: Optional[Callable[[T, CreateSchema], None]] = None,
        after_create: Optional[Callable[[T], None]] = None,
    ) -> T:
        """
        创建对象
        
        Args:
            data: 创建数据（Pydantic Schema）
            unique_fields: 唯一性检查字段，格式: {
                "field_name": {"error_msg": "错误消息"}
            }
            before_create: 创建前的钩子函数，可以修改对象
            after_create: 创建后的钩子函数
        
        Returns:
            创建的对象
        """
        # 检查唯一性
        if unique_fields:
            field_checks = {
                field: {
                    "value": getattr(data, field, None),
                    "error_msg": info.get("error_msg", f"{field}已存在"),
                }
                for field, info in unique_fields.items()
            }
            await check_multiple_unique(
                db=self.db,
                model=self.model,
                field_checks=field_checks,
                check_soft_delete=self.check_soft_delete,
            )
        
        # 创建对象
        obj_data = data.model_dump(exclude_unset=True)
        obj = self.model(**obj_data)
        
        # 调用创建前钩子
        if before_create:
            before_create(obj, data)
        
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        
        # 调用创建后钩子
        if after_create:
            after_create(obj)
        
        logger.info(f"{self.resource_name} created: {obj.id}")
        
        return obj
    
    async def update(
        self,
        obj_id: int,
        data: UpdateSchema,
        unique_fields: Optional[Dict[str, Dict[str, Any]]] = None,
        before_update: Optional[Callable[[T, UpdateSchema], None]] = None,
        after_update: Optional[Callable[[T], None]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> T:
        """
        更新对象
        
        Args:
            obj_id: 对象ID
            data: 更新数据（Pydantic Schema）
            unique_fields: 唯一性检查字段
            before_update: 更新前的钩子函数
            after_update: 更新后的钩子函数
            exclude_fields: 排除的字段列表（不会更新这些字段）
        
        Returns:
            更新后的对象
        """
        # 获取对象
        obj = await self.get_by_id(obj_id)
        
        # 检查唯一性（排除当前对象）
        if unique_fields:
            field_checks = {}
            for field, info in unique_fields.items():
                value = getattr(data, field, None)
                # 只检查有值的字段
                if value is not None and hasattr(data, field):
                    field_checks[field] = {
                        "value": value,
                        "error_msg": info.get("error_msg", f"{field}已存在"),
                    }
            
            if field_checks:
                await check_multiple_unique(
                    db=self.db,
                    model=self.model,
                    field_checks=field_checks,
                    exclude_id=obj_id,
                    check_soft_delete=self.check_soft_delete,
                )
        
        # 调用更新前钩子
        if before_update:
            before_update(obj, data)
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        if exclude_fields:
            update_data = {k: v for k, v in update_data.items() if k not in exclude_fields}
        
        for field, value in update_data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        
        await self.db.flush()
        await self.db.refresh(obj)
        
        # 调用更新后钩子
        if after_update:
            after_update(obj)
        
        logger.info(f"{self.resource_name} updated: {obj.id}")
        
        return obj
    
    async def delete(
        self,
        obj_id: int,
        hard_delete: bool = False,
        before_delete: Optional[Callable[[T], None]] = None,
    ) -> None:
        """
        删除对象
        
        Args:
            obj_id: 对象ID
            hard_delete: 是否硬删除（物理删除），默认软删除
            before_delete: 删除前的钩子函数（可以用于级联删除检查等）
        """
        obj = await self.get_by_id(obj_id)
        
        # 调用删除前钩子
        if before_delete:
            before_delete(obj)
        
        if hard_delete:
            await self.db.delete(obj)
            logger.info(f"{self.resource_name} deleted (hard): {obj.id}")
        else:
            if hasattr(obj, "is_deleted"):
                obj.is_deleted = True
                logger.info(f"{self.resource_name} deleted (soft): {obj.id}")
            else:
                # 如果没有软删除字段，使用硬删除
                await self.db.delete(obj)
                logger.info(f"{self.resource_name} deleted (hard, no soft delete): {obj.id}")
        
        await self.db.flush()
    
    async def change_status(
        self,
        obj_id: int,
        status: int,
        status_field: str = "is_active",
    ) -> T:
        """
        修改对象状态
        
        Args:
            obj_id: 对象ID
            status: 状态值（0或1）
            status_field: 状态字段名，默认为 "is_active"
        
        Returns:
            更新后的对象
        """
        obj = await self.get_by_id(obj_id)
        
        if not hasattr(obj, status_field):
            raise ValueError(f"Model {self.model.__name__} has no field '{status_field}'")
        
        setattr(obj, status_field, status == 1)
        await self.db.flush()
        await self.db.refresh(obj)
        
        status_text = "正常" if status == 1 else "封禁"
        logger.info(f"{self.resource_name} status changed: {obj.id} -> {status_text}")
        
        return obj
    
    async def get_list(
        self,
        conditions: Optional[List] = None,
        order_by: Optional[Any] = None,
        offset: int = 0,
        limit: int = 10,
        formatter: Optional[Callable[[T], Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取列表（带分页）
        
        Args:
            conditions: 查询条件列表
            order_by: 排序字段
            offset: 偏移量
            limit: 限制数量
            formatter: 数据格式化函数
        
        Returns:
            (对象列表, 总数量)
        """
        # 构建基础条件
        base_conditions = []
        
        # 添加软删除条件
        if self.check_soft_delete:
            base_conditions.extend(build_soft_delete_condition(self.model))
        
        # 添加自定义条件
        if conditions:
            base_conditions.extend(conditions)
        
        # 查询总数
        count_query = select(func.count(self.model.id))
        if base_conditions:
            count_query = count_query.where(and_(*base_conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model)
        if base_conditions:
            query = query.where(and_(*base_conditions))
        
        if order_by is not None:
            query = query.order_by(order_by)
        
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        # 格式化数据
        if formatter:
            item_list = [formatter(item) for item in items]
        else:
            item_list = [self._format_response(item) if hasattr(self, "_format_response") else item for item in items]
        
        return item_list, total
    
    def _format_response(self, obj: T) -> Dict[str, Any]:
        """
        格式化响应数据
        
        子类应该覆盖此方法以实现自定义格式化逻辑
        
        Args:
            obj: 模型对象
        
        Returns:
            格式化后的字典
        """
        # 默认实现：返回对象的所有属性
        return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}



