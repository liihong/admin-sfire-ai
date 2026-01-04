"""
首页配置 Pydantic Schemas
首页配置相关数据结构定义
"""
from typing import Optional, List, Literal, Any, Dict
from pydantic import BaseModel, Field

# 配置类型
ConfigType = Literal["string", "json", "array"]


class HomeConfigBase(BaseModel):
    """首页配置基础信息"""
    config_key: str = Field(..., min_length=1, max_length=64, description="配置键")
    config_value: Optional[str] = Field(None, description="配置值（JSON格式字符串）")
    config_type: ConfigType = Field(default="string", description="配置类型")
    description: Optional[str] = Field(None, max_length=256, description="配置说明")
    is_enabled: bool = Field(default=True, description="是否启用")


class HomeConfigUpdate(BaseModel):
    """更新首页配置请求"""
    config_value: Optional[str] = Field(None, description="配置值（JSON格式字符串）")
    config_type: Optional[ConfigType] = None
    description: Optional[str] = Field(None, max_length=256)
    is_enabled: Optional[bool] = None


class HomeConfigResponse(BaseModel):
    """首页配置响应数据"""
    id: int = Field(..., description="配置ID")
    config_key: str = Field(..., description="配置键")
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field(..., description="配置类型")
    description: Optional[str] = Field(None, description="配置说明")
    is_enabled: bool = Field(..., description="是否启用")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class HomeConfigListResponse(BaseModel):
    """首页配置列表响应"""
    list: List[HomeConfigResponse] = Field(..., description="配置列表")
    total: int = Field(..., description="总数量")


class HomeConfigBatchUpdate(BaseModel):
    """批量更新首页配置请求"""
    configs: List[Dict[str, Any]] = Field(
        ...,
        description="配置列表，格式: [{'config_key': 'home_title', 'config_value': '...', ...}, ...]"
    )

