"""
技能领域服务模块
包含技能服务和技能向量化服务
"""
from .service import SkillService
from .embedding import get_skill_embedding_service

__all__ = [
    "SkillService",
    "get_skill_embedding_service",
]








