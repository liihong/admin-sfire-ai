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
from db.session import async_session_maker


class CoinAccountService:
    """火源币账户管理服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = CoinCalculatorService(db)

    async def get_user_with_lock(self, user_id: int, skip_locked: bool = False) -> User:
        """
        获取用户并加锁(防止并发问题)

        Args:
            user_id: 用户ID
            skip_locked: 是否跳过已被锁定的记录(快速失败),用于避免长等待

        Returns:
            用户对象
        """
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update(skip_locked=skip_locked)  # 行级锁,防止并发修改
        )
        user = result.scalar_one_or_none()

        if not user:
            # 如果是 skip_locked 模式下没获取到,可能是锁冲突
            if skip_locked:
                from sqlalchemy.exc import OperationalError
                raise OperationalError(
                    "锁冲突，用户记录被其他事务占用",
                    orig=type('obj', (object,), {'args': [1205]})
                )
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
    ) -> Decimal:
        """
        预冻结算力（用户无感知操作，不记录日志）

        操作:
        - frozen_balance += amount
        - 不创建流水记录（用户无感知）

        Args:
            user_id: 用户ID
            amount: 冻结金额
            task_id: 关联任务ID
            remark: 备注

        Returns:
            实际冻结金额
        """
        import asyncio
        from sqlalchemy.exc import OperationalError, DBAPIError

        max_retries = 5  # 最大重试次数
        base_delay = 0.3  # 基础延迟(秒)

        for attempt in range(max_retries):
            try:
                # 获取用户并加锁(使用 skip_locked 快速失败)
                user = await self.get_user_with_lock(user_id, skip_locked=True)

                # 检查可用余额
                available = user.balance - user.frozen_balance
                if available < amount:
                    raise BadRequestException(
                        f"余额不足。可用余额: {available:.0f}, 需要: {amount:.0f}"
                    )

                # 冻结金额（不记录日志，用户无感知）
                user.frozen_balance += amount

                # 立即刷新到数据库
                await self.db.flush()

                return amount

            except (OperationalError, DBAPIError) as e:
                # 检查是否是锁等待超时或死锁错误
                error_code = None
                if hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                    error_code = e.orig.args[0] if e.orig.args else None

                # 1205: Lock wait timeout exceeded
                # 1213: Deadlock found when trying to get lock
                is_lock_error = error_code in (1205, 1213)

                if is_lock_error and attempt < max_retries - 1:
                    # 指数退避: 0.3s, 0.6s, 1.2s, 1.8s, 2.4s
                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"算力预冻结时遇到锁冲突(尝试 {attempt + 1}/{max_retries}): "
                        f"用户ID={user_id}, 错误码={error_code}, {delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # 重试次数用完或非锁错误,抛出异常
                    raise

    async def unfreeze_and_deduct(
        self,
        user_id: int,
        task_id: str,
        actual_cost: Decimal,
        input_tokens: int,
        output_tokens: int,
        model_id: int,
        model_name: str,
        frozen_amount: Decimal
    ) -> None:
        """
        解冻并扣除实际消耗

        操作:
        - 从 frozen_balance 中减少预冻结金额（解冻）
        - 从 balance 中扣除实际消耗
        - 创建 CONSUME 流水记录（负数）

        Args:
            user_id: 用户ID
            task_id: 关联任务ID
            actual_cost: 实际消耗金额
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
            model_name: 模型名称
            frozen_amount: 预冻结金额
        """
        import asyncio
        from sqlalchemy.exc import OperationalError, DBAPIError

        max_retries = 5  # 最大重试次数
        base_delay = 0.3  # 基础延迟(秒)

        for attempt in range(max_retries):
            try:
                # 获取用户并加锁(使用 skip_locked 快速失败)
                user = await self.get_user_with_lock(user_id, skip_locked=True)

                # 记录变动前余额
                before_balance = user.balance
                before_frozen = user.frozen_balance

                # 解冻：减少冻结余额
                user.frozen_balance -= frozen_amount

                # 扣除实际消耗
                user.balance -= actual_cost

                # 创建消耗流水（负数表示减少）
                remark = (
                    f"AI对话消耗 - "
                    f"输入Token: {input_tokens}, 输出Token: {output_tokens}, "
                    f"模型: {model_name}"
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
                    f"解冻前: {before_frozen}, 解冻后: {user.frozen_balance}, "
                    f"余额前: {before_balance}, 余额后: {user.balance}"
                )

                return  # 成功,退出重试循环

            except (OperationalError, DBAPIError) as e:
                # 检查是否是锁等待超时或死锁错误
                error_code = None
                if hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                    error_code = e.orig.args[0] if e.orig.args else None

                # 1205: Lock wait timeout exceeded
                # 1213: Deadlock found when trying to get lock
                is_lock_error = error_code in (1205, 1213)

                if is_lock_error and attempt < max_retries - 1:
                    # 指数退避: 0.3s, 0.6s, 1.2s, 1.8s, 2.4s
                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"算力解冻扣款时遇到锁冲突(尝试 {attempt + 1}/{max_retries}): "
                        f"用户ID={user_id}, 错误码={error_code}, {delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # 重试次数用完或非锁错误,抛出异常
                    raise

    async def refund_full(
        self,
        user_id: int,
        task_id: str,
        reason: str,
        frozen_amount: Decimal,
        error_code: Optional[int] = None
    ) -> None:
        """
        全额退还 (API错误时)

        操作:
        - frozen_balance -= 预冻结金额 (只是减少冻结余额)
        - 不改变 balance (因为冻结时并未减少balance)

        Args:
            user_id: 用户ID
            task_id: 关联任务ID
            reason: 退款原因
            frozen_amount: 预冻结金额
            error_code: 错误码(可选)
        """
        import asyncio
        from sqlalchemy.exc import OperationalError, DBAPIError

        max_retries = 5  # 最大重试次数
        base_delay = 0.3  # 基础延迟(秒)

        for attempt in range(max_retries):
            try:
                # 获取用户并加锁(使用 skip_locked 快速失败)
                user = await self.get_user_with_lock(user_id, skip_locked=True)

                # 只解冻，不改变总余额（用户无感知，不记录日志）
                # 因为冻结时：frozen_balance增加，balance不变
                # 解冻时：frozen_balance减少，balance不变
                user.frozen_balance -= frozen_amount

                return  # 成功,退出重试循环

            except (OperationalError, DBAPIError) as e:
                # 检查是否是锁等待超时或死锁错误
                error_code_temp = None
                if hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                    error_code_temp = e.orig.args[0] if e.orig.args else None

                # 1205: Lock wait timeout exceeded
                # 1213: Deadlock found when trying to get lock
                is_lock_error = error_code_temp in (1205, 1213)

                if is_lock_error and attempt < max_retries - 1:
                    # 指数退避: 0.3s, 0.6s, 1.2s, 1.8s, 2.4s
                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"算力退款时遇到锁冲突(尝试 {attempt + 1}/{max_retries}): "
                        f"用户ID={user_id}, 错误码={error_code_temp}, {delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # 重试次数用完或非锁错误,抛出异常
                    raise

    async def deduct_violation_penalty(
        self,
        user_id: int,
        task_id: str,
        model_id: int,
        model_name: str,
        frozen_amount: Decimal
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
            model_name: 模型名称
            frozen_amount: 预冻结金额
        """
        import asyncio
        from sqlalchemy.exc import OperationalError, DBAPIError

        max_retries = 5  # 最大重试次数
        base_delay = 0.3  # 基础延迟(秒)

        for attempt in range(max_retries):
            try:
                # 获取用户并加锁(使用 skip_locked 快速失败)
                user = await self.get_user_with_lock(user_id, skip_locked=True)

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
                remark = f"内容违规处罚 - 模型: {model_name}"

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

                return  # 成功,退出重试循环

            except (OperationalError, DBAPIError) as e:
                # 检查是否是锁等待超时或死锁错误
                error_code = None
                if hasattr(e, 'orig') and hasattr(e.orig, 'args'):
                    error_code = e.orig.args[0] if e.orig.args else None

                # 1205: Lock wait timeout exceeded
                # 1213: Deadlock found when trying to get lock
                is_lock_error = error_code in (1205, 1213)

                if is_lock_error and attempt < max_retries - 1:
                    # 指数退避: 0.3s, 0.6s, 1.2s, 1.8s, 2.4s
                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"算力违规处罚时遇到锁冲突(尝试 {attempt + 1}/{max_retries}): "
                        f"用户ID={user_id}, 错误码={error_code}, {delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # 重试次数用完或非锁错误,抛出异常
                    raise

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

    # ============== 快速事务方法(独立会话,快速释放锁) ==============

    async def freeze_amount_quick(self, user_id: int, amount: Decimal) -> bool:
        """
        快速预冻结(独立事务,快速释放锁)

        使用独立的数据库会话和事务,避免长时间持有锁
        适用于需要快速冻结但不立即提交的场景

        Args:
            user_id: 用户ID
            amount: 冻结金额

        Returns:
            是否成功
        """
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(User)
                    .where(User.id == user_id)
                    .with_for_update(nowait=False)  # 等待锁,但设置超时
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.error(f"快速冻结失败: 用户 {user_id} 不存在")
                    return False

                # 检查可用余额
                available = user.balance - user.frozen_balance
                if available < amount:
                    logger.warning(
                        f"快速冻结失败: 用户 {user_id} 余额不足, "
                        f"可用 {available:.0f}, 需要 {amount:.0f}"
                    )
                    return False

                # 冻结金额
                user.frozen_balance += amount

                # 立即提交,快速释放锁
                await db.commit()
                logger.debug(f"用户 {user_id} 快速冻结成功: {amount}")
                return True

        except Exception as e:
            logger.error(f"快速冻结异常: 用户 {user_id}, 金额 {amount}, 错误: {e}")
            return False

    async def unfreeze_and_deduct_quick(
        self,
        user_id: int,
        task_id: str,
        actual_cost: Decimal,
        input_tokens: int,
        output_tokens: int,
        model_id: int,
        model_name: str,
        frozen_amount: Decimal
    ) -> bool:
        """
        快速解冻并扣除(独立事务)

        Args:
            user_id: 用户ID
            task_id: 任务ID
            actual_cost: 实际消耗
            input_tokens: 输入token数
            output_tokens: 输出token数
            model_id: 模型ID
            model_name: 模型名称
            frozen_amount: 预冻结金额

        Returns:
            是否成功
        """
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(User)
                    .where(User.id == user_id)
                    .with_for_update()
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.error(f"快速结算失败: 用户 {user_id} 不存在")
                    return False

                # 记录变动前余额
                before_balance = user.balance

                # 解冻并扣除
                user.frozen_balance -= frozen_amount
                user.balance -= actual_cost

                # 创建消耗流水
                remark = (
                    f"AI对话消耗 - "
                    f"输入Token: {input_tokens}, 输出Token: {output_tokens}, "
                    f"模型: {model_name}"
                )

                consume_log = ComputeLog(
                    user_id=user_id,
                    type=ComputeType.CONSUME,
                    amount=-actual_cost,
                    before_balance=before_balance,
                    after_balance=user.balance,
                    remark=remark,
                    task_id=task_id,
                    source="api"
                )
                db.add(consume_log)

                # 立即提交
                await db.commit()

                logger.info(
                    f"用户 {user_id} 快速结算成功: "
                    f"预冻结 {frozen_amount}, 实际消耗 {actual_cost}"
                )
                return True

        except Exception as e:
            logger.error(f"快速结算异常: 用户 {user_id}, 任务 {task_id}, 错误: {e}")
            return False

    async def refund_quick(
        self,
        user_id: int,
        task_id: str,
        frozen_amount: Decimal,
        reason: str = "任务失败退款"
    ) -> bool:
        """
        快速退款(独立事务)

        Args:
            user_id: 用户ID
            task_id: 任务ID
            frozen_amount: 预冻结金额
            reason: 退款原因

        Returns:
            是否成功
        """
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(User)
                    .where(User.id == user_id)
                    .with_for_update()
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.error(f"快速退款失败: 用户 {user_id} 不存在")
                    return False

                # 只解冻,不改变总余额
                user.frozen_balance -= frozen_amount

                # 立即提交
                await db.commit()

                logger.info(f"用户 {user_id} 快速退款成功: {frozen_amount}, 原因: {reason}")
                return True

        except Exception as e:
            logger.error(f"快速退款异常: 用户 {user_id}, 错误: {e}")
            return False
