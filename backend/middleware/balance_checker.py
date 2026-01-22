"""
余额预检中间件
在对话前检查用户余额并预冻结
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.coin.account import CoinAccountService
from services.coin.calculator import CoinCalculatorService
from services.system.permission import PermissionService
from utils.exceptions import BadRequestException


class BalanceCheckerMiddleware:
    """余额预检中间件"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_service = CoinAccountService(db)
        self.calculator = CoinCalculatorService(db)
        self.permission_service = PermissionService(db)

    async def check_and_freeze(
        self,
        user_id: int,
        model_id: int,
        input_text: str,
        task_id: str,
        estimated_output_tokens: Optional[int] = None
    ) -> dict:
        """
        对话前余额检查并预冻结

        ✅ 优化：使用原子操作，避免锁冲突
        - 不再先 check_balance 再 freeze_amount（会导致两次锁等待）
        - 直接调用 freeze_amount_atomic，一次性完成检查和冻结

        Args:
            user_id: 用户ID
            model_id: 模型ID
            input_text: 输入文本
            task_id: 任务ID
            estimated_output_tokens: 预估输出Token数(可选)

        Returns:
            预冻结信息字典

        Raises:
            BadRequestException: 余额不足或VIP过期时
        """
        # 0. 检查VIP状态（如果VIP过期，拒绝使用算力）
        permission = await self.permission_service.get_user_permission(user_id)
        if permission.get("is_vip_expired"):
            raise BadRequestException(
                "您的会员已过期，无法使用算力。请续费会员后再试。"
            )
        
        # 1. 估算最大消耗
        estimated_cost = await self.calculator.estimate_max_cost(
            model_id=model_id,
            input_text=input_text,
            estimated_output_tokens=estimated_output_tokens
        )

        logger.debug(
            f"用户 {user_id} 预冻结估算: "
            f"模型ID={model_id}, 预估消耗={estimated_cost}"
        )

        # 2. 直接使用原子操作冻结（内部会检查余额）
        # ✅ 这样只需要一次原子 UPDATE，避免锁冲突
        freeze_result = await self.account_service.freeze_amount_atomic(
            user_id=user_id,
            amount=estimated_cost,
            request_id=task_id,
            model_id=model_id,
            remark=f"对话预冻结 - 模型ID: {model_id}"
        )

        # 3. 检查冻结结果
        if freeze_result['insufficient_balance']:
            # 获取用户当前余额，用于错误提示
            balance_info = await self.account_service.get_user_balance(user_id)
            raise BadRequestException(
                f"余额不足。可用余额: {balance_info['available_balance']:.4f} 火源币, "
                f"需要: {estimated_cost:.4f} 火源币。"
                f"请充值后再试。"
            )

        if not freeze_result['success']:
            logger.error(
                f"❌ [余额检查] 冻结失败: 用户={user_id}, "
                f"task_id={task_id}, result={freeze_result}"
            )
            raise BadRequestException(
                "算力冻结失败，请稍后重试"
            )

        logger.debug(
            f"✅ [余额检查] 冻结成功: 用户={user_id}, "
            f"task_id={task_id}, 金额={estimated_cost}, "
            f"freeze_log_id={freeze_result['freeze_log_id']}"
        )

        return {
            "task_id": task_id,
            "frozen_amount": estimated_cost,
            "model_id": model_id,
            "user_id": user_id,
            "freeze_log_id": freeze_result['freeze_log_id'],
        }

    async def settle(
        self,
        user_id: int,
        task_id: str,
        actual_cost: Decimal,
        input_tokens: int,
        output_tokens: int,
        model_id: int,
        model_name: str,
        frozen_amount: Decimal,
        is_error: bool = False,
        error_code: Optional[int] = None,
        is_violation: bool = False
    ) -> None:
        """
        最终结算

        ✅ 优化：使用原子操作，避免锁冲突

        Args:
            user_id: 用户ID
            task_id: 任务ID
            actual_cost: 实际消耗
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
            model_name: 模型名称
            frozen_amount: 预冻结金额
            is_error: 是否为错误
            error_code: 错误码
            is_violation: 是否内容违规
        """
        if is_error:
            # API错误,全额退还（使用原子退款）
            reason = "API调用失败"
            await self.account_service.refund_amount_atomic(
                user_id=user_id,
                request_id=task_id,
                reason=reason
            )

        elif is_violation:
            # 内容违规,扣除处罚费用
            await self.account_service.deduct_violation_penalty(
                user_id=user_id,
                task_id=task_id,
                model_id=model_id,
                model_name=model_name,
                frozen_amount=frozen_amount
            )

        else:
            # ✅ 正常完成,使用原子结算（解冻 + 扣除）
            settle_result = await self.account_service.settle_amount_atomic(
                user_id=user_id,
                request_id=task_id,
                actual_cost=actual_cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_name=model_name
            )

            if not settle_result['success']:
                logger.error(
                    f"❌ [结算] 失败: 用户={user_id}, task_id={task_id}, "
                    f"message={settle_result.get('message', '未知错误')}"
                )
                # 结算失败不抛异常，避免影响主流程
                # 但记录错误日志供后续处理
