"""
顶妈产品知识库 v2 Schema
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class GuardrailSchema(BaseModel):
    """文案护栏（结构化）"""

    contains: List[str] = Field(default_factory=list, description="可写配料/成分")
    excludes: List[str] = Field(default_factory=list, description="明确不含")
    forbidden: List[str] = Field(default_factory=list, description="禁止写法")
    writable_tags: List[str] = Field(default_factory=list, description="可写卖点标签")


class ProcessCopywritingSchema(BaseModel):
    """制作过程文案结构"""

    scene_keywords: List[str] = Field(default_factory=list, description="过程场景触发词")
    focus_label: str = Field(default="", description="过程焦点名称")
    aliases: List[str] = Field(default_factory=list, description="过程场景别名")
    writable_ingredients: List[str] = Field(default_factory=list, description="过程可写配料")
    writable_actions: List[str] = Field(default_factory=list, description="过程可写动作")
    forbidden_ingredients: List[str] = Field(default_factory=list, description="过程禁写配料")
    scene_hint: str = Field(default="", description="场景提示")


class RecipeDetailSchema(BaseModel):
    ingredients: Optional[List[Dict[str, Any]]] = None
    steps: Optional[List[str]] = None
    notes: Optional[List[str]] = None


class SkuComponentLinkSchema(BaseModel):
    """SKU 组件关联"""

    component_code: str
    component_name: Optional[str] = None
    role: str = "other"
    process_focus: bool = False
    display_label: Optional[str] = None
    sort_order: int = 0


# ---------- Component ----------

class ComponentBase(BaseModel):
    component_code: str = Field(..., min_length=1, max_length=64)
    component_name: str = Field(..., min_length=1, max_length=128)
    component_type: str = Field(default="sauce", max_length=32)
    aliases: Optional[List[str]] = Field(default_factory=list)
    pack_formula: Optional[str] = None
    recipe_detail: Optional[Dict[str, Any]] = None
    guardrail: Optional[GuardrailSchema] = None
    process_copywriting: Optional[ProcessCopywritingSchema] = None
    source_version: Optional[str] = Field(None, max_length=32)
    status: int = Field(default=1, ge=0, le=1)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("aliases", mode="before")
    @classmethod
    def normalize_aliases(cls, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(BaseModel):
    component_name: Optional[str] = Field(None, min_length=1, max_length=128)
    component_type: Optional[str] = Field(None, max_length=32)
    aliases: Optional[List[str]] = None
    pack_formula: Optional[str] = None
    recipe_detail: Optional[Dict[str, Any]] = None
    guardrail: Optional[GuardrailSchema] = None
    process_copywriting: Optional[ProcessCopywritingSchema] = None
    source_version: Optional[str] = Field(None, max_length=32)
    status: Optional[int] = Field(None, ge=0, le=1)
    sort_order: Optional[int] = Field(None, ge=0)


class ComponentResponse(ComponentBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ComponentQueryParams(BaseModel):
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=200)
    component_type: Optional[str] = None
    status: Optional[int] = Field(None, ge=0, le=1)
    keyword: Optional[str] = None


# ---------- SKU ----------

class SkuBase(BaseModel):
    sku_code: str = Field(..., min_length=1, max_length=64)
    sku_name: str = Field(..., min_length=1, max_length=128)
    category_code: str = Field(..., min_length=1, max_length=32)
    category_name: str = Field(..., min_length=1, max_length=64)
    aliases: Optional[List[str]] = Field(default_factory=list)
    pack_formula: Optional[str] = None
    guardrail: Optional[GuardrailSchema] = None
    process_copywriting: Optional[ProcessCopywritingSchema] = None
    source_version: Optional[str] = Field(None, max_length=32)
    status: int = Field(default=1, ge=0, le=1)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("aliases", mode="before")
    @classmethod
    def normalize_aliases(cls, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []


class SkuCreate(SkuBase):
    component_links: Optional[List[SkuComponentLinkSchema]] = Field(
        default_factory=list, description="组件关联"
    )


class SkuUpdate(BaseModel):
    sku_name: Optional[str] = Field(None, min_length=1, max_length=128)
    category_code: Optional[str] = Field(None, min_length=1, max_length=32)
    category_name: Optional[str] = Field(None, min_length=1, max_length=64)
    aliases: Optional[List[str]] = None
    pack_formula: Optional[str] = None
    guardrail: Optional[GuardrailSchema] = None
    process_copywriting: Optional[ProcessCopywritingSchema] = None
    source_version: Optional[str] = Field(None, max_length=32)
    status: Optional[int] = Field(None, ge=0, le=1)
    sort_order: Optional[int] = Field(None, ge=0)
    component_links: Optional[List[SkuComponentLinkSchema]] = None


class SkuResponse(SkuBase):
    id: int
    tenant_id: int
    component_links: List[SkuComponentLinkSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SkuQueryParams(BaseModel):
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=200)
    category_code: Optional[str] = None
    status: Optional[int] = Field(None, ge=0, le=1)
    keyword: Optional[str] = None


class SkuCategoryResponse(BaseModel):
    category_code: str
    category_name: str
    count: int
