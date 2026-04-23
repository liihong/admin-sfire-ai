"""
Copywriting Library Schema - 文案库 Pydantic 模型

注意：此模块为独立业务线，不依赖 inspirations / AI对话等体系。
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .common import PageParams
from models.copywriting_library import CopywritingEntryStatus


class CopywritingEntryBase(BaseModel):
    """文案库条目基础字段"""

    project_id: int = Field(..., description="项目/IP ID（必填）")
    content: str = Field(..., min_length=1, max_length=200000, description="文案正文")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签数组（自由输入）")
    status: Optional[str] = Field(
        default=None,
        description=f"状态：{', '.join([e.value for e in CopywritingEntryStatus])}",
    )

    @field_validator("content")
    @classmethod
    def _clean_content(cls, v: str) -> str:
        # 保留用户换行，但去掉首尾空白
        return (v or "").strip()

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            return []
        if len(v) > 20:
            raise ValueError("标签数量不能超过20个")
        cleaned: List[str] = []
        for t in v:
            s = str(t).strip()
            if not s:
                continue
            if len(s) > 30:
                raise ValueError("单个标签长度不能超过30字符")
            cleaned.append(s)
        return cleaned

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {e.value for e in CopywritingEntryStatus}
        if v not in allowed:
            raise ValueError(f"无效的状态值: {v}")
        return v


class CopywritingEntryCreate(CopywritingEntryBase):
    """创建文案库条目请求（最小必填：content + project_id）"""


class CopywritingEntryUpdate(BaseModel):
    """更新文案库条目请求"""

    content: Optional[str] = Field(None, min_length=1, max_length=200000, description="文案正文")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    status: Optional[str] = Field(None, description="状态：draft/todo/published/archived")

    @field_validator("content")
    @classmethod
    def _clean_content(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        if len(v) > 20:
            raise ValueError("标签数量不能超过20个")
        cleaned: List[str] = []
        for t in v:
            s = str(t).strip()
            if not s:
                continue
            if len(s) > 30:
                raise ValueError("单个标签长度不能超过30字符")
            cleaned.append(s)
        return cleaned

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {e.value for e in CopywritingEntryStatus}
        if v not in allowed:
            raise ValueError(f"无效的状态值: {v}")
        return v


class CopywritingPublishDataUpdate(BaseModel):
    """补录发布后数据"""

    views: Optional[int] = Field(None, ge=0, description="播放/曝光量")
    likes: Optional[int] = Field(None, ge=0, description="点赞数")
    comments: Optional[int] = Field(None, ge=0, description="评论数")
    shares: Optional[int] = Field(None, ge=0, description="转发/分享数")
    published_at: Optional[datetime] = Field(None, description="发布时间（可选）")


class CopywritingEntryResponse(BaseModel):
    """文案库条目响应"""

    id: int
    user_id: int
    project_id: int
    content: str
    tags: List[str] = Field(default_factory=list)
    status: str

    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    published_at: Optional[datetime] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_project(cls, obj) -> "CopywritingEntryResponse":
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            project_id=obj.project_id,
            content=obj.content,
            tags=obj.get_tags_list() if hasattr(obj, "get_tags_list") else (obj.tags or []),
            status=obj.status,
            views=obj.views,
            likes=obj.likes,
            comments=obj.comments,
            shares=obj.shares,
            published_at=obj.published_at,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            project_name=getattr(obj.project, "name", None) if getattr(obj, "project", None) else None,
        )


class CopywritingEntryQueryParams(PageParams):
    """文案库查询参数"""

    project_id: Optional[int] = Field(None, description="项目ID筛选（必传时可强制）")
    status: Optional[str] = Field(None, description="状态筛选：draft/todo/published/archived")
    tag: Optional[str] = Field(None, description="标签筛选（单个标签）")
    keyword: Optional[str] = Field(None, description="关键词搜索（content LIKE）")
    sort_by: Optional[str] = Field(default="created_at", description="排序字段：created_at/updated_at")
    sort_order: Optional[str] = Field(default="desc", description="排序方向：asc/desc")

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {e.value for e in CopywritingEntryStatus}
        if v not in allowed:
            raise ValueError(f"无效的状态值: {v}")
        return v

