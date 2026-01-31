"""
火源币账户管理服务
实现算力的冻结、扣除、退还等核心操作
"""
import json
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger

from models.user import User
from models.compute import ComputeLog, ComputeType
from .calculator import CoinCalculatorService
from utils.exceptions import BadRequestException, NotFoundException
from db.session import async_session_maker


class CoinAccountService:
    """
    火源币账户管理服务类
    
    职责说明：
    - 余额管理：冻结、扣除、退还
    - 流水记录：创建算力变动流水
    - 原子操作：CAS乐观锁实现无锁冲突操作
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化火源币账户服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.calculator = CoinCalculatorService(db)
    
    async def get_user_with_lock(
        self,
        user_id: int,
        skip_locked: bool = False
    ) -> User:
        """
        获取用户并加锁（用于余额操作）
        
        Args:
            user_id: 用户ID
            skip_locked: 是否跳过锁等待（快速失败）
        
        Returns:
            用户对象
        
        Raises:
            NotFoundException: 用户不存在
        """
        if skip_locked:
            # 使用 NOWAIT 快速失败
            query = select(User).where(User.id == user_id).with_for_update(nowait=True)
        else:
            # 等待锁释放
            query = select(User).where(User.id == user_id).with_for_update()
        
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(f"用户 {user_id} 不存在")
        
        return user

    async def get_user_for_read(self, user_id: int) -> Optional[User]:
        """
        获取用户信息（只读，不加锁）

        ⚠️ 不再使用 FOR UPDATE，避免锁冲突

        Args:
            user_id: 用户ID

        Returns:
            用户对象或None
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def check_balance(
        self,
        user_id: int,
        required_amount: Decimal
    ) -> bool:
        """
        检查余额是否充足（原子操作，无需加锁）

        ⚠️ 不再使用 FOR UPDATE，使用原子SQL避免锁冲突

        Args:
            user_id: 用户ID
            required_amount: 需要的金额

        Returns:
            True-余额充足, False-余额不足
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(User.balance, User.frozen_balance)
            .where(User.id == user_id)
        )
        row = result.first()

        if not row:
            return False

        balance, frozen_balance = row
        available = balance - frozen_balance
        return available >= required_amount

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

    # ============== ✅ 原子化操作方法（无锁冲突） ==============

    async def freeze_amount_atomic(
        self,
        user_id: int,
        amount: Decimal,
        request_id: str,
        model_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        remark: Optional[str] = None
    ) -> dict:
        """
        ✅ 原子化冻结算力（幂等性保证 + 乐观锁 CAS）

        核心优化：
        - ✅ 使用乐观锁（CAS版本号），避免锁等待超时
        - ✅ 通过request_id实现幂等性
        - ✅ 自动重试（CAS冲突时，1ms间隔）

        CAS 原理：
        ```sql
        UPDATE users
        SET frozen_balance = frozen_balance + amount,
            version = version + 1
        WHERE id = user_id
          AND version = current_version
          AND balance - frozen_balance >= amount  -- ✅ 原子条件判断
        ```

        Args:
            user_id: 用户ID
            amount: 冻结金额
            request_id: 请求ID（全局唯一，用于幂等性）
            model_id: 模型ID（可选）
            conversation_id: 会话ID（可选）
            remark: 备注（可选）

        Returns:
            {
                'success': bool,              # 是否成功
                'already_frozen': bool,       # 是否已冻结（幂等）
                'freeze_log_id': int,         # 冻结记录ID
                'insufficient_balance': bool, # 是否余额不足
                'available_balance': Decimal, # 可用余额（仅在余额不足时返回）
                'balance': Decimal,           # 总余额（仅在余额不足时返回）
                'frozen_balance': Decimal     # 冻结余额（仅在余额不足时返回）
            }
        """
        from models.compute_freeze import ComputeFreezeLog, FreezeStatus
        from sqlalchemy import update, select
        from sqlalchemy.exc import IntegrityError
        import asyncio
        import time

        max_retries = 50  # CAS冲突最多重试50次（每次1ms，总共50ms）
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                # ✅ 第一步：幂等性检查（无锁查询，优先检查）
                result = await self.db.execute(
                    select(ComputeFreezeLog).where(
                        ComputeFreezeLog.request_id == request_id
                    )
                )
                existing_log = result.scalar_one_or_none()

                if existing_log:
                    logger.info(
                        f"✅ [CAS冻结] 幂等返回: request_id={request_id}, "
                        f"用户={user_id}, 金额={amount}, 原冻结记录ID={existing_log.id}"
                    )
                    return {
                        'success': True,
                        'already_frozen': True,
                        'freeze_log_id': existing_log.id,
                        'insufficient_balance': False,
                    }

                # ✅ 第二步：查询当前用户版本号（无锁）
                user_result = await self.db.execute(
                    select(User.id, User.version, User.balance, User.frozen_balance)
                    .where(User.id == user_id)
                )
                user_row = user_result.first()

                if not user_row:
                    await self.db.rollback()
                    logger.error(f"❌ [CAS冻结] 用户不存在: user_id={user_id}")
                    return {
                        'success': False,
                        'already_frozen': False,
                        'freeze_log_id': None,
                        'insufficient_balance': False,
                    }

                current_version = user_row[1]

                # ✅ 第三步：CAS 更新（乐观锁）
                update_result = await self.db.execute(
                    update(User)
                    .where(
                        User.id == user_id,
                        User.version == current_version,  # ✅ CAS 版本号
                        User.balance - User.frozen_balance >= amount  # ✅ 原子条件
                    )
                    .values(
                        frozen_balance=User.frozen_balance + amount,
                        version=User.version + 1  # ✅ 版本号+1
                    )
                )

                if update_result.rowcount == 0:
                    # CAS 失败：版本号冲突 或 余额不足
                    # 检查是否是余额不足
                    user_check = await self.db.execute(
                        select(User.balance, User.frozen_balance)
                        .where(User.id == user_id)
                    )
                    balance_row = user_check.first()
                    if balance_row:
                        balance = balance_row[0]
                        frozen_balance = balance_row[1]
                        available = balance - frozen_balance
                        if available < amount:
                            await self.db.rollback()
                            logger.warning(
                                f"⚠️ [CAS冻结] 余额不足: 用户={user_id}, "
                                f"可用={available}, 需要={amount}"
                            )
                            return {
                                'success': False,
                                'already_frozen': False,
                                'freeze_log_id': None,
                                'insufficient_balance': True,
                                'available_balance': available,  # ✅ 返回余额信息，避免额外查询
                                'balance': balance,
                                'frozen_balance': frozen_balance,
                            }

                    # 版本号冲突，快速重试
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.001)  # 1ms 后重试
                        continue
                    else:
                        await self.db.rollback()
                        logger.error(
                            f"❌ [CAS冻结] CAS重试耗尽: 用户={user_id}, "
                            f"尝试次数={max_retries}"
                        )
                        return {
                            'success': False,
                            'already_frozen': False,
                            'freeze_log_id': None,
                            'insufficient_balance': False,
                        }

                # ✅ 第四步：创建冻结记录
                freeze_log = ComputeFreezeLog(
                    request_id=request_id,
                    user_id=user_id,
                    amount=amount,
                    model_id=model_id,
                    conversation_id=conversation_id,
                    status=FreezeStatus.FROZEN.value,
                    remark=remark,
                )
                self.db.add(freeze_log)
                await self.db.flush()

                await self.db.commit()

                elapsed = time.time() - start_time
                logger.info(
                    f"✅ [CAS冻结] 成功: 用户={user_id}, 金额={amount}, "
                    f"request_id={request_id}, 冻结记录ID={freeze_log.id}, "
                    f"耗时={elapsed*1000:.1f}ms, 重试次数={attempt}"
                )

                return {
                    'success': True,
                    'already_frozen': False,
                    'freeze_log_id': freeze_log.id,
                    'insufficient_balance': False,
                }

            except IntegrityError:
                # 幂等性保证：request_id 冲突（并发场景下的竞态）
                await self.db.rollback()

                # 再次查询原有记录
                result = await self.db.execute(
                    select(ComputeFreezeLog).where(
                        ComputeFreezeLog.request_id == request_id
                    )
                )
                existing_log = result.scalar_one_or_none()

                if existing_log:
                    logger.info(
                        f"✅ [CAS冻结] 幂等返回(并发): request_id={request_id}, "
                        f"用户={user_id}, 金额={amount}, 原冻结记录ID={existing_log.id}"
                    )
                    return {
                        'success': True,
                        'already_frozen': True,
                        'freeze_log_id': existing_log.id,
                        'insufficient_balance': False,
                    }
                else:
                    # 异常情况：不应该发生
                    logger.error(f"❌ [CAS冻结] 幂等检查失败: request_id={request_id}")
                    return {
                        'success': False,
                        'already_frozen': False,
                        'freeze_log_id': None,
                        'insufficient_balance': False,
                    }

            except Exception as e:
                await self.db.rollback()
                logger.error(f"❌ [CAS冻结] 异常: 用户={user_id}, 错误={e}")
                raise

        # 理论上不会执行到这里
        logger.error(f"❌ [CAS冻结] 重试耗尽: 用户={user_id}")
        return {
            'success': False,
            'already_frozen': False,
            'freeze_log_id': None,
            'insufficient_balance': False,
        }

    async def settle_amount_atomic(
        self,
        user_id: int,
        request_id: str,
        actual_cost: Decimal,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model_name: str = "",
        agent_id: Optional[int] = None,
        agent_name: Optional[str] = None
    ) -> dict:
        """
        ✅ 原子化结算算力（乐观锁 CAS + 解冻 + 扣除）

        操作：
        1. 从 frozen_balance 减去预冻结金额（解冻）
        2. 从 balance 减去实际消耗
        3. 创建消耗流水记录
        4. 更新冻结记录状态为 SETTLED

        CAS 原理：
        ```sql
        UPDATE users
        SET frozen_balance = frozen_balance - freeze_amount,
            balance = balance - actual_cost,
            version = version + 1
        WHERE id = user_id
          AND version = current_version
          AND frozen_balance >= freeze_amount  -- ✅ 原子条件
        ```

        Args:
            user_id: 用户ID
            request_id: 请求ID
            actual_cost: 实际消耗金额
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_name: 模型名称
            agent_id: 智能体ID（可选）
            agent_name: 智能体名称（可选）

        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        from models.compute_freeze import ComputeFreezeLog, FreezeStatus
        from models.compute import ComputeLog, ComputeType
        from sqlalchemy import select, update
        from datetime import datetime
        import asyncio
        import time

        max_retries = 50  # CAS冲突最多重试50次
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                # 查询冻结记录
                result = await self.db.execute(
                    select(ComputeFreezeLog).where(
                        ComputeFreezeLog.request_id == request_id
                    )
                )
                freeze_log = result.scalar_one_or_none()

                if not freeze_log:
                    logger.error(f"❌ [CAS结算] 冻结记录不存在: request_id={request_id}")
                    return {'success': False, 'message': '冻结记录不存在'}

                # ✅ 修复：freeze_log.status 是枚举对象，需要比较枚举对象而不是枚举值
                if freeze_log.status != FreezeStatus.FROZEN:
                    logger.warning(
                        f"⚠️ [CAS结算] 记录已处理: request_id={request_id}, "
                        f"status={freeze_log.status}"
                    )
                    return {'success': True, 'message': '已处理'}

                freeze_amount = freeze_log.amount

                # ✅ 查询当前用户版本号和余额
                user_result = await self.db.execute(
                    select(User.id, User.version, User.balance, User.frozen_balance)
                    .where(User.id == user_id)
                )
                user_row = user_result.first()

                if not user_row:
                    await self.db.rollback()
                    logger.error(f"❌ [CAS结算] 用户不存在: user_id={user_id}")
                    return {'success': False, 'message': '用户不存在'}

                current_version = user_row[1]
                before_balance = user_row[2]

                # ✅ 执行 CAS 更新：解冻 + 扣除
                update_result = await self.db.execute(
                    update(User)
                    .where(
                        User.id == user_id,
                        User.version == current_version,  # ✅ CAS 版本号
                        User.frozen_balance >= freeze_amount  # ✅ 原子条件
                    )
                    .values(
                        frozen_balance=User.frozen_balance - freeze_amount,  # 解冻
                        balance=User.balance - actual_cost,  # 扣除实际消耗
                        version=User.version + 1  # ✅ 版本号+1
                    )
                )

                if update_result.rowcount == 0:
                    # CAS 失败：版本号冲突 或 冻结余额不足
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.001)  # 1ms 后重试
                        continue
                    else:
                        await self.db.rollback()
                        logger.error(
                            f"❌ [CAS结算] CAS重试耗尽: 用户={user_id}, "
                            f"尝试次数={max_retries}"
                        )
                        return {'success': False, 'message': '结算失败'}

                # ✅ 重新查询用户余额（用于流水记录）
                after_user = await self.db.execute(
                    select(User.balance).where(User.id == user_id)
                )
                after_balance = after_user.scalar_one()

                # 更新冻结记录状态
                freeze_log.status = FreezeStatus.SETTLED.value
                freeze_log.actual_cost = actual_cost
                freeze_log.input_tokens = input_tokens
                freeze_log.output_tokens = output_tokens
                freeze_log.settled_at = datetime.now()

                # 创建消耗流水
                # 构建备注信息：只包含agent和模型信息，不包含token信息
                remark_parts = []
                if agent_name:
                    remark_parts.append(f"智能体: {agent_name}")
                elif agent_id:
                    remark_parts.append(f"智能体ID: {agent_id}")
                if model_name:
                    remark_parts.append(f"模型: {model_name}")
                
                remark = "AI对话消耗"
                if remark_parts:
                    remark += " - " + ", ".join(remark_parts)

                # 构建扩展数据（JSON格式，存储agent和模型详细信息）
                extra_data_dict = {}
                if agent_id:
                    extra_data_dict["agent_id"] = agent_id
                if agent_name:
                    extra_data_dict["agent_name"] = agent_name
                if model_name:
                    extra_data_dict["model_name"] = model_name
                
                extra_data_json = json.dumps(extra_data_dict) if extra_data_dict else None

                consume_log = ComputeLog(
                    user_id=user_id,
                    type=ComputeType.CONSUME,
                    amount=-actual_cost,  # 负数表示减少
                    before_balance=before_balance,
                    after_balance=after_balance,
                    remark=remark,
                    task_id=request_id,
                    source="api",
                    extra_data=extra_data_json
                )
                self.db.add(consume_log)

                await self.db.commit()

                elapsed = time.time() - start_time
                logger.info(
                    f"✅ [CAS结算] 成功: 用户={user_id}, "
                    f"预冻结={freeze_amount}, 实际消耗={actual_cost}, "
                    f"余额: {before_balance} → {after_balance}, "
                    f"request_id={request_id}, 耗时={elapsed*1000:.1f}ms, "
                    f"重试次数={attempt}"
                )

                return {'success': True, 'message': '结算成功'}

            except Exception as e:
                await self.db.rollback()
                logger.error(f"❌ [CAS结算] 异常: 用户={user_id}, 错误={e}")
                raise

        # 理论上不会执行到这里
        logger.error(f"❌ [CAS结算] 重试耗尽: 用户={user_id}")
        return {'success': False, 'message': '结算失败'}

    async def refund_amount_atomic(
        self,
        user_id: int,
        request_id: str,
        reason: str = "AI生成失败"
    ) -> dict:
        """
        ✅ 原子化退还算力（乐观锁 CAS + 全额退还）

        操作：
        1. 从 frozen_balance 减去预冻结金额（解冻）
        2. 不扣减 balance（全额退还）
        3. 更新冻结记录状态为 REFUNDED

        CAS 原理：
        ```sql
        UPDATE users
        SET frozen_balance = frozen_balance - freeze_amount,
            version = version + 1
        WHERE id = user_id
          AND version = current_version
          AND frozen_balance >= freeze_amount  -- ✅ 原子条件
        ```

        Args:
            user_id: 用户ID
            request_id: 请求ID
            reason: 退款原因

        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        from models.compute_freeze import ComputeFreezeLog, FreezeStatus
        from sqlalchemy import select, update
        from datetime import datetime
        import asyncio
        import time

        max_retries = 50  # CAS冲突最多重试50次
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                # 查询冻结记录
                result = await self.db.execute(
                    select(ComputeFreezeLog).where(
                        ComputeFreezeLog.request_id == request_id
                    )
                )
                freeze_log = result.scalar_one_or_none()

                if not freeze_log:
                    logger.error(f"❌ [CAS退款] 冻结记录不存在: request_id={request_id}")
                    return {'success': False, 'message': '冻结记录不存在'}

                if freeze_log.status != FreezeStatus.FROZEN:
                    logger.warning(
                        f"⚠️ [CAS退款] 记录已处理: request_id={request_id}, "
                        f"status={freeze_log.status}"
                    )
                    return {'success': True, 'message': '已处理'}

                freeze_amount = freeze_log.amount

                # ✅ 查询当前用户版本号
                user_result = await self.db.execute(
                    select(User.id, User.version, User.frozen_balance)
                    .where(User.id == user_id)
                )
                user_row = user_result.first()

                if not user_row:
                    await self.db.rollback()
                    logger.error(f"❌ [CAS退款] 用户不存在: user_id={user_id}")
                    return {'success': False, 'message': '用户不存在'}

                current_version = user_row[1]

                # ✅ 执行 CAS 更新：只解冻，不扣余额
                update_result = await self.db.execute(
                    update(User)
                    .where(
                        User.id == user_id,
                        User.version == current_version,  # ✅ CAS 版本号
                        User.frozen_balance >= freeze_amount  # ✅ 原子条件
                    )
                    .values(
                        frozen_balance=User.frozen_balance - freeze_amount,  # 只解冻
                        version=User.version + 1  # ✅ 版本号+1
                    )
                )

                if update_result.rowcount == 0:
                    # CAS 失败：版本号冲突 或 冻结余额不足
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.001)  # 1ms 后重试
                        continue
                    else:
                        await self.db.rollback()
                        logger.error(
                            f"❌ [CAS退款] CAS重试耗尽: 用户={user_id}, "
                            f"尝试次数={max_retries}"
                        )
                        return {'success': False, 'message': '退款失败'}

                # 更新冻结记录状态
                freeze_log.status = FreezeStatus.REFUNDED.value
                freeze_log.refunded_at = datetime.now()
                freeze_log.remark = reason

                await self.db.commit()

                elapsed = time.time() - start_time
                logger.info(
                    f"✅ [CAS退款] 成功: 用户={user_id}, "
                    f"退还金额={freeze_amount}, request_id={request_id}, "
                    f"原因={reason}, 耗时={elapsed*1000:.1f}ms, 重试次数={attempt}"
                )

                return {'success': True, 'message': '退款成功'}

            except Exception as e:
                await self.db.rollback()
                logger.error(f"❌ [CAS退款] 异常: 用户={user_id}, 错误={e}")
                raise

        # 理论上不会执行到这里
        logger.error(f"❌ [CAS退款] 重试耗尽: 用户={user_id}")
        return {'success': False, 'message': '退款失败'}

