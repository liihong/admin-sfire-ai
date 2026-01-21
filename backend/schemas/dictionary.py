"""
数据字典 Schema - Pydantic 模型

用于 API 请求/响应验证
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============== 字典项 Schema ==============

class DictItemBase(BaseModel):
    """字典项基础模型"""
    item_value: str = Field(..., min_length=1, max_length=128, description="选项值")
    item_label: str = Field(..., min_length=1, max_length=128, description="显示标签")
    description: Optional[str] = Field(None, max_length=256, description="选项描述")
    is_enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序顺序")


class DictItemCreate(DictItemBase):
    """创建字典项请求"""
    dict_id: int = Field(..., description="关联字典ID")


class DictItemUpdate(BaseModel):
    """更新字典项请求"""
    item_value: Optional[str] = Field(None, min_length=1, max_length=128, description="选项值")
    item_label: Optional[str] = Field(None, min_length=1, max_length=128, description="显示标签")
    description: Optional[str] = Field(None, max_length=256, description="选项描述")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class DictItemResponse(DictItemBase):
    """字典项响应模型"""
    id: int = Field(..., description="字典项ID")
    dict_id: int = Field(..., description="关联字典ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class DictItemSimple(BaseModel):
    """字典项简单响应（用于下拉选项）"""
    label: str = Field(..., description="显示标签")
    value: str = Field(..., description="选项值")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_item(cls, item) -> "DictItemSimple":
        """从字典项模型转换"""
        return cls(label=item.item_label, value=item.item_value)


# ============== 字典类型 Schema ==============

class DictBase(BaseModel):
    """字典类型基础模型"""
    dict_code: str = Field(..., min_length=1, max_length=64, description="字典编码")
    dict_name: str = Field(..., min_length=1, max_length=128, description="字典名称")
    description: Optional[str] = Field(None, max_length=256, description="字典描述")
    is_enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序顺序")


class DictCreate(DictBase):
    """创建字典类型请求"""
    pass


class DictUpdate(BaseModel):
    """更新字典类型请求"""
    dict_code: Optional[str] = Field(None, min_length=1, max_length=64, description="字典编码")
    dict_name: Optional[str] = Field(None, min_length=1, max_length=128, description="字典名称")
    description: Optional[str] = Field(None, max_length=256, description="字典描述")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class DictResponse(DictBase):
    """字典类型响应模型"""
    id: int = Field(..., description="字典ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class DictWithItemsResponse(DictResponse):
    """字典类型响应（含字典项）"""
    items: List[DictItemResponse] = Field(default_factory=list, description="字典项列表")


# ============== 查询参数 Schema ==============

class DictQueryParams(BaseModel):
    """字典类型查询参数"""
    dict_code: Optional[str] = Field(None, description="字典编码（精确匹配）")
    dict_name: Optional[str] = Field(None, description="字典名称（模糊匹配）")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")


class DictItemQueryParams(BaseModel):
    """字典项查询参数"""
    dict_id: Optional[int] = Field(None, description="关联字典ID")
    dict_code: Optional[str] = Field(None, description="字典编码（精确匹配）")
    item_value: Optional[str] = Field(None, description="选项值（模糊匹配）")
    item_label: Optional[str] = Field(None, description="显示标签（模糊匹配）")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")

















