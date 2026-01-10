"""
火源币相关数据验证模型
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional


class CoinBalanceResponse(BaseModel):
    """算力余额响应"""
    balance: Decimal = Field(description="总余额")
    frozen_balance: Decimal = Field(description="冻结余额")
    available_balance: Decimal = Field(description="可用余额")

    class Config:
        json_schema_extra = {
            "example": {
                "balance": 1000.00,
                "frozen_balance": 50.00,
                "available_balance": 950.00
            }
        }


class CoinCostRequest(BaseModel):
    """算力计算请求"""
    input_tokens: int = Field(ge=0, description="输入Token数")
    output_tokens: int = Field(ge=0, description="输出Token数")
    model_id: int = Field(description="模型ID")

    class Config:
        json_schema_extra = {
            "example": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "model_id": 1
            }
        }


class CoinEstimateRequest(BaseModel):
    """算力估算请求"""
    input_text: str = Field(min_length=1, description="输入文本")
    model_id: int = Field(description="模型ID")
    estimated_output_tokens: Optional[int] = Field(
        default=None,
        ge=0,
        description="预估输出Token数(可选,不填则使用最大值)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "input_text": "你好,请介绍一下Python",
                "model_id": 1,
                "estimated_output_tokens": None
            }
        }


class CoinCostResponse(BaseModel):
    """算力计算响应"""
    estimated_cost: Decimal = Field(description="预估消耗火源币")
    breakdown: Optional[dict] = Field(default=None, description="费用明细")


class CoinTransactionLogResponse(BaseModel):
    """算力流水响应"""
    id: int
    type: str
    type_name: str
    amount: Decimal
    before_balance: Decimal
    after_balance: Decimal
    remark: Optional[str]
    task_id: Optional[str]
    created_at: str


class CoinRechargeRequest(BaseModel):
    """算力充值请求(管理员)"""
    user_id: int = Field(description="用户ID")
    amount: Decimal = Field(gt=0, description="充值金额")
    remark: Optional[str] = Field(default=None, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "amount": 100.00,
                "remark": "活动奖励"
            }
        }


class CoinAdjustRequest(BaseModel):
    """算力调整请求(管理员)"""
    user_id: int = Field(description="用户ID")
    amount: Decimal = Field(description="调整金额(正数增加,负数减少)")
    remark: str = Field(description="调整原因")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "amount": -50.00,
                "remark": "异常扣费退回"
            }
        }
