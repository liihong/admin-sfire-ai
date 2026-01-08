"""
Project Schema - 项目（IP）Pydantic 模型

用于 API 请求/响应验证，保持与小程序端的接口兼容性
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from models.project import Project


# ============== PersonaSettings ==============

class PersonaSettings(BaseModel):
    """IP 人设配置"""
    tone: str = Field(default="专业亲和", description="语气风格：专业亲和/幽默风趣/严肃正式等")
    catchphrase: str = Field(default="", description="口头禅")
    target_audience: str = Field(default="", description="目标受众")
    benchmark_accounts: List[str] = Field(default_factory=list, description="对标账号列表")
    content_style: str = Field(default="", description="内容风格描述")
    taboos: List[str] = Field(default_factory=list, description="内容禁忌")
    keywords: List[str] = Field(default_factory=list, description="常用关键词")
    introduction: str = Field(default="", description="IP 简介")
    
    model_config = ConfigDict(from_attributes=True)


# ============== Project Schemas ==============

class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="项目名称")
    industry: str = Field(default="通用", description="赛道")
    avatar_letter: Optional[str] = Field(default=None, description="项目首字母")
    avatar_color: Optional[str] = Field(default=None, description="头像背景色")
    persona_settings: Optional[PersonaSettings] = Field(default=None, description="人设配置（嵌套方式）")


class ProjectCreate(ProjectBase):
    """
    创建项目请求模型
    
    支持两种传参方式：
    1. 嵌套方式: persona_settings: { tone: "xxx", introduction: "xxx" }
    2. 扁平方式: 直接传递人设字段（与 persona_settings 字段一一对应）
    """
    # === 扁平化人设字段（与 persona_settings 字段一一对应） ===
    introduction: Optional[str] = Field(None, description="IP简介")
    tone: Optional[str] = Field(None, description="语气风格")
    target_audience: Optional[str] = Field(None, description="目标受众")
    content_style: Optional[str] = Field(None, description="内容风格")
    catchphrase: Optional[str] = Field(None, description="常用口头禅")
    keywords: Optional[List[str]] = Field(None, description="常用关键词")
    taboos: Optional[List[str]] = Field(None, description="内容禁忌")
    benchmark_accounts: Optional[List[str]] = Field(None, description="对标账号")


class ProjectUpdate(BaseModel):
    """
    更新项目请求模型
    
    支持两种传参方式：
    1. 嵌套方式: persona_settings: { tone: "xxx", introduction: "xxx" }
    2. 扁平方式: 直接传递人设字段（与 persona_settings 字段一一对应）
    """
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="项目名称")
    industry: Optional[str] = Field(None, description="赛道")
    persona_settings: Optional[PersonaSettings] = Field(None, description="人设配置（嵌套方式）")
    
    # === 扁平化人设字段（与 persona_settings 字段一一对应） ===
    introduction: Optional[str] = Field(None, description="IP简介")
    tone: Optional[str] = Field(None, description="语气风格")
    target_audience: Optional[str] = Field(None, description="目标受众")
    content_style: Optional[str] = Field(None, description="内容风格")
    catchphrase: Optional[str] = Field(None, description="常用口头禅")
    keywords: Optional[List[str]] = Field(None, description="常用关键词")
    taboos: Optional[List[str]] = Field(None, description="内容禁忌")
    benchmark_accounts: Optional[List[str]] = Field(None, description="对标账号")


class ProjectResponse(BaseModel):
    """项目响应模型（兼容小程序端格式）"""
    id: str = Field(..., description="项目ID（UUID字符串格式）")
    user_id: int = Field(..., description="用户ID")
    name: str = Field(..., description="项目名称")
    industry: str = Field(..., description="赛道")
    avatar_letter: str = Field(default="", description="项目首字母")
    avatar_color: str = Field(default="#3B82F6", description="头像背景色")
    persona_settings: PersonaSettings = Field(..., description="人设配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    is_active: bool = Field(default=False, description="是否为当前激活项目")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_active(cls, project: Project, is_active: bool = False) -> "ProjectResponse":
        """从 ORM 模型创建响应，支持设置 is_active"""
        persona_dict = project.get_persona_settings_dict()
        persona_settings = PersonaSettings(**persona_dict) if persona_dict else PersonaSettings()
        
        return cls(
            id=str(project.id),
            user_id=project.user_id,
            name=project.name,
            industry=project.industry,
            avatar_letter=project.avatar_letter or "",
            avatar_color=project.avatar_color or "#3B82F6",
            persona_settings=persona_settings,
            created_at=project.created_at,
            updated_at=project.updated_at or project.created_at,
            is_active=is_active,
        )


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    success: bool = True
    projects: List[ProjectResponse] = Field(default_factory=list, description="项目列表")
    active_project_id: Optional[str] = Field(None, description="当前激活的项目ID（UUID字符串）")


class ProjectSingleResponse(BaseModel):
    """单个项目响应模型"""
    success: bool = True
    project: ProjectResponse = Field(..., description="项目详情")


class ProjectSwitchRequest(BaseModel):
    """切换项目请求模型"""
    project_id: str = Field(..., description="要切换到的项目ID（UUID字符串）")


# ============== 预设选项 ==============

INDUSTRY_OPTIONS = [
    "通用",
    "医疗健康",
    "教育培训",
    "金融理财",
    "科技互联网",
    "电商零售",
    "餐饮美食",
    "旅游出行",
    "房产家居",
    "美妆护肤",
    "母婴育儿",
    "体育健身",
    "娱乐影视",
    "游戏动漫",
    "法律咨询",
    "职场成长",
    "情感心理",
    "三农乡村",
    "其他"
]

TONE_OPTIONS = [
    "专业亲和",
    "幽默风趣",
    "严肃正式",
    "温暖治愈",
    "犀利直接",
    "娓娓道来",
    "激情澎湃",
    "冷静理性"
]

