"""
增强的对话服务 - 集成算力扣除逻辑
完整实现预冻结、流式生成、最终结算的流程
"""
import uuid
from decimal import Decimal
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from middleware.balance_checker import BalanceCheckerMiddleware
from services.content_moderation import ContentModerationService
from services.coin_calculator import CoinCalculatorService
from services.llm_service import BaseLLM
from models.llm_model import LLMModel
from utils.exceptions import BadRequestException


class EnhancedConversationService:
    """增强的对话服务类 (集成算力扣除)"""

    def __init__(self, db: AsyncSession, llm_client: BaseLLM):
        self.db = db
        self.llm_client = llm_client
        self.balance_checker = BalanceCheckerMiddleware(db)
        self.moderation = ContentModerationService()
        self.calculator = CoinCalculatorService(db)

    async def _get_model_name(self, model_id: int) -> str:
        """获取模型名称"""
        result = await self.db.execute(
            select(LLMModel.name).where(LLMModel.id == model_id)
        )
        model_name = result.scalar_one_or_none()
        return model_name or f"模型#{model_id}"

    async def chat(
        self,
        user_id: int,
        message: str,
        model_id: int,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        """
        流式对话 (完整算力扣除流程)

        完整流程:
        1. 前置内容审查
        2. 估算最大消耗
        3. 余额预检并预冻结
        4. 调用LLM (流式)
        5. 追踪Token使用
        6. 后置内容审查
        7. 最终结算 (多���少补/错误处理)

        Args:
            user_id: 用户ID
            message: 用户消息
            model_id: 模型ID
            system_prompt: 系统提示词
            conversation_id: 对话ID
            temperature: 温度参数
            max_tokens: 最大Token数

        Yields:
            流式输出的文本块

        Raises:
            BadRequestException: 内容违规或余额不足
        """
        # 生成任务ID (用于关联预冻结和结算)
        task_id = str(uuid.uuid4())

        # 获取模型名称
        model_name = await self._get_model_name(model_id)

        # ========== 第1步: 前置内容审查 ==========
        moderation_result = await self.moderation.check_input(message)
        if not moderation_result["passed"]:
            raise BadRequestException(
                f"输入内容包含违规词汇: {moderation_result['matched_word']}"
            )

        # ========== 第2步: 余额预检并预冻结 ==========
        try:
            freeze_info = await self.balance_checker.check_and_freeze(
                user_id=user_id,
                model_id=model_id,
                input_text=message,
                task_id=task_id,
                estimated_output_tokens=max_tokens
            )
        except BadRequestException as e:
            # 余额不足
            logger.warning(f"用户 {user_id} 余额不足: {str(e)}")
            raise

        # ========== 第3步: 调用LLM并追踪 ==========
        input_tokens = self.calculator.estimate_tokens_from_text(message)
        output_tokens = 0
        full_response = ""
        is_error = False
        error_code = None
        is_violation = False

        try:
            # 流式生成
            async for chunk in self.llm_client.generate_stream(
                prompt=message,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                # ========== 第4步: 后置内容审查 (流式) ==========
                violation_check = await self.moderation.check_stream(chunk)
                if not violation_check:
                    logger.warning(f"任务 {task_id} 流式输出检测到违规内容")
                    is_violation = True
                    break

                # 累积输出
                full_response += chunk
                output_tokens = self.calculator.estimate_tokens_from_text(full_response)

                # 实时返回给前端
                yield chunk

            # ========== 第5步: 最终结算 ==========
            if is_violation:
                # 内容违规,执行处罚
                await self.balance_checker.settle(
                    user_id=user_id,
                    task_id=task_id,
                    actual_cost=Decimal("0"),  # 处罚金额由服务内部计算
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_id=model_id,
                    model_name=model_name,
                    frozen_amount=freeze_info["frozen_amount"],
                    is_violation=True
                )
                logger.warning(f"任务 {task_id} 因内容违规被处罚")

            else:
                # 正常完成,计算实际消耗并结算
                actual_cost = await self.calculator.calculate_cost(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_id=model_id
                )

                await self.balance_checker.settle(
                    user_id=user_id,
                    task_id=task_id,
                    actual_cost=actual_cost,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_id=model_id,
                    model_name=model_name,
                    frozen_amount=freeze_info["frozen_amount"],
                    is_error=False
                )

                logger.info(
                    f"任务 {task_id} 完成 - "
                    f"输入Token: {input_tokens}, "
                    f"输出Token: {output_tokens}, "
                    f"消耗: {actual_cost} 火源币"
                )

        except Exception as e:
            # ========== 第6步: 错误处理 ==========
            logger.error(f"任务 {task_id} 发生错误: {str(e)}")
            is_error = True

            # 尝试提取错误码
            if hasattr(e, 'code'):
                error_code = e.code
            elif hasattr(e, 'status_code'):
                error_code = e.status_code

            # 全额退款
            await self.balance_checker.settle(
                user_id=user_id,
                task_id=task_id,
                actual_cost=Decimal("0"),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id,
                model_name=model_name,
                frozen_amount=freeze_info["frozen_amount"],
                is_error=True,
                error_code=error_code
            )

            # 重新抛出异常
            raise

    async def chat_non_stream(
        self,
        user_id: int,
        message: str,
        model_id: int,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> dict:
        """
        非流式对话 (完整算力扣除流程)

        Args:
            user_id: 用户ID
            message: 用户消息
            model_id: 模型ID
            system_prompt: 系统提示词
            conversation_id: 对话ID
            temperature: 温度参数
            max_tokens: 最大Token数

        Returns:
            {
                "response": str,           # AI回复
                "input_tokens": int,       # 输入Token数
                "output_tokens": int,      # 输出Token数
                "cost": Decimal,           # 消耗火源币
                "task_id": str             # 任务ID
            }
        """
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 获取模型名称
        model_name = await self._get_model_name(model_id)

        # 前置内容审查
        moderation_result = await self.moderation.check_input(message)
        if not moderation_result["passed"]:
            raise BadRequestException(
                f"输入内容包含违规词汇: {moderation_result['matched_word']}"
            )

        # 余额预检并预冻结
        freeze_info = await self.balance_checker.check_and_freeze(
            user_id=user_id,
            model_id=model_id,
            input_text=message,
            task_id=task_id,
            estimated_output_tokens=max_tokens
        )

        try:
            # 调用LLM
            response = await self.llm_client.generate_text(
                prompt=message,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 后置内容审查
            moderation_result = await self.moderation.check_output(response)
            if not moderation_result["passed"]:
                # 内容违规,执行处罚
                await self.balance_checker.settle(
                    user_id=user_id,
                    task_id=task_id,
                    actual_cost=Decimal("0"),
                    input_tokens=0,
                    output_tokens=0,
                    model_id=model_id,
                    model_name=model_name,
                    frozen_amount=freeze_info["frozen_amount"],
                    is_violation=True
                )
                raise BadRequestException(
                    f"生成内容包含违规词汇: {moderation_result['matched_word']}"
                )

            # 计算实际消耗
            input_tokens = self.calculator.estimate_tokens_from_text(message)
            output_tokens = self.calculator.estimate_tokens_from_text(response)
            actual_cost = await self.calculator.calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id
            )

            # 结算
            await self.balance_checker.settle(
                user_id=user_id,
                task_id=task_id,
                actual_cost=actual_cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id,
                model_name=model_name,
                frozen_amount=freeze_info["frozen_amount"],
                is_error=False
            )

            return {
                "response": response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": actual_cost,
                "task_id": task_id
            }

        except Exception as e:
            # 错误处理
            error_code = getattr(e, 'code', None) or getattr(e, 'status_code', None)

            await self.balance_checker.settle(
                user_id=user_id,
                task_id=task_id,
                actual_cost=Decimal("0"),
                input_tokens=0,
                output_tokens=0,
                model_id=model_id,
                model_name=model_name,
                frozen_amount=freeze_info["frozen_amount"],
                is_error=True,
                error_code=error_code
            )

            raise
