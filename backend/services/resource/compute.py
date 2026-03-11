"""
Compute Log Service
算力流水服务
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

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
        # 充值类型时，金额列显示支付金额（元）；其他类型显示算力变动
        display_amount = float(log.amount)
        payment_amount = float(log.payment_amount) if log.payment_amount is not None else None
        return {
            "id": str(log.id),
            "userId": str(log.user_id),
            "username": user.username if user else None,
            "type": log.type.value,
            "typeName": COMPUTE_TYPE_NAMES.get(log.type, "未知"),
            "amount": display_amount,
            "paymentAmount": payment_amount,  # 充值时的支付金额（元），非充值时为 None
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
            统计信息（含算力余额、流水汇总）
        """
        # 1. 查询用户当前算力余额（User 表）
        user_result = await self.db.execute(
            select(User.balance, User.frozen_balance).where(User.id == user_id)
        )
        user_row = user_result.one_or_none()
        if user_row:
            balance = user_row[0] or Decimal("0")
            frozen_balance = user_row[1] or Decimal("0")
            available_balance = balance - frozen_balance
        else:
            balance = frozen_balance = available_balance = Decimal("0")

        # 2. 按类型分组统计流水
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
            "balance": float(balance),
            "frozenBalance": float(frozen_balance),
            "availableBalance": float(available_balance),
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
        
        # 统一转为 float，便于 JSON 序列化
        for key in type_mapping.values():
            val = statistics[key]
            statistics[key] = float(val) if isinstance(val, Decimal) else val
        
        return statistics

    def _recharge_valid_condition(self):
        """
        充值有效条件：排除未支付订单
        - 系统充值（有 operator_id）保留
        - 用户支付订单：仅保留已支付（payment_status 为 paid 或 None）
        """
        return or_(
            ComputeLog.operator_id.isnot(None),
            ComputeLog.payment_status.is_(None),
            ComputeLog.payment_status == "paid",
        )

    async def get_system_statistics(self) -> dict:
        """
        获取系统级算力统计
        
        Returns:
            totalConsume: 系统总消耗（正数）
            totalRecharge: 系统总充值（正数，仅统计有效充值）
        """
        # 总消耗：CONSUME 类型，取绝对值求和
        consume_result = await self.db.execute(
            select(func.coalesce(func.sum(func.abs(ComputeLog.amount)), 0)).where(
                ComputeLog.type == ComputeType.CONSUME
            )
        )
        total_consume = consume_result.scalar() or Decimal("0")

        # 总充值：RECHARGE 类型，仅统计有效充值
        recharge_conditions = [
            ComputeLog.type == ComputeType.RECHARGE,
            self._recharge_valid_condition(),
        ]
        recharge_result = await self.db.execute(
            select(func.coalesce(func.sum(ComputeLog.amount), 0)).where(
                and_(*recharge_conditions)
            )
        )
        total_recharge = recharge_result.scalar() or Decimal("0")
        # 充值 amount 为正数，直接使用

        return {
            "totalConsume": float(total_consume),
            "totalRecharge": float(total_recharge),
        }

    async def get_user_summary_list(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """
        获取用户算力汇总列表（按用户分组统计消耗与充值）
        
        Args:
            page_num: 页码
            page_size: 每页数量
            username: 用户名模糊搜索
            start_time: 开始时间（ISO 格式）
            end_time: 结束时间（ISO 格式）
        
        Returns:
            (列表数据, 总数)
        """
        # 时间条件
        time_cond = []
        if start_time:
            try:
                time_cond.append(ComputeLog.created_at >= datetime.fromisoformat(start_time.replace("Z", "+00:00")))
            except ValueError:
                pass
        if end_time:
            try:
                time_cond.append(ComputeLog.created_at <= datetime.fromisoformat(end_time.replace("Z", "+00:00")))
            except ValueError:
                pass

        # 消耗子查询
        consume_cond = [ComputeLog.type == ComputeType.CONSUME]
        if time_cond:
            consume_cond.extend(time_cond)
        consume_subq = (
            select(
                ComputeLog.user_id,
                func.coalesce(func.sum(func.abs(ComputeLog.amount)), 0).label("totalConsume"),
            )
            .where(and_(*consume_cond))
            .group_by(ComputeLog.user_id)
        ).subquery()

        # 充值子查询（仅有效充值）
        recharge_cond = [
            ComputeLog.type == ComputeType.RECHARGE,
            self._recharge_valid_condition(),
        ]
        if time_cond:
            recharge_cond.extend(time_cond)
        recharge_subq = (
            select(
                ComputeLog.user_id,
                func.coalesce(func.sum(ComputeLog.amount), 0).label("totalRecharge"),
            )
            .where(and_(*recharge_cond))
            .group_by(ComputeLog.user_id)
        ).subquery()

        # 主查询：从消耗或充值中有记录的用户出发，左连接两个子查询和 User
        from sqlalchemy import union
        user_ids_consume = select(ComputeLog.user_id).where(ComputeLog.type == ComputeType.CONSUME).distinct()
        user_ids_recharge = select(ComputeLog.user_id).where(
            and_(ComputeLog.type == ComputeType.RECHARGE, self._recharge_valid_condition())
        ).distinct()
        if time_cond:
            user_ids_consume = user_ids_consume.where(and_(*time_cond))
            user_ids_recharge = user_ids_recharge.where(and_(*time_cond))
        user_ids_union = union(user_ids_consume, user_ids_recharge).subquery()

        # 关联消耗、充值、用户信息
        query = (
            select(
                user_ids_union.c.user_id,
                func.coalesce(consume_subq.c.totalConsume, 0).label("totalConsume"),
                func.coalesce(recharge_subq.c.totalRecharge, 0).label("totalRecharge"),
                User.username,
                User.phone,
            )
            .outerjoin(consume_subq, user_ids_union.c.user_id == consume_subq.c.user_id)
            .outerjoin(recharge_subq, user_ids_union.c.user_id == recharge_subq.c.user_id)
            .outerjoin(User, user_ids_union.c.user_id == User.id)
        )
        if username:
            query = query.where(User.username.like(f"%{username}%"))

        # 总数（先执行 count 子查询）
        count_subq = query.subquery()
        count_result = await self.db.execute(select(func.count()).select_from(count_subq))
        total = count_result.scalar() or 0

        # 分页数据，按总消耗降序
        query = (
            query.order_by(func.coalesce(consume_subq.c.totalConsume, 0).desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for row in rows:
            user_id, total_consume, total_recharge, row_username, row_phone = (
                row[0], row[1], row[2], row[3], row[4]
            )
            items.append({
                "userId": str(user_id),
                "username": row_username,
                "phone": row_phone,
                "totalConsume": float(total_consume or 0),
                "totalRecharge": float(total_recharge or 0),
            })
        return items, total





