"""
数据序列化工具
将 SQLAlchemy 模型转换为 API 响应格式
"""
from datetime import datetime
from typing import Any, Optional
from app.models.agent import Agent
from app.schemas.agent import AgentConfig


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



