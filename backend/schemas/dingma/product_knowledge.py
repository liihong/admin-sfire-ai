"""
顶妈产品知识库（配方）管理 Schema
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ProductKnowledgeBase(BaseModel):
    """产品知识库基础字段"""

    category_code: str = Field(..., min_length=1, max_length=32, description="品类编码，如 mixian、wonton")
    category_name: str = Field(..., min_length=1, max_length=64, description="品类名称，如 米线、馄饨")
    product_code: str = Field(..., min_length=1, max_length=64, description="产品稳定编码，租户内唯一")
    product_name: str = Field(..., min_length=1, max_length=128, description="产品名称")
    aliases: Optional[List[str]] = Field(default_factory=list, description="别名列表，用于模糊匹配")
    pack_formula: Optional[str] = Field(None, description="出货配比（含克重/包数）")
    recipe_detail: Optional[Dict[str, Any]] = Field(None, description="制作详情 JSON")
    copywriting_facts: Optional[str] = Field(None, description="文案事实（含/不含/可写/不可写）")
    source_version: Optional[str] = Field(None, max_length=32, description="课件版本，如 2026-01")
    status: int = Field(default=1, ge=0, le=1, description="状态：1-启用 0-禁用")
    sort_order: int = Field(default=0, ge=0, description="排序")

    @field_validator("aliases", mode="before")
    @classmethod
    def normalize_aliases(cls, value: object) -> List[str]:
        """将空值或字符串规范为别名列表"""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return []


class ProductKnowledgeCreate(ProductKnowledgeBase):
    """创建产品知识库请求"""

    pass


class ProductKnowledgeUpdate(BaseModel):
    """更新产品知识库请求（product_code 创建后不可改）"""

    category_code: Optional[str] = Field(None, min_length=1, max_length=32, description="品类编码")
    category_name: Optional[str] = Field(None, min_length=1, max_length=64, description="品类名称")
    product_name: Optional[str] = Field(None, min_length=1, max_length=128, description="产品名称")
    aliases: Optional[List[str]] = Field(None, description="别名列表")
    pack_formula: Optional[str] = Field(None, description="出货配比")
    recipe_detail: Optional[Dict[str, Any]] = Field(None, description="制作详情 JSON")
    copywriting_facts: Optional[str] = Field(None, description="文案事实")
    source_version: Optional[str] = Field(None, max_length=32, description="课件版本")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")

    @field_validator("aliases", mode="before")
    @classmethod
    def normalize_aliases(cls, value: object) -> Optional[List[str]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return []


class ProductKnowledgeResponse(ProductKnowledgeBase):
    """产品知识库响应"""

    id: int = Field(..., description="主键 ID")
    tenant_id: int = Field(..., description="租户 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ProductKnowledgeQueryParams(BaseModel):
    """列表查询参数"""

    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=200, description="每页数量")
    category_code: Optional[str] = Field(None, description="品类编码筛选")
    product_name: Optional[str] = Field(None, description="产品名称模糊搜索")
    product_code: Optional[str] = Field(None, description="产品编码精确搜索")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态筛选")
    keyword: Optional[str] = Field(None, description="关键词（产品名/别名/编码）")


class ProductKnowledgeCategoryResponse(BaseModel):
    """品类下拉选项"""

    category_code: str = Field(..., description="品类编码")
    category_name: str = Field(..., description="品类名称")
    count: int = Field(..., description="该品类下产品数量")
