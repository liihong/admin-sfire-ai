"""
管理员操作日志服务
用于记录和查询管理员操作日志
"""
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import json

from models.admin_operation_log import AdminOperationLog, OperationType


class OperationLogService:
    """操作日志服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(
        self,
        admin_user_id: int,
        user_id: int,
        operation_type: str,
        operation_detail: Optional[Dict[str, Any]] = None,
        remark: Optional[str] = None,
    ) -> AdminOperationLog:
        """
        创建操作日志
        
        Args:
            admin_user_id: 操作管理员ID
            user_id: 目标用户ID
            operation_type: 操作类型
            operation_detail: 操作详情（字典，会自动转为JSON）
            remark: 备注
        
        Returns:
            创建的操作日志对象
        """
        log = AdminOperationLog(
            admin_user_id=admin_user_id,
            user_id=user_id,
            operation_type=operation_type,
            operation_detail=json.dumps(operation_detail, ensure_ascii=False) if operation_detail else None,
            remark=remark,
        )
        
        self.db.add(log)
        # 注意：不在这里 commit，交给调用方处理事务
        
        logger.info(
            f"操作日志已创建: admin_user_id={admin_user_id}, "
            f"user_id={user_id}, operation_type={operation_type}"
        )
        
        return log
    
    async def get_logs_by_user(
        self,
        user_id: int,
        limit: int = 50,
    ) -> List[AdminOperationLog]:
        """
        获取指定用户的操作日志
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
        
        Returns:
            操作日志列表
        """
        query = (
            select(AdminOperationLog)
            .where(AdminOperationLog.user_id == user_id)
            .order_by(desc(AdminOperationLog.created_at))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_logs_by_admin(
        self,
        admin_user_id: int,
        limit: int = 50,
    ) -> List[AdminOperationLog]:
        """
        获取指定管理员的操作日志
        
        Args:
            admin_user_id: 管理员ID
            limit: 返回数量限制
        
        Returns:
            操作日志列表
        """
        query = (
            select(AdminOperationLog)
            .where(AdminOperationLog.admin_user_id == admin_user_id)
            .order_by(desc(AdminOperationLog.created_at))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())








