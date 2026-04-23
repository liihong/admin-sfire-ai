"""
项目对标抖音账号 — Pydantic 模型
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkAccountCreate(BaseModel):
    url: str = Field(..., min_length=8, description="抖音用户主页或分享链接")
    remark: Optional[str] = Field(None, description="备注")


class BenchmarkAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    sec_uid: str
    profile_url: str
    nickname: str
    avatar_url: str = Field(default="", description="账号头像 URL")
    signature: str = Field(default="", description="账号简介")
    follower_count: int = Field(default=0, description="粉丝数")
    following_count: int = Field(default=0, description="关注数")
    total_favorited: int = Field(default=0, description="获赞总数")
    aweme_count: int = Field(default=0, description="作品数")
    remark: Optional[str]
    is_enabled: bool


class BenchmarkVideoItem(BaseModel):
    aweme_id: str
    is_top: int = Field(default=0, description="是否置顶：1-置顶，0-普通")
    desc: str = Field(default="", description="作品文案/描述")
    create_time: int = Field(default=0, description="创建时间（秒级时间戳，若接口未返回则为 0）")
    cover_url: str = Field(default="", description="封面图 URL")
    digg_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    collect_count: int = Field(default=0, description="收藏数")
    play_count: int = Field(default=0, description="播放数")
    duration: int = Field(default=0, description="视频时长（秒）")
    author_nickname: str = Field(default="", description="作者昵称")
    author_avatar_url: str = Field(default="", description="作者头像 URL")
    video_url: str = Field(default="", description="视频直链（若可用）")
    share_url: str = Field(default="", description="抖音分享页链接（若可用）")


class BenchmarkVideoListResponse(BaseModel):
    items: List[BenchmarkVideoItem]
    next_cursor: int = Field(0, description="下一页游标")
    has_more: bool = Field(False, description="是否还有更多")
