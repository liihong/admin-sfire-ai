"""
工具包配置 Pydantic Schemas
"""
import re
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from .common import PageParams

_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class ToolPackageBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=64, description="唯一标识（如 voice-clone）")
    name: str = Field(..., min_length=1, max_length=128, description="名称")
    description: Optional[str] = Field(None, description="描述")
    icon: str = Field(default="Microphone", max_length=64, description="Element Plus 图标名")
    sort_order: int = Field(default=0, ge=0, description="排序")
    status: int = Field(default=1, ge=0, le=1, description="0-禁用, 1-启用")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().lower()
        if not _CODE_RE.match(v):
            raise ValueError("code 仅允许小写字母、数字与连字符，且须以小写字母开头")
        return v


class ToolPackageCreate(ToolPackageBase):
    pass


class ToolPackageUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=64)
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[int] = Field(None, ge=0, le=1)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if not _CODE_RE.match(v):
            raise ValueError("code 仅允许小写字母、数字与连字符，且须以小写字母开头")
        return v


class ToolPackageQueryParams(PageParams):
    status: Optional[int] = Field(None, ge=0, le=1, description="状态筛选")
    keyword: Optional[str] = Field(None, description="名称或 code 模糊搜索")


class ToolPackageResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    icon: str
    sort_order: int
    status: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ToolPackageSortItem(BaseModel):
    id: int = Field(..., description="工具包 ID")
    sort_order: int = Field(..., ge=0, description="排序值")


class ToolPackageSortRequest(BaseModel):
    items: List[ToolPackageSortItem] = Field(..., min_length=1, description="排序项列表")
