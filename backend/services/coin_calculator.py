"""
火源币计算服务
实现从Token到火源币的换算逻辑
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.llm_model import LLMModel
from constants.coin_config import CoinConfig, MODEL_RATE_CONFIGS


class CoinCalculatorService:
    """火源币计算服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = CoinConfig()

    async def get_model_config(self, model_id: int) -> Optional[LLMModel]:
        """
        获取模型配置

        Args:
            model_id: 模型ID

        Returns:
            模型配置对象
        """
        result = await self.db.execute(
            select(LLMModel).where(LLMModel.id == model_id)
        )
        return result.scalar_one_or_none()

    async def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_id: int
    ) -> Decimal:
        """
        根据实际Token数和模型配置计算算力消耗

        计算公式:
        消耗火源币 = [(输入Token数 × 输入权重) + (输出Token数 × 输出权重) + 基础调度费] × 模型倍率系数 × Token换算比例

        Args:
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID

        Returns:
            消耗的火源币数量
        """
        # 获取模型配置
        model = await self.get_model_config(model_id)
        if not model:
            logger.warning(f"模型ID {model_id} 不存在,使用默认配置")
            return self.config.calculate_default_cost(input_tokens, output_tokens)

        # 计算基础成本
        base_cost = (
            Decimal(input_tokens) * Decimal(model.input_weight) +
            Decimal(output_tokens) * Decimal(model.output_weight) +
            Decimal(model.base_fee)
        )

        # 应用倍率系数
        total_cost = base_cost * Decimal(model.rate_multiplier) * self.config.TOKEN_TO_COIN_RATE

        # 四舍五入到整数
        return round(total_cost)

    async def estimate_max_cost(
        self,
        model_id: int,
        input_text: str,
        estimated_output_tokens: Optional[int] = None
    ) -> Decimal:
        """
        预估最大消耗(用于预冻结)

        Args:
            model_id: 模型ID
            input_text: 输入文本
            estimated_output_tokens: 预估输出Token数(如果不提供则使用模型最大值)

        Returns:
            预估的最大火源币消耗
        """
        # 获取模型配置
        model = await self.get_model_config(model_id)
        if not model:
            logger.warning(f"模型ID {model_id} 不存在,使用默认配置")
            max_output = 4096
        else:
            max_output = model.max_tokens_per_request

        # 估算输入Token数
        input_tokens = self.config.estimate_tokens_from_text(input_text)

        # 确定输出Token数
        if estimated_output_tokens is None:
            # 使用预冻结估算系数
            output_tokens = int(max_output * self.config.FREEZE_ESTIMATE_MULTIPLIER)
        else:
            output_tokens = estimated_output_tokens

        # 计算最大消耗
        max_cost = await self.calculate_cost(input_tokens, output_tokens, model_id)

        logger.debug(
            f"预冻结估算: 输入Token={input_tokens}, "
            f"预估输出Token={output_tokens}, 预冻结金额={max_cost}"
        )

        return max_cost

    def estimate_tokens_from_text(self, text: str) -> int:
        """
        从文本估算Token数

        Args:
            text: 输入文本

        Returns:
            估算的Token数
        """
        return self.config.estimate_tokens_from_text(text)

    async def calculate_violation_penalty(
        self,
        model_id: int
    ) -> Decimal:
        """
        计算内容违规处罚费用

        Args:
            model_id: 模型ID

        Returns:
            处罚费用
        """
        model = await self.get_model_config(model_id)
        if not model:
            base_fee = self.config.DEFAULT_BASE_FEE
        else:
            base_fee = Decimal(model.base_fee)

        return self.config.calculate_violation_penalty(base_fee)

    def get_cost_breakdown(
        self,
        input_tokens: int,
        output_tokens: int,
        model_id: int,
        model_config: Optional[LLMModel] = None
    ) -> dict:
        """
        获取费用明细

        Args:
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
            model_config: 模型配置(如果已提供则不查询数据库)

        Returns:
            费用明细字典
        """
        if model_config:
            input_weight = Decimal(model_config.input_weight)
            output_weight = Decimal(model_config.output_weight)
            base_fee = Decimal(model_config.base_fee)
            rate_multiplier = Decimal(model_config.rate_multiplier)
        else:
            # 使用默认值
            input_weight = self.config.DEFAULT_INPUT_WEIGHT
            output_weight = self.config.DEFAULT_OUTPUT_WEIGHT
            base_fee = self.config.DEFAULT_BASE_FEE
            rate_multiplier = self.config.DEFAULT_RATE_MULTIPLIER

        # 计算各项费用
        input_cost = Decimal(input_tokens) * input_weight
        output_cost = Decimal(output_tokens) * output_weight
        subtotal = input_cost + output_cost + base_fee
        total = subtotal * rate_multiplier * self.config.TOKEN_TO_COIN_RATE

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_weight": float(input_weight),
            "output_weight": float(output_weight),
            "base_fee": float(base_fee),
            "rate_multiplier": float(rate_multiplier),
            "input_cost": float(input_cost),
            "output_cost": float(output_cost),
            "subtotal": float(subtotal),
            "total": round(float(total), 4),
            "token_to_coin_rate": float(self.config.TOKEN_TO_COIN_RATE),
        }
