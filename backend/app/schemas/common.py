"""
Common Pydantic Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """分页参数"""
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.pageNum - 1) * self.pageSize


class Token(BaseModel):
    """令牌响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenData(BaseModel):
    """令牌数据"""
    sub: Optional[str] = Field(None, description="用户标识")
    exp: Optional[int] = Field(None, description="过期时间戳")
    type: Optional[str] = Field(None, description="令牌类型")


class IDRequest(BaseModel):
    """ID 请求"""
    id: int = Field(..., description="ID")


class IDsRequest(BaseModel):
    """批量 ID 请求"""
    ids: list[int] = Field(..., description="ID列表")



