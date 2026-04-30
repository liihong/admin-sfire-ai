"""租户管理 Schema"""
from typing import Optional, List
from pydantic import BaseModel, Field

from .common import PageParams


class TenantCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=64, description="租户代码（英文唯一）")
    name: str = Field(..., min_length=1, max_length=128, description="租户名称")
    is_default: bool = Field(False, description="是否主租户（全局仅能有一条 True）")
    remark: Optional[str] = Field(None, description="备注")
    wechat_app_id: Optional[str] = Field(None, max_length=64, description="微信小程序 AppID（可选）")
    wechat_app_secret: Optional[str] = Field(
        None,
        max_length=128,
        description="微信小程序 AppSecret（独立小程序时填写；与 WECHAT_APP_ID 相同时可省略，用 .env Secret）",
    )


class TenantUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    is_default: Optional[bool] = None
    remark: Optional[str] = None
    wechat_app_id: Optional[str] = Field(None, max_length=64)
    wechat_app_secret: Optional[str] = Field(
        None,
        max_length=128,
        description="更新时传入非空字符串则写入；不传则保持不变",
    )


class TenantResponse(BaseModel):
    id: int
    code: str
    name: str
    is_default: bool
    remark: Optional[str] = None
    wechat_app_id: Optional[str] = None
    wechat_secret_configured: bool = Field(False, description="是否已配置独立小程序 AppSecret（或由 .env 接管）")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class TenantOption(BaseModel):
    """下拉选项"""

    id: int = Field(..., description="租户 ID")
    code: str
    name: str


class TenantQueryParams(PageParams):
    code: Optional[str] = Field(None, description="代码模糊查询")
    name: Optional[str] = Field(None, description="名称模糊查询")

