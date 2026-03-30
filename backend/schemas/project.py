"""
Project Schema - 项目（IP）Pydantic 模型
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from models.project import Project

DEFAULT_STYLE_TONES = "专业亲和"


def _coerce_to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value if v) if value else ""
    return str(value) if value else ""


def _coerce_keywords(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if x is not None and str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [k.strip() for k in value.split(",") if k.strip()]
    return []


def normalize_persona_settings_dict(
    raw: Optional[dict],
    *,
    project_name: str = "",
    project_industry: str = "通用",
) -> dict:
    """
    将 persona_settings 规范为 PersonaSettings 结构；仅识别新键（与小程序 / API 一致）。
    """
    raw = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}

    keys_str = [
        "ip_name", "ip_age", "ip_city", "ip_industry", "ip_identityTag", "ip_experience",
        "cl_mainProducts", "cl_targetPopulation", "cl_painPoints", "cl_advantages", "cl_feedback",
        "style_tones", "style_mantra",
    ]
    for k in keys_str:
        v = raw.get(k)
        out[k] = _coerce_to_str(v) if v is not None else ""

    out["keywords"] = _coerce_keywords(raw.get("keywords"))

    if not out["style_tones"]:
        out["style_tones"] = DEFAULT_STYLE_TONES
    if not out["ip_name"]:
        out["ip_name"] = project_name or ""
    if not out["ip_industry"]:
        out["ip_industry"] = project_industry or "通用"

    return out


class PersonaSettings(BaseModel):
    """IP 人设配置（persona_settings JSON，与小程序一致）"""
    ip_name: str = Field(default="", description="名称")
    ip_age: str = Field(default="", description="年龄")
    ip_city: str = Field(default="", description="城市")
    ip_industry: str = Field(default="", description="行业")
    ip_identityTag: str = Field(default="", description="身份标签")
    ip_experience: str = Field(default="", description="经历介绍")
    cl_mainProducts: str = Field(default="", description="主要产品")
    cl_targetPopulation: str = Field(default="", description="目标人群")
    cl_painPoints: str = Field(default="", description="人群痛点")
    cl_advantages: str = Field(default="", description="产品优势")
    cl_feedback: str = Field(default="", description="客户反馈")
    style_tones: str = Field(default=DEFAULT_STYLE_TONES, description="语气风格")
    style_mantra: str = Field(default="", description="个人口头禅")
    keywords: List[str] = Field(default_factory=list, description="关键词")

    @field_validator("cl_targetPopulation", mode="before")
    @classmethod
    def coerce_cl_target(cls, v):
        return _coerce_to_str(v)

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="项目名称")
    industry: str = Field(default="通用", description="赛道")
    avatar_letter: Optional[str] = Field(default=None, description="项目首字母")
    avatar_color: Optional[str] = Field(default=None, description="头像背景色")
    persona_settings: Optional[PersonaSettings] = Field(default=None, description="人设配置（嵌套）")


def _persona_flat_field_names() -> tuple[str, ...]:
    return tuple(PersonaSettings.model_fields.keys())


class ProjectCreate(ProjectBase):
    """创建项目：支持嵌套 persona_settings 或与 PersonaSettings 同名的扁平字段"""
    model_config = ConfigDict(extra="ignore")

    ip_name: Optional[str] = None
    ip_age: Optional[str] = None
    ip_city: Optional[str] = None
    ip_industry: Optional[str] = None
    ip_identityTag: Optional[str] = None
    ip_experience: Optional[str] = None
    cl_mainProducts: Optional[str] = None
    cl_targetPopulation: Optional[str] = None
    cl_painPoints: Optional[str] = None
    cl_advantages: Optional[str] = None
    cl_feedback: Optional[str] = None
    style_tones: Optional[str] = None
    style_mantra: Optional[str] = None
    keywords: Optional[List[str]] = None

    @field_validator("cl_targetPopulation", mode="before")
    @classmethod
    def coerce_cl_target(cls, v):
        return _coerce_to_str(v) if v is not None else None


class ProjectUpdate(BaseModel):
    """更新项目"""
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    industry: Optional[str] = None
    avatar_letter: Optional[str] = None
    avatar_color: Optional[str] = None
    persona_settings: Optional[PersonaSettings] = None

    ip_name: Optional[str] = None
    ip_age: Optional[str] = None
    ip_city: Optional[str] = None
    ip_industry: Optional[str] = None
    ip_identityTag: Optional[str] = None
    ip_experience: Optional[str] = None
    cl_mainProducts: Optional[str] = None
    cl_targetPopulation: Optional[str] = None
    cl_painPoints: Optional[str] = None
    cl_advantages: Optional[str] = None
    cl_feedback: Optional[str] = None
    style_tones: Optional[str] = None
    style_mantra: Optional[str] = None
    keywords: Optional[List[str]] = None

    @field_validator("cl_targetPopulation", mode="before")
    @classmethod
    def coerce_cl_target(cls, v):
        return _coerce_to_str(v) if v is not None else None


class ProjectResponse(BaseModel):
    id: str = Field(...)
    user_id: int = Field(...)
    name: str = Field(...)
    industry: str = Field(...)
    avatar_letter: str = Field(default="")
    avatar_color: str = Field(default="#3B82F6")
    persona_settings: PersonaSettings = Field(...)
    master_prompt: Optional[str] = Field(default=None)
    status: int = Field(default=1)
    is_frozen: bool = Field(default=False)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    is_active: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_active(cls, project: Project, is_active: bool = False) -> "ProjectResponse":
        persona_dict = project.get_persona_settings_dict()
        if "master_prompt" in persona_dict:
            persona_dict = {k: v for k, v in persona_dict.items() if k != "master_prompt"}
        normalized = normalize_persona_settings_dict(
            persona_dict,
            project_name=project.name or "",
            project_industry=project.industry or "通用",
        )
        persona_settings = PersonaSettings.model_validate(normalized)

        from models.project import ProjectStatus

        updated_at = project.updated_at if hasattr(project, "__dict__") and "updated_at" in project.__dict__ else project.created_at

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
    success: bool = True
    projects: List[ProjectResponse] = Field(default_factory=list)
    active_project_id: Optional[str] = None


class ProjectSingleResponse(BaseModel):
    success: bool = True
    project: ProjectResponse = Field(...)


class ProjectSwitchRequest(BaseModel):
    project_id: str = Field(...)


INDUSTRY_OPTIONS = [
    "通用", "医疗健康", "教育培训", "金融理财", "科技互联网", "电商零售", "餐饮美食",
    "旅游出行", "房产家居", "美妆护肤", "母婴育儿", "体育健身", "娱乐影视", "游戏动漫",
    "法律咨询", "职场成长", "情感心理", "三农乡村", "其他",
]

TONE_OPTIONS = [
    "专业亲和", "幽默风趣", "严肃正式", "温暖治愈", "犀利直接", "娓娓道来", "激情澎湃", "冷静理性",
]


class IPCollectRequest(BaseModel):
    messages: List[dict] = Field(...)
    step: Optional[int] = None
    context: Optional[dict] = None


class IPCollectResponse(BaseModel):
    reply: str = Field(...)
    next_step: Optional[int] = None
    collected_info: Optional[dict] = None
    is_complete: bool = False


class IPCompressRequest(BaseModel):
    raw_info: dict = Field(...)


class IPCompressResponse(BaseModel):
    compressed_info: dict = Field(...)


class IPReportRequest(BaseModel):
    name: str = Field(...)
    industry: str = Field(...)
    ip_experience: Optional[str] = Field(None, description="经历介绍")
    style_tones: Optional[str] = None
    cl_targetPopulation: Optional[str] = None
    cl_painPoints: Optional[str] = None
    keywords: Optional[List[str]] = None
    cl_advantages: Optional[str] = None
    cl_feedback: Optional[str] = None
    style_mantra: Optional[str] = None


class IPReportContent(BaseModel):
    name: str = Field(...)
    persona_tags: List[str] = Field(...)
    core_archetype: str = Field(...)
    one_line_intro: str = Field(...)


class IPReportContentMoat(BaseModel):
    insight: str = Field(...)
    emotional_hook: str = Field(...)


class IPReportLanguageFingerprint(BaseModel):
    tone_modeling: str = Field(...)
    atmosphere: str = Field(...)


class IPReportBusinessPotential(BaseModel):
    viral_potential: str = Field(...)
    red_lines: str = Field(...)


class IPReportData(BaseModel):
    name: str = Field(...)
    persona_tags: List[str] = Field(...)
    core_archetype: str = Field(...)
    one_line_intro: str = Field(...)
    content_moat: IPReportContentMoat = Field(...)
    language_fingerprint: IPReportLanguageFingerprint = Field(...)
    business_potential: IPReportBusinessPotential = Field(...)
    expert_message: str = Field(...)


class IPReportResponse(BaseModel):
    report: IPReportData = Field(...)
    score: int = Field(..., ge=0, le=100)
    score_reason: str = Field(...)
