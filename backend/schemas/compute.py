"""
Compute Log Pydantic Schemas
算力流水相关 Schema 定义
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# 算力变动类型
ComputeTypeStr = Literal[
    "recharge",      # 充值
    "consume",       # 消耗
    "refund",        # 退款
    "reward",        # 奖励
    "freeze",        # 冻结
    "unfreeze",      # 解冻
    "transfer_in",   # 转入
    "transfer_out",  # 转出
    "commission",    # 分销佣金
    "adjustment",    # 管理员调整
]


class AdjustBalanceRequest(BaseModel):
    """
    算力调整请求
    POST /api/v1/users/{id}/adjust-balance
    """
    amount: Decimal = Field(..., description="调整金额（正数增加，负数减少）")
    remark: Optional[str] = Field(None, max_length=500, description="调整备注/原因")


class ComputeLogResponse(BaseModel):
    """
    算力流水响应
    对应前端显示的流水记录
    """
    id: str = Field(..., description="流水ID")
    userId: str = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    type: str = Field(..., description="变动类型")
    typeName: str = Field(..., description="变动类型名称")
    amount: float = Field(..., description="变动金额")
    beforeBalance: float = Field(..., description="变动前余额")
    afterBalance: float = Field(..., description="变动后余额")
    remark: Optional[str] = Field(None, description="备注")
    orderId: Optional[str] = Field(None, description="关联订单ID")
    taskId: Optional[str] = Field(None, description="关联任务ID")
    operatorId: Optional[str] = Field(None, description="操作人ID")
    operatorName: Optional[str] = Field(None, description="操作人名称")
    source: Optional[str] = Field(None, description="来源")
    createTime: str = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ComputeLogListResponse(BaseModel):
    """算力流水列表响应"""
    list: List[ComputeLogResponse] = Field(..., description="流水列表")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")


class ComputeLogQueryParams(BaseModel):
    """算力流水查询参数"""
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")
    userId: Optional[str] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名（模糊查询）")
    type: Optional[ComputeTypeStr] = Field(None, description="变动类型")
    startTime: Optional[str] = Field(None, description="开始时间")
    endTime: Optional[str] = Field(None, description="结束时间")
    minAmount: Optional[Decimal] = Field(None, description="最小金额")
    maxAmount: Optional[Decimal] = Field(None, description="最大金额")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.pageNum - 1) * self.pageSize


class ComputeTypeOption(BaseModel):
    """算力变动类型选项"""
    label: str = Field(..., description="显示标签")
    value: str = Field(..., description="类型值")
    color: Optional[str] = Field(None, description="显示颜色")


class ComputeStatistics(BaseModel):
    """算力统计信息"""
    totalRecharge: Decimal = Field(default=Decimal("0"), description="总充值")
    totalConsume: Decimal = Field(default=Decimal("0"), description="总消耗")
    totalRefund: Decimal = Field(default=Decimal("0"), description="总退款")
    totalReward: Decimal = Field(default=Decimal("0"), description="总奖励")
    totalCommission: Decimal = Field(default=Decimal("0"), description="总佣金")
    totalAdjustment: Decimal = Field(default=Decimal("0"), description="总调整")





