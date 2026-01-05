"""
数据序列化工具
将 SQLAlchemy 模型转换为 API 响应格式
"""
from datetime import datetime
from typing import Any, Optional
from models.agent import Agent
from schemas.agent import AgentConfig
from models.llm_model import LLMModel


def agent_to_response(agent: Agent) -> dict:
    """将 Agent 模型转换为响应格式"""
    config_data = agent.config or {}
    config = AgentConfig(**config_data)
    
    return {
        "id": str(agent.id),
        "name": agent.name,
        "icon": agent.icon,
        "description": agent.description or "",
        "systemPrompt": agent.system_prompt,
        "model": agent.model,
        "config": config.model_dump(),
        "sortOrder": agent.sort_order,
        "status": agent.status,
        "usageCount": agent.usage_count,
        "createTime": agent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updateTime": agent.updated_at.strftime("%Y-%m-%d %H:%M:%S") if agent.updated_at else "",
    }


def llm_model_to_response(model: LLMModel) -> dict:
    """将 LLMModel 模型转换为响应格式"""
    return {
        "id": model.id,
        "name": model.name,
        "model_id": model.model_id,
        "provider": model.provider,
        "has_api_key": model.has_api_key,
        "base_url": model.base_url,
        "is_enabled": model.is_enabled,
        "total_tokens_used": model.total_tokens_used,
        "balance": float(model.balance) if model.balance is not None else None,
        "balance_updated_at": model.balance_updated_at.isoformat() if model.balance_updated_at else None,
        "sort_order": model.sort_order,
        "remark": model.remark,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


