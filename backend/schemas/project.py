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
    avatar_letter: Optional[str] = Field(None, description="项目首字母")
    avatar_color: Optional[str] = Field(None, description="头像背景色")
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
    master_prompt: Optional[str] = Field(default=None, description="Master Prompt（IP核心特征描述）")
    status: int = Field(default=1, description="状态：1-正常, 2-已冻结")
    is_frozen: bool = Field(default=False, description="是否已冻结")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    is_active: bool = Field(default=False, description="是否为当前激活项目")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_active(cls, project: Project, is_active: bool = False) -> "ProjectResponse":
        """从 ORM 模型创建响应，支持设置 is_active"""
        persona_dict = project.get_persona_settings_dict()
        # 从 persona_settings 中移除 master_prompt（如果存在），因为现在是独立字段
        if "master_prompt" in persona_dict:
            persona_dict = {k: v for k, v in persona_dict.items() if k != "master_prompt"}
        persona_settings = PersonaSettings(**persona_dict) if persona_dict else PersonaSettings()
        
        from models.project import ProjectStatus
        
        # 安全获取 updated_at，避免触发延迟加载
        updated_at = project.updated_at if hasattr(project, '__dict__') and 'updated_at' in project.__dict__ else project.created_at
        
        return cls(
            id=str(project.id),
            user_id=project.user_id,
            name=project.name,
            industry=project.industry,
            avatar_letter=project.avatar_letter or "",
            avatar_color=project.avatar_color or "#3B82F6",
            persona_settings=persona_settings,
            master_prompt=project.master_prompt,
            status=project.status,
            is_frozen=project.status == ProjectStatus.FROZEN.value,
            created_at=project.created_at,
            updated_at=updated_at or project.created_at,
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


# ============== AI 智能填写相关 Schemas ==============

class IPCollectRequest(BaseModel):
    """IP信息采集对话请求"""
    messages: List[dict] = Field(..., description="对话消息列表，格式: [{'role': 'user', 'content': '...'}, ...]")
    step: Optional[int] = Field(None, description="当前步骤（可选）")
    context: Optional[dict] = Field(None, description="上下文信息（已收集的信息）")


class IPCollectResponse(BaseModel):
    """IP信息采集对话响应"""
    reply: str = Field(..., description="AI回复内容")
    next_step: Optional[int] = Field(None, description="下一步骤（可选）")
    collected_info: Optional[dict] = Field(None, description="已收集的信息摘要（可选）")
    is_complete: bool = Field(default=False, description="是否收集完成")


class IPCompressRequest(BaseModel):
    """IP信息压缩请求"""
    raw_info: dict = Field(..., description="原始IP信息（可能很长）")
    # 包含字段：name, industry, introduction, tone, target_audience, catchphrase, keywords 等


class IPCompressResponse(BaseModel):
    """IP信息压缩响应"""
    compressed_info: dict = Field(..., description="压缩后的IP信息")
    # 包含字段：
    # - introduction: 200字以内
    # - target_audience: 50字以内
    # - keywords: 最多8个
    # - catchphrase: 保持简短
    # - 其他字段保持不变


class IPReportRequest(BaseModel):
    """IP定位报告生成请求"""
    name: str = Field(..., description="项目名称")
    industry: str = Field(..., description="行业")
    introduction: Optional[str] = Field(None, description="IP简介")
    tone: Optional[str] = Field(None, description="语气风格")
    target_audience: Optional[str] = Field(None, description="目标受众")
    target_pains: Optional[str] = Field(None, description="目标人群痛点")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    industry_understanding: Optional[str] = Field(None, description="行业理解")
    unique_views: Optional[str] = Field(None, description="独特观点")
    catchphrase: Optional[str] = Field(None, description="口头禅")


class IPReportContent(BaseModel):
    """IP定位报告内容"""
    name: str = Field(..., description="IP名称")
    persona_tags: List[str] = Field(..., description="人格标签")
    core_archetype: str = Field(..., description="核心原型")
    one_line_intro: str = Field(..., description="一句话简介")


class IPReportContentMoat(BaseModel):
    """内容护城河"""
    insight: str = Field(..., description="反共识洞察")
    emotional_hook: str = Field(..., description="情感钩子")


class IPReportLanguageFingerprint(BaseModel):
    """语言指纹分析"""
    tone_modeling: str = Field(..., description="语感建模")
    atmosphere: str = Field(..., description="标志性氛围")


class IPReportBusinessPotential(BaseModel):
    """商业潜力与避坑指南"""
    viral_potential: str = Field(..., description="爆款潜质")
    red_lines: str = Field(..., description="人设红线")


class IPReportData(BaseModel):
    """IP定位报告数据"""
    name: str = Field(..., description="IP名称")
    persona_tags: List[str] = Field(..., description="人格标签")
    core_archetype: str = Field(..., description="核心原型")
    one_line_intro: str = Field(..., description="一句话简介")
    content_moat: IPReportContentMoat = Field(..., description="内容护城河")
    language_fingerprint: IPReportLanguageFingerprint = Field(..., description="语言指纹分析")
    business_potential: IPReportBusinessPotential = Field(..., description="商业潜力与避坑指南")
    expert_message: str = Field(..., description="专家寄语")


class IPReportResponse(BaseModel):
    """IP定位报告响应"""
    report: IPReportData = Field(..., description="IP定位报告")
    score: int = Field(..., ge=0, le=100, description="IP数字化程度评分（0-100）")
    score_reason: str = Field(..., description="评分理由")

