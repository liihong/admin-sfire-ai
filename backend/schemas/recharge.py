"""
充值相关数据验证模型
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List
from datetime import datetime


class RechargePackageResponse(BaseModel):
    """套餐响应模型"""
    id: int = Field(description="套餐ID")
    name: str = Field(description="套餐名称")
    price: Decimal = Field(description="销售价格（元）")
    power_amount: Decimal = Field(description="获得算力（火源币）")
    unit_price: Optional[str] = Field(default=None, description="实际单价（1:121格式）")
    tag: Optional[List[str]] = Field(default=None, description="标签列表")
    description: Optional[str] = Field(default=None, description="运营建议/描述")
    article_count: Optional[int] = Field(default=None, description="约可生成文案数量")
    sort_order: int = Field(default=0, description="排序")
    status: int = Field(description="状态：0-禁用, 1-启用")
    is_popular: bool = Field(default=False, description="是否主推款")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "爆款合伙人",
                "price": 99.00,
                "power_amount": 15000,
                "unit_price": "1:151",
                "tag": ["最划算", "80%用户选择"],
                "description": "主推款。价格在百元内，性价比最高。",
                "article_count": 500,
                "sort_order": 3,
                "status": 1,
                "is_popular": True
            }
        }


class RechargePackageCreate(BaseModel):
    """套餐创建模型（管理后台用）"""
    name: str = Field(min_length=1, max_length=128, description="套餐名称")
    price: Decimal = Field(gt=0, description="销售价格（元）")
    power_amount: Decimal = Field(gt=0, description="获得算力（火源币）")
    unit_price: Optional[str] = Field(default=None, max_length=32, description="实际单价")
    tag: Optional[List[str]] = Field(default=None, description="标签列表")
    description: Optional[str] = Field(default=None, description="运营建议/描述")
    article_count: Optional[int] = Field(default=None, ge=0, description="约可生成文案数量")
    sort_order: int = Field(default=0, description="排序")
    status: int = Field(default=1, ge=0, le=1, description="状态：0-禁用, 1-启用")
    is_popular: bool = Field(default=False, description="是否主推款")


class RechargePackageUpdate(BaseModel):
    """套餐更新模型"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=128, description="套餐名称")
    price: Optional[Decimal] = Field(default=None, gt=0, description="销售价格（元）")
    power_amount: Optional[Decimal] = Field(default=None, gt=0, description="获得算力（火源币）")
    unit_price: Optional[str] = Field(default=None, max_length=32, description="实际单价")
    tag: Optional[List[str]] = Field(default=None, description="标签列表")
    description: Optional[str] = Field(default=None, description="运营建议/描述")
    article_count: Optional[int] = Field(default=None, ge=0, description="约可生成文案数量")
    sort_order: Optional[int] = Field(default=None, description="排序")
    status: Optional[int] = Field(default=None, ge=0, le=1, description="状态：0-禁用, 1-启用")
    is_popular: Optional[bool] = Field(default=None, description="是否主推款")


class RechargeOrderRequest(BaseModel):
    """创建充值订单请求"""
    package_id: int = Field(gt=0, description="套餐ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "package_id": 1
            }
        }


class RechargeOrderResponse(BaseModel):
    """订单响应模型"""
    order_id: str = Field(description="订单号")
    package_id: int = Field(description="套餐ID")
    package_name: str = Field(description="套餐名称")
    price: Decimal = Field(description="支付金额（元）")
    power_amount: Decimal = Field(description="获得算力（火源币）")
    payment_status: str = Field(description="支付状态")
    payment_params: dict = Field(description="支付参数（微信支付）")
    created_at: datetime = Field(description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "R202401011234567890",
                "package_id": 1,
                "package_name": "爆款合伙人",
                "price": 99.00,
                "power_amount": 15000,
                "payment_status": "pending",
                "payment_params": {
                    "timeStamp": "1234567890",
                    "nonceStr": "abc123",
                    "package": "prepay_id=wx1234567890",
                    "signType": "RSA",
                    "paySign": "signature"
                },
                "created_at": "2024-01-01T12:00:00"
            }
        }


class PaymentCallbackRequest(BaseModel):
    """支付回调请求（微信支付）"""
    id: Optional[str] = Field(default=None, description="微信支付回调ID")
    create_time: Optional[str] = Field(default=None, description="创建时间")
    resource_type: Optional[str] = Field(default=None, description="资源类型")
    event_type: Optional[str] = Field(default=None, description="事件类型")
    summary: Optional[str] = Field(default=None, description="摘要")
    resource: Optional[dict] = Field(default=None, description="资源数据（加密）")


class OrderStatusResponse(BaseModel):
    """订单状态响应"""
    order_id: str = Field(description="订单号")
    payment_status: str = Field(description="支付状态")
    payment_time: Optional[datetime] = Field(default=None, description="支付时间")
    wechat_transaction_id: Optional[str] = Field(default=None, description="微信交易号")
















