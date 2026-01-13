"""
余额预检中间件
在对话前检查用户余额并预冻结
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.coin_account import CoinAccountService
from services.coin_calculator import CoinCalculatorService
from utils.exceptions import BadRequestException


class BalanceCheckerMiddleware:
    """余额预检中间件"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_service = CoinAccountService(db)
        self.calculator = CoinCalculatorService(db)

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

        流程:
        1. 估算最大消耗
        2. 检查可用余额
        3. 余额不足返回错误
        4. 余额充足则预冻结

        Args:
            user_id: 用户ID
            model_id: 模型ID
            input_text: 输入文本
            task_id: 任务ID
            estimated_output_tokens: 预估输出Token数(可选)

        Returns:
            预冻结信息字典

        Raises:
            BadRequestException: 余额不足时
        """
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

        # 2. 检查可用余额
        has_balance = await self.account_service.check_balance(
            user_id=user_id,
            required_amount=estimated_cost
        )

        if not has_balance:
            # 获取用户当前余额
            balance_info = await self.account_service.get_user_balance(user_id)
            raise BadRequestException(
                f"余额不足。可用余额: {balance_info['available_balance']:.4f} 火源币, "
                f"需要: {estimated_cost:.4f} 火源币。"
                f"请充值后再试。"
            )

        # 3. 预冻结算力（用户无感知，不记录日志）
        frozen_amount = await self.account_service.freeze_amount(
            user_id=user_id,
            amount=estimated_cost,
            task_id=task_id,
            remark=f"对话预冻结 - 模型ID: {model_id}"
        )

        return {
            "task_id": task_id,
            "frozen_amount": frozen_amount,
            "model_id": model_id,
            "user_id": user_id,
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
            # API错误,全额退还
            reason = "API调用失败"
            await self.account_service.refund_full(
                user_id=user_id,
                task_id=task_id,
                reason=reason,
                frozen_amount=frozen_amount,
                error_code=error_code
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
            # 正常完成,解冻并扣除实际消耗
            await self.account_service.unfreeze_and_deduct(
                user_id=user_id,
                task_id=task_id,
                actual_cost=actual_cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id,
                model_name=model_name,
                frozen_amount=frozen_amount
            )
