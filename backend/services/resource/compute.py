"""
Compute Log Service
算力流水服务
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from loguru import logger

from models.user import User
from models.compute import ComputeLog, ComputeType
from schemas.compute import ComputeLogQueryParams
from utils.pagination import paginate, build_order_by, PageResult
from utils.exceptions import NotFoundException, BadRequestException


# 算力变动类型中文映射
COMPUTE_TYPE_NAMES = {
    ComputeType.RECHARGE: "充值",
    ComputeType.CONSUME: "消耗",
    ComputeType.REFUND: "退款",
    ComputeType.REWARD: "奖励",
    ComputeType.FREEZE: "冻结",
    ComputeType.UNFREEZE: "解冻",
    ComputeType.TRANSFER_IN: "转入",
    ComputeType.TRANSFER_OUT: "转出",
    ComputeType.COMMISSION: "分销佣金",
    ComputeType.ADJUSTMENT: "管理员调整",
}

# 算力变动类型颜色
COMPUTE_TYPE_COLORS = {
    ComputeType.RECHARGE: "#67C23A",    # 绿色-充值
    ComputeType.CONSUME: "#F56C6C",     # 红色-消耗
    ComputeType.REFUND: "#E6A23C",      # 橙色-退款
    ComputeType.REWARD: "#409EFF",      # 蓝色-奖励
    ComputeType.FREEZE: "#909399",      # 灰色-冻结
    ComputeType.UNFREEZE: "#909399",    # 灰色-解冻
    ComputeType.TRANSFER_IN: "#67C23A", # 绿色-转入
    ComputeType.TRANSFER_OUT: "#F56C6C",# 红色-转出
    ComputeType.COMMISSION: "#E6A23C",  # 橙色-佣金
    ComputeType.ADJUSTMENT: "#909399",  # 灰色-调整
}


class ComputeService:
    """算力流水服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _format_log_response(self, log: ComputeLog, user: Optional[User] = None) -> dict:
        """格式化算力流水响应数据"""
        return {
            "id": str(log.id),
            "userId": str(log.user_id),
            "username": user.username if user else None,
            "type": log.type.value,
            "typeName": COMPUTE_TYPE_NAMES.get(log.type, "未知"),
            "amount": float(log.amount),
            "beforeBalance": float(log.before_balance),
            "afterBalance": float(log.after_balance),
            "remark": log.remark,
            "orderId": log.order_id,
            "taskId": log.task_id,
            "operatorId": str(log.operator_id) if log.operator_id else None,
            "operatorName": None,  # TODO: 关联查询操作人
            "source": log.source,
            "createTime": log.created_at.isoformat() if log.created_at else None,
        }
    
    async def get_compute_logs(
        self,
        params: ComputeLogQueryParams
    ) -> PageResult:
        """
        获取算力流水列表
        
        Args:
            params: 查询参数
        
        Returns:
            分页结果
        """
        # 构建查询条件
        conditions = []
        
        # 按用户ID过滤
        if params.userId:
            conditions.append(ComputeLog.user_id == int(params.userId))
        
        # 按类型过滤
        if params.type:
            compute_type = ComputeType(params.type)
            conditions.append(ComputeLog.type == compute_type)
        
        # 按金额范围过滤
        if params.minAmount is not None:
            conditions.append(ComputeLog.amount >= params.minAmount)
        if params.maxAmount is not None:
            conditions.append(ComputeLog.amount <= params.maxAmount)
        
        # 按时间范围过滤
        if params.startTime:
            try:
                start_dt = datetime.fromisoformat(params.startTime.replace("Z", "+00:00"))
                conditions.append(ComputeLog.created_at >= start_dt)
            except ValueError:
                pass
        
        if params.endTime:
            try:
                end_dt = datetime.fromisoformat(params.endTime.replace("Z", "+00:00"))
                conditions.append(ComputeLog.created_at <= end_dt)
            except ValueError:
                pass
        
        # 查询总数
        count_query = select(func.count(ComputeLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据（带用户信息）
        query = (
            select(ComputeLog, User)
            .outerjoin(User, ComputeLog.user_id == User.id)
        )
        if conditions:
            query = query.where(and_(*conditions))
        
        # 如果按用户名模糊查询
        if params.username:
            query = query.where(User.username.like(f"%{params.username}%"))
            # 重新计算总数
            count_query = (
                select(func.count(ComputeLog.id))
                .outerjoin(User, ComputeLog.user_id == User.id)
                .where(User.username.like(f"%{params.username}%"))
            )
            if conditions:
                count_query = count_query.where(and_(*conditions))
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
        
        query = query.order_by(ComputeLog.created_at.desc())
        query = query.offset(params.offset).limit(params.pageSize)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # 格式化响应
        log_list = [
            self._format_log_response(log, user) 
            for log, user in rows
        ]
        
        return PageResult(
            list=log_list,
            total=total,
            pageNum=params.pageNum,
            pageSize=params.pageSize,
        )
    
    async def get_user_compute_logs(
        self,
        user_id: int,
        page_num: int = 1,
        page_size: int = 10,
        log_type: Optional[str] = None,
    ) -> PageResult:
        """
        获取指定用户的算力流水
        
        Args:
            user_id: 用户ID
            page_num: 页码
            page_size: 每页数量
            log_type: 流水类型
        
        Returns:
            分页结果
        """
        conditions = [ComputeLog.user_id == user_id]
        
        if log_type:
            compute_type = ComputeType(log_type)
            conditions.append(ComputeLog.type == compute_type)
        
        # 过滤掉充值失败的订单和待支付的订单
        # 条件：
        # 1. 不是充值类型，保留
        # 2. 是充值类型：
        #    - 系统充值（有 operator_id），保留（无论 payment_status 是什么）
        #    - 用户支付订单（无 operator_id），只保留已支付的（payment_status 为 paid 或 None）
        conditions.append(
            or_(
                ComputeLog.type != ComputeType.RECHARGE,  # 不是充值类型，保留
                and_(
                    ComputeLog.type == ComputeType.RECHARGE,  # 是充值类型
                    or_(
                        ComputeLog.operator_id.isnot(None),  # 系统充值（有操作人），保留
                        and_(
                            ComputeLog.operator_id.is_(None),  # 用户支付订单（无操作人）
                            or_(
                                ComputeLog.payment_status.is_(None),  # payment_status 为 None（兼容旧数据）
                                ComputeLog.payment_status == "paid"  # 已支付
                            )
                        )
                    )
                )
            )
        )
        
        # 获取用户信息
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        result = await paginate(
            db=self.db,
            model=ComputeLog,
            conditions=conditions,
            order_by=ComputeLog.created_at.desc(),
            page_num=page_num,
            page_size=page_size,
            formatter=lambda log: self._format_log_response(log, user),
        )
        
        return result
    
    async def create_compute_log(
        self,
        user_id: int,
        log_type: ComputeType,
        amount: Decimal,
        before_balance: Decimal,
        after_balance: Decimal,
        remark: Optional[str] = None,
        order_id: Optional[str] = None,
        task_id: Optional[str] = None,
        operator_id: Optional[int] = None,
        source: str = "admin",
    ) -> ComputeLog:
        """
        创建算力流水记录
        
        Args:
            user_id: 用户ID
            log_type: 变动类型
            amount: 变动金额
            before_balance: 变动前余额
            after_balance: 变动后余额
            remark: 备注
            order_id: 关联订单ID
            task_id: 关联任务ID
            operator_id: 操作人ID
            source: 来源
        
        Returns:
            创建的流水记录
        """
        log = ComputeLog(
            user_id=user_id,
            type=log_type,
            amount=amount,
            before_balance=before_balance,
            after_balance=after_balance,
            remark=remark,
            order_id=order_id,
            task_id=task_id,
            operator_id=operator_id,
            source=source,
        )
        
        self.db.add(log)
        # 注意：这里不 commit，交给调用方处理事务
        
        return log
    
    async def get_type_options(self) -> List[dict]:
        """获取算力变动类型选项"""
        options = []
        for compute_type in ComputeType:
            options.append({
                "label": COMPUTE_TYPE_NAMES.get(compute_type, compute_type.value),
                "value": compute_type.value,
                "color": COMPUTE_TYPE_COLORS.get(compute_type, "#909399"),
            })
        return options
    
    async def get_user_statistics(self, user_id: int) -> dict:
        """
        获取用户算力统计信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            统计信息
        """
        # 按类型分组统计
        query = (
            select(
                ComputeLog.type,
                func.sum(ComputeLog.amount).label("total")
            )
            .where(ComputeLog.user_id == user_id)
            .group_by(ComputeLog.type)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        statistics = {
            "totalRecharge": Decimal("0"),
            "totalConsume": Decimal("0"),
            "totalRefund": Decimal("0"),
            "totalReward": Decimal("0"),
            "totalCommission": Decimal("0"),
            "totalAdjustment": Decimal("0"),
        }
        
        type_mapping = {
            ComputeType.RECHARGE: "totalRecharge",
            ComputeType.CONSUME: "totalConsume",
            ComputeType.REFUND: "totalRefund",
            ComputeType.REWARD: "totalReward",
            ComputeType.COMMISSION: "totalCommission",
            ComputeType.ADJUSTMENT: "totalAdjustment",
        }
        
        for log_type, total in rows:
            key = type_mapping.get(log_type)
            if key:
                statistics[key] = total or Decimal("0")
        
        return statistics





