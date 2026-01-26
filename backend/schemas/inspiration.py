"""
Inspiration Schema - 灵感 Pydantic 模型

用于 API 请求/响应验证
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .common import PageParams


# ============== 基础 Schema ==============

class InspirationBase(BaseModel):
    """灵感基础模型"""
    content: str = Field(..., min_length=1, max_length=500, description="灵感内容（限制500字符）")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表（如 [\"#视频脚本\", \"#文案想法\"]）")
    project_id: Optional[int] = Field(None, description="项目ID（可选）")
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """验证内容长度"""
        if len(v) > 500:
            raise ValueError('灵感内容不能超过500字符')
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """验证标签"""
        if v is None:
            return []
        if len(v) > 10:
            raise ValueError('标签数量不能超过10个')
        for tag in v:
            if len(tag) > 20:
                raise ValueError('单个标签长度不能超过20字符')
            # 标签格式验证（可选，根据实际需求调整）
            # if not tag.startswith('#'):
            #     raise ValueError('标签必须以#开头')
        return v


class InspirationCreate(InspirationBase):
    """创建灵感请求模型"""
    pass


class InspirationUpdate(BaseModel):
    """更新灵感请求模型"""
    content: Optional[str] = Field(None, min_length=1, max_length=500, description="灵感内容")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    project_id: Optional[int] = Field(None, description="项目ID")
    status: Optional[str] = Field(None, description="状态：active/archived/deleted")
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v: Optional[str]) -> Optional[str]:
        """验证内容长度"""
        if v is not None and len(v) > 500:
            raise ValueError('灵感内容不能超过500字符')
        return v.strip() if v else None


class InspirationResponse(BaseModel):
    """灵感响应模型"""
    id: int = Field(..., description="灵感ID")
    user_id: int = Field(..., description="用户ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    content: str = Field(..., description="灵感内容")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    status: str = Field(..., description="状态：active/archived/deleted")
    is_pinned: bool = Field(default=False, description="是否置顶")
    generated_content: Optional[str] = Field(None, description="已生成的口播文案")
    generated_at: Optional[datetime] = Field(None, description="生成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    # 关联对象（可选）
    project_name: Optional[str] = Field(None, description="项目名称")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_project(cls, obj) -> "InspirationResponse":
        """从ORM对象创建响应，包含项目信息"""
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "project_id": obj.project_id,
            "content": obj.content,
            "tags": obj.get_tags_list() if hasattr(obj, 'get_tags_list') else (obj.tags or []),
            "status": obj.status,
            "is_pinned": obj.is_pinned,
            "generated_content": obj.generated_content,
            "generated_at": obj.generated_at,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "project_name": obj.project.name if obj.project else None,
        }
        return cls(**data)


class InspirationQueryParams(PageParams):
    """灵感查询参数"""
    status: Optional[str] = Field(None, description="状态筛选：active/archived/deleted")
    project_id: Optional[int] = Field(None, description="项目ID筛选")
    tag: Optional[str] = Field(None, description="标签筛选（单个标签）")
    keyword: Optional[str] = Field(None, description="关键词搜索（内容搜索）")
    is_pinned: Optional[bool] = Field(None, description="是否置顶筛选")
    sort_by: Optional[str] = Field(default="created_at", description="排序字段：created_at/pinned")
    sort_order: Optional[str] = Field(default="desc", description="排序方向：asc/desc")


class InspirationGenerateRequest(BaseModel):
    """生成口播文案请求模型"""
    inspiration_id: int = Field(..., description="灵感ID")
    agent_type: Optional[str] = Field(default="ip_collector", description="智能体类型")
    model_type: Optional[str] = Field(None, description="模型类型（可选，不传则使用智能体配置的模型）")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="最大生成tokens")


class InspirationGenerateResponse(BaseModel):
    """生成口播文案响应模型"""
    success: bool = Field(..., description="是否成功")
    content: str = Field(..., description="生成的口播文案")
    inspiration_id: int = Field(..., description="灵感ID")
    agent_type: str = Field(..., description="使用的智能体类型")
    model_type: str = Field(..., description="使用的模型类型")


class InspirationPinRequest(BaseModel):
    """置顶/取消置顶请求模型"""
    is_pinned: bool = Field(..., description="是否置顶")


class InspirationArchiveRequest(BaseModel):
    """归档/取消归档请求模型"""
    status: str = Field(..., description="状态：active/archived")

