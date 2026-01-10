"""
火源币计算配置常量
定义算力计算的核心参数和公式

算力计算公式:
消耗火源币 = [(输入Token数 × 输入权重) + (输出Token数 × 输出权重) + 基础调度费] × 模型倍率系数
"""
from decimal import Decimal


class CoinConfig:
    """火源币配置常量"""

    # Token与火源币的换算基础比例 (1 Token = 0.001 火源币)
    TOKEN_TO_COIN_RATE = Decimal("0.001")

    # 默认权重配置
    DEFAULT_INPUT_WEIGHT = Decimal("1.0")    # 输入Token权重
    DEFAULT_OUTPUT_WEIGHT = Decimal("3.0")   # 输出Token权重 (输出成本是输入的3倍)
    DEFAULT_BASE_FEE = Decimal("10.0")       # 基础调度费(火源币)

    # 模型默认倍率
    DEFAULT_RATE_MULTIPLIER = Decimal("1.0")

    # 内容违规处罚费用 (基础调度费的倍数)
    VIOLATION_PENALTY_MULTIPLIER = Decimal("0.1")

    # 预冻结估算系数 (按最大输出Token数的倍数预冻结)
    FREEZE_ESTIMATE_MULTIPLIER = Decimal("1.5")

    # 错误码免单配置
    FREE_ERROR_CODES = [500, 502, 503, 504]

    # 字符数到Token的估算比例
    # 中文约1字符=0.6Token, 英文约1字符=0.25Token
    CHAR_TO_TOKEN_RATIO_ZH = Decimal("0.6")
    CHAR_TO_TOKEN_RATIO_EN = Decimal("0.25")

    # 混合文本平均比例
    CHAR_TO_TOKEN_RATIO_MIXED = Decimal("0.4")

    @classmethod
    def calculate_default_cost(cls, input_tokens: int, output_tokens: int) -> Decimal:
        """
        使用默认配置计算算力消耗

        Args:
            input_tokens: 输入Token数
            output_tokens: 输出Token数

        Returns:
            消耗的火源币数量
        """
        base_cost = (
            Decimal(input_tokens) * cls.DEFAULT_INPUT_WEIGHT +
            Decimal(output_tokens) * cls.DEFAULT_OUTPUT_WEIGHT +
            cls.DEFAULT_BASE_FEE
        ) * cls.TOKEN_TO_COIN_RATE

        return round(base_cost, 4)

    @classmethod
    def estimate_tokens_from_text(cls, text: str) -> int:
        """
        从文本估算Token数

        Args:
            text: 输入文本

        Returns:
            估算的Token数
        """
        if not text:
            return 0

        # 统计中文字符数
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # 统计非中文字符数
        other_chars = len(text) - chinese_chars

        # 计算估算Token数
        estimated_tokens = (
            chinese_chars * cls.CHAR_TO_TOKEN_RATIO_ZH +
            other_chars * cls.CHAR_TO_TOKEN_RATIO_EN
        )

        return int(estimated_tokens) + 1  # 至少1个Token

    @classmethod
    def calculate_violation_penalty(cls, base_fee: Decimal) -> Decimal:
        """
        计算内容违规处罚费用

        Args:
            base_fee: 基础调度费

        Returns:
            处罚费用
        """
        return round(base_fee * cls.VIOLATION_PENALTY_MULTIPLIER, 4)


# 预设模型倍率配置
MODEL_RATE_CONFIGS = {
    # Claude系列
    "claude-3-5-sonnet": {
        "rate_multiplier": Decimal("1.0"),
        "input_weight": Decimal("1.0"),
        "output_weight": Decimal("3.0"),
        "base_fee": Decimal("10.0"),
    },
    "claude-3-opus": {
        "rate_multiplier": Decimal("2.0"),
        "input_weight": Decimal("1.5"),
        "output_weight": Decimal("4.0"),
        "base_fee": Decimal("20.0"),
    },
    "claude-3-haiku": {
        "rate_multiplier": Decimal("0.25"),
        "input_weight": Decimal("0.8"),
        "output_weight": Decimal("2.0"),
        "base_fee": Decimal("5.0"),
    },

    # GPT系列
    "gpt-4o": {
        "rate_multiplier": Decimal("1.5"),
        "input_weight": Decimal("1.2"),
        "output_weight": Decimal("3.5"),
        "base_fee": Decimal("15.0"),
    },
    "gpt-4o-mini": {
        "rate_multiplier": Decimal("0.1"),
        "input_weight": Decimal("0.5"),
        "output_weight": Decimal("1.5"),
        "base_fee": Decimal("2.0"),
    },
    "gpt-4-turbo": {
        "rate_multiplier": Decimal("1.8"),
        "input_weight": Decimal("1.3"),
        "output_weight": Decimal("3.8"),
        "base_fee": Decimal("18.0"),
    },
    "gpt-3.5-turbo": {
        "rate_multiplier": Decimal("0.2"),
        "input_weight": Decimal("0.6"),
        "output_weight": Decimal("1.8"),
        "base_fee": Decimal("3.0"),
    },

    # DeepSeek系列
    "deepseek-chat": {
        "rate_multiplier": Decimal("0.15"),
        "input_weight": Decimal("0.7"),
        "output_weight": Decimal("2.0"),
        "base_fee": Decimal("3.0"),
    },
    "deepseek-coder": {
        "rate_multiplier": Decimal("0.15"),
        "input_weight": Decimal("0.7"),
        "output_weight": Decimal("2.0"),
        "base_fee": Decimal("3.0"),
    },

    # 其他模型
    "default": {
        "rate_multiplier": Decimal("1.0"),
        "input_weight": Decimal("1.0"),
        "output_weight": Decimal("3.0"),
        "base_fee": Decimal("10.0"),
    }
}
