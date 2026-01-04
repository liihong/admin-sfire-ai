"""
大模型管理 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from .common import PageParams


# 提供商类型
ProviderType = Literal["openai", "anthropic", "deepseek"]


class LLMModelBase(BaseModel):
    """大模型基础信息"""
    name: str = Field(..., min_length=1, max_length=128, description="模型显示名称")
    model_id: str = Field(..., min_length=1, max_length=128, description="模型标识（API 中的模型名称）")
    provider: ProviderType = Field(..., description="提供商：openai/anthropic/deepseek")
    base_url: Optional[str] = Field(None, max_length=512, description="API 基础 URL（为空则使用默认 URL）")
    is_enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, ge=0, description="排序顺序")
    remark: Optional[str] = Field(None, description="备注")


class LLMModelCreate(LLMModelBase):
    """创建大模型请求"""
    api_key: Optional[str] = Field(None, description="API Key")


class LLMModelUpdate(BaseModel):
    """更新大模型请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    model_id: Optional[str] = Field(None, min_length=1, max_length=128)
    provider: Optional[ProviderType] = None
    api_key: Optional[str] = Field(None, description="API Key（留空则不修改）")
    base_url: Optional[str] = Field(None, max_length=512)
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    remark: Optional[str] = None


class LLMModelResponse(BaseModel):
    """大模型响应"""
    id: int = Field(..., description="模型ID")
    name: str = Field(..., description="模型显示名称")
    model_id: str = Field(..., description="模型标识")
    provider: str = Field(..., description="提供商")
    has_api_key: bool = Field(..., description="是否已配置 API Key")
    base_url: Optional[str] = Field(None, description="API 基础 URL")
    is_enabled: bool = Field(..., description="是否启用")
    total_tokens_used: int = Field(default=0, description="累计使用的 token 数")
    balance: Optional[float] = Field(None, description="账户余额")
    balance_updated_at: Optional[str] = Field(None, description="余额更新时间")
    sort_order: int = Field(..., description="排序顺序")
    remark: Optional[str] = Field(None, description="备注")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class LLMModelListResponse(BaseModel):
    """大模型列表响应"""
    list: List[LLMModelResponse] = Field(..., description="模型列表")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")


class LLMModelQueryParams(PageParams):
    """大模型查询参数"""
    name: Optional[str] = Field(None, description="模型名称（模糊查询）")
    provider: Optional[ProviderType] = Field(None, description="提供商")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class AvailableModelItem(BaseModel):
    """可用模型项（供智能体编辑页使用）"""
    id: str = Field(..., description="模型ID（字符串格式，前端需要）")
    name: str = Field(..., description="模型显示名称")
    model_id: str = Field(..., description="模型标识")
    provider: str = Field(..., description="提供商")
    max_tokens: int = Field(default=4096, description="最大 token 数（默认值）")


class BalanceRefreshResponse(BaseModel):
    """余额刷新响应"""
    balance: Optional[float] = Field(None, description="账户余额")
    balance_updated_at: Optional[str] = Field(None, description="余额更新时间")
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="提示信息")

