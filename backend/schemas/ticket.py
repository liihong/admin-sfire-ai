"""
工单相关 Pydantic Schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field

from .common import PageParams


# 工单类型
TicketTypeLiteral = Literal["membership", "recharge"]

# 工单状态（预留多种便于扩展）
TicketStatusLiteral = Literal["pending", "processing", "completed", "rejected", "failed"]

# 会员周期
PeriodTypeLiteral = Literal["monthly", "quarterly", "yearly"]


class TicketMembershipCreate(BaseModel):
    """开通会员工单创建参数"""
    level_code: str = Field(..., description="等级代码：vip/svip/max")
    vip_expire_date: str = Field(..., description="VIP到期时间，格式：YYYY-MM-DD")
    is_paid: bool = Field(..., description="是否已收费")
    payment_method: Optional[str] = Field(None, description="收费方式：微信/支付宝/对公转账等")
    voucher: Optional[str] = Field(None, description="凭证（图片URL或文字说明）")
    period_type: PeriodTypeLiteral = Field(..., description="会员周期：monthly-月度, quarterly-季度, yearly-年度")


class TicketRechargeCreate(BaseModel):
    """充值算力工单创建参数"""
    amount: Decimal = Field(..., gt=0, description="充值金额（算力点）")


class TicketCreate(BaseModel):
    """工单创建请求"""
    type: TicketTypeLiteral = Field(..., description="工单类型：membership-开通会员, recharge-充值算力")
    user_id: int = Field(..., description="目标用户ID")
    # 会员工单必填字段
    membership: Optional[TicketMembershipCreate] = Field(None, description="会员工单详情（type=membership时必填）")
    # 充值工单必填字段
    recharge: Optional[TicketRechargeCreate] = Field(None, description="充值工单详情（type=recharge时必填）")
    remark: Optional[str] = Field(None, description="备注说明")


class TicketQueryParams(PageParams):
    """工单查询参数"""
    type: Optional[TicketTypeLiteral] = Field(None, description="工单类型")
    status: Optional[TicketStatusLiteral] = Field(None, description="工单状态")
    user_id: Optional[int] = Field(None, description="目标用户ID")
    creator_id: Optional[int] = Field(None, description="创建人ID")


class TicketUserInfo(BaseModel):
    """工单关联用户简要信息"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    phone: Optional[str] = Field(None, description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")


class TicketCreatorInfo(BaseModel):
    """工单创建人简要信息"""
    id: int = Field(..., description="管理员ID")
    username: str = Field(..., description="管理员用户名")


class TicketResponse(BaseModel):
    """工单响应"""
    id: int = Field(..., description="工单ID")
    type: str = Field(..., description="工单类型")
    status: str = Field(..., description="工单状态")
    user_id: int = Field(..., description="目标用户ID")
    user: Optional[TicketUserInfo] = Field(None, description="目标用户信息")
    creator_id: int = Field(..., description="创建人ID")
    creator: Optional[TicketCreatorInfo] = Field(None, description="创建人信息")
    handler_id: Optional[int] = Field(None, description="处理人ID")
    handler: Optional[TicketCreatorInfo] = Field(None, description="处理人信息")
    # 会员工单字段
    is_paid: Optional[bool] = Field(None, description="是否已收费")
    payment_method: Optional[str] = Field(None, description="收费方式")
    voucher: Optional[str] = Field(None, description="凭证")
    period_type: Optional[str] = Field(None, description="会员周期")
    # 扩展数据（解析后）
    extra_data: Optional[dict] = Field(None, description="扩展数据：level_code/vip_expire_date 或 amount")
    remark: Optional[str] = Field(None, description="备注")
    handled_at: Optional[datetime] = Field(None, description="处理时间")
    fail_reason: Optional[str] = Field(None, description="处理失败原因")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
