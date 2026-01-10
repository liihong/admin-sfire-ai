"""
火源币账户管理服务
实现算力的冻结、扣除、退还等核心操作
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger

from models.user import User
from models.compute import ComputeLog, ComputeType
from services.coin_calculator import CoinCalculatorService
from utils.exceptions import BadRequestException, NotFoundException


class CoinAccountService:
    """火源币账户管理服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = CoinCalculatorService(db)

    async def get_user_with_lock(self, user_id: int) -> User:
        """
        获取用户并加锁(防止并发问题)

        Args:
            user_id: 用户ID

        Returns:
            用户对象
        """
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()  # 行级锁,防止并发修改
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"用户ID {user_id} 不存在")

        return user

    async def check_balance(
        self,
        user_id: int,
        required_amount: Decimal
    ) -> bool:
        """
        检查余额是否充足

        Args:
            user_id: 用户ID
            required_amount: 需要的金额

        Returns:
            True-余额充足, False-余额不足
        """
        user = await self.get_user_with_lock(user_id)
        available = user.balance - user.frozen_balance

        return available >= required_amount

    async def freeze_amount(
        self,
        user_id: int,
        amount: Decimal,
        task_id: str,
        remark: Optional[str] = None
    ) -> None:
        """
        预冻结算力

        操作:
        - frozen_balance += amount
        - 创建 FREEZE 类型的流水记录

        Args:
            user_id: 用户ID
            amount: 冻结金额
            task_id: 关联任务ID
            remark: 备注
        """
        # 获取用户并加锁
        user = await self.get_user_with_lock(user_id)

        # 检查可用余额
        available = user.balance - user.frozen_balance
        if available < amount:
            raise BadRequestException(
                f"余额不足。可用余额: {available:.4f}, 需要: {amount:.4f}"
            )

        # 记录变动前余额
        before_balance = user.balance
        before_frozen = user.frozen_balance

        # 冻结金额
        user.frozen_balance += amount

        # 创建冻结流水记录
        log = ComputeLog(
            user_id=user_id,
            type=ComputeType.FREEZE,
            amount=amount,
            before_balance=before_balance,
            after_balance=user.balance,  # 总余额不变
            remark=remark or f"预冻结算力,任务ID: {task_id}",
            task_id=task_id,
            source="api"
        )
        self.db.add(log)

        # 立即刷新到数据库，确保后续查询能找到这条记录
        await self.db.flush()

        logger.info(
            f"用户 {user_id} 预冻结算力: {amount}, "
            f"冻结前: {before_frozen}, 冻结后: {user.frozen_balance}"
        )

    async def unfreeze_and_deduct(
        self,
        user_id: int,
        task_id: str,
        actual_cost: Decimal,
        input_tokens: int,
        output_tokens: int,
        model_id: int
    ) -> None:
        """
        解冻并扣除实际消耗

        操作:
        - 从 frozen_balance 中扣除预冻结金额
        - 从 balance 中扣除实际消耗
        - 退还差额 (预冻结金额 - 实际消耗) 到 balance
        - 创建 CONSUME 流水记录

        Args:
            user_id: 用户ID
            task_id: 关联任务ID
            actual_cost: 实际消耗金额
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
        """
        # 获取用户并加锁
        user = await self.get_user_with_lock(user_id)

        # 获取该任务的预冻结记录
        freeze_logs_result = await self.db.execute(
            select(ComputeLog)
            .where(
                ComputeLog.user_id == user_id,
                ComputeLog.task_id == task_id,
                ComputeLog.type == ComputeType.FREEZE
            )
            .order_by(ComputeLog.created_at.desc())
            .limit(1)
        )
        freeze_log = freeze_logs_result.scalar_one_or_none()

        if not freeze_log:
            logger.error(f"任务 {task_id} 没有找到预冻结记录")
            raise BadRequestException("任务状态异常,无法结算")

        frozen_amount = freeze_log.amount

        # 记录变动前余额
        before_balance = user.balance
        before_frozen = user.frozen_balance

        # 解冻
        user.frozen_balance -= frozen_amount

        # 扣除实际消耗
        user.balance -= actual_cost

        # 计算退还金额
        refund_amount = frozen_amount - actual_cost
        if refund_amount > 0:
            # 有剩余,退还到余额
            user.balance += refund_amount

        # 创建消耗流水
        remark = (
            f"AI对话消耗 - "
            f"输入Token: {input_tokens}, 输出Token: {output_tokens}, "
            f"模型ID: {model_id}"
        )

        consume_log = ComputeLog(
            user_id=user_id,
            type=ComputeType.CONSUME,
            amount=-actual_cost,  # 负数表示减少
            before_balance=before_balance,
            after_balance=user.balance,
            remark=remark,
            task_id=task_id,
            source="api"
        )
        self.db.add(consume_log)

        logger.info(
            f"用户 {user_id} 算力结算: "
            f"预冻结 {frozen_amount}, 实际消耗 {actual_cost}, "
            f"退还 {refund_amount}, 当前余额 {user.balance}"
        )

    async def refund_full(
        self,
        user_id: int,
        task_id: str,
        reason: str,
        error_code: Optional[int] = None
    ) -> None:
        """
        全额退还 (API错误时)

        操作:
        - frozen_balance -= 预冻结金额
        - balance += 预冻结金额 (全额退还)
        - 创建 REFUND 流水记录

        Args:
            user_id: 用户ID
            task_id: 关联任务ID
            reason: 退款原因
            error_code: 错误码(可选)
        """
        # 获取用户并加锁
        user = await self.get_user_with_lock(user_id)

        # 获取预冻结记录
        freeze_logs_result = await self.db.execute(
            select(ComputeLog)
            .where(
                ComputeLog.user_id == user_id,
                ComputeLog.task_id == task_id,
                ComputeLog.type == ComputeType.FREEZE
            )
            .order_by(ComputeLog.created_at.desc())
            .limit(1)
        )
        freeze_log = freeze_logs_result.scalar_one_or_none()

        if not freeze_log:
            logger.warning(f"任务 {task_id} 没有找到预冻结记录,跳过退款")
            return

        frozen_amount = freeze_log.amount

        # 记录变动前余额
        before_balance = user.balance
        before_frozen = user.frozen_balance

        # 解冻并退还
        user.frozen_balance -= frozen_amount
        user.balance += frozen_amount

        # 创建退款流水
        remark = f"全额退还 - {reason}"
        if error_code:
            remark += f" (错误码: {error_code})"

        refund_log = ComputeLog(
            user_id=user_id,
            type=ComputeType.REFUND,
            amount=frozen_amount,  # 正数表示增加
            before_balance=before_balance,
            after_balance=user.balance,
            remark=remark,
            task_id=task_id,
            source="api"
        )
        self.db.add(refund_log)

        logger.info(
            f"用户 {user_id} 全额退款: {frozen_amount}, 原因: {reason}"
        )

    async def deduct_violation_penalty(
        self,
        user_id: int,
        task_id: str,
        model_id: int
    ) -> None:
        """
        扣除违规处罚费用

        操作:
        - 仅扣除基础调度费的一定比例作为处罚
        - 退还其余预冻结金额
        - 创建 CONSUME 流水 (备注: 内容违规)

        Args:
            user_id: 用户ID
            task_id: 关联任务ID
            model_id: 模型ID
        """
        # 获取用户并加锁
        user = await self.get_user_with_lock(user_id)

        # 获取预冻结记录
        freeze_logs_result = await self.db.execute(
            select(ComputeLog)
            .where(
                ComputeLog.user_id == user_id,
                ComputeLog.task_id == task_id,
                ComputeLog.type == ComputeType.FREEZE
            )
            .order_by(ComputeLog.created_at.desc())
            .limit(1)
        )
        freeze_log = freeze_logs_result.scalar_one_or_none()

        if not freeze_log:
            logger.warning(f"任务 {task_id} 没有找到预冻结记录")
            return

        frozen_amount = freeze_log.amount

        # 计算处罚费用
        penalty = await self.calculator.calculate_violation_penalty(model_id)

        # 记录变动前余额
        before_balance = user.balance
        before_frozen = user.frozen_balance

        # 解冻
        user.frozen_balance -= frozen_amount

        # 扣除处罚费用
        user.balance -= penalty

        # 退还剩余部分
        refund_amount = frozen_amount - penalty
        if refund_amount > 0:
            user.balance += refund_amount

        # 创建消耗流水
        remark = f"内容违规处罚 - 模型ID: {model_id}"

        consume_log = ComputeLog(
            user_id=user_id,
            type=ComputeType.CONSUME,
            amount=-penalty,  # 负数表示减少
            before_balance=before_balance,
            after_balance=user.balance,
            remark=remark,
            task_id=task_id,
            source="api"
        )
        self.db.add(consume_log)

        logger.warning(
            f"用户 {user_id} 内容违规处罚: {penalty}, "
            f"预冻结 {frozen_amount}, 退还 {refund_amount}"
        )

    async def recharge(
        self,
        user_id: int,
        amount: Decimal,
        remark: Optional[str] = None,
        operator_id: Optional[int] = None,
        order_id: Optional[str] = None
    ) -> None:
        """
        充值算力

        Args:
            user_id: 用户ID
            amount: 充值金额
            remark: 备注
            operator_id: 操作人ID(管理员操作时)
            order_id: 订单ID
        """
        # 获取用户并加锁
        user = await self.get_user_with_lock(user_id)

        # 记录变动前余额
        before_balance = user.balance

        # 增加余额
        user.balance += amount

        # 创建充值流水
        recharge_log = ComputeLog(
            user_id=user_id,
            type=ComputeType.RECHARGE,
            amount=amount,  # 正数表示增加
            before_balance=before_balance,
            after_balance=user.balance,
            remark=remark or "算力充值",
            order_id=order_id,
            operator_id=operator_id,
            source="admin" if operator_id else "api"
        )
        self.db.add(recharge_log)

        logger.info(
            f"用户 {user_id} 充值成功: {amount}, "
            f"充值前: {before_balance}, 充值后: {user.balance}"
        )

    async def adjust(
        self,
        user_id: int,
        amount: Decimal,
        remark: str,
        operator_id: int
    ) -> None:
        """
        管理员调整算力

        Args:
            user_id: 用户ID
            amount: 调整金额(正数增加,负数减少)
            remark: 调整原因
            operator_id: 操作人ID
        """
        # 获取用户并加锁
        user = await self.get_user_with_lock(user_id)

        # 记录变动前余额
        before_balance = user.balance

        # 调整余额
        user.balance += amount

        # 创建调整流水
        adjust_log = ComputeLog(
            user_id=user_id,
            type=ComputeType.ADJUSTMENT,
            amount=amount,
            before_balance=before_balance,
            after_balance=user.balance,
            remark=remark,
            operator_id=operator_id,
            source="admin"
        )
        self.db.add(adjust_log)

        logger.info(
            f"管理员 {operator_id} 调整用户 {user_id} 算力: {amount}, "
            f"调整前: {before_balance}, 调整后: {user.balance}, 原因: {remark}"
        )

    async def get_user_balance(self, user_id: int) -> dict:
        """
        获取用户余额信息

        Args:
            user_id: 用户ID

        Returns:
            余额信息字典
        """
        user = await self.get_user_with_lock(user_id)

        return {
            "balance": user.balance,
            "frozen_balance": user.frozen_balance,
            "available_balance": user.balance - user.frozen_balance,
        }
