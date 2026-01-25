"""
余额预检中间件
在对话前检查用户余额并预冻结
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from services.coin import CoinServiceFactory
from services.system.permission import PermissionService
from utils.exceptions import BadRequestException


class BalanceCheckerMiddleware:
    """余额预检中间件"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.coin_service = CoinServiceFactory(db)
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
        
        # 使用工厂的组合方法：检查并冻结
        return await self.coin_service.check_and_freeze(
            user_id=user_id,
            model_id=model_id,
            input_text=input_text,
            task_id=task_id,
            estimated_output_tokens=estimated_output_tokens
        )

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
        # 使用工厂的组合方法：结算交易
        await self.coin_service.settle_transaction(
            user_id=user_id,
            task_id=task_id,
            actual_cost=actual_cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=model_id,
            model_name=model_name,
            frozen_amount=frozen_amount,
            is_error=is_error,
            error_code=error_code,
            is_violation=is_violation
        )
