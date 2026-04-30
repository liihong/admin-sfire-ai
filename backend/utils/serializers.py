"""
数据序列化工具
将 SQLAlchemy 模型转换为 API 响应格式
"""
from datetime import datetime
from typing import Any, Optional
from models.agent import Agent
from schemas.agent import AgentConfig
from models.llm_model import LLMModel


def agent_to_client_detail_response(agent: Agent, model_name: Optional[str] = None) -> dict:
    """将 Agent 模型转换为 C 端详情响应格式（不包含提示词 systemPrompt）
    
    Args:
        agent: Agent 模型实例
        model_name: 可选，模型显示名称
    """
    config_data = agent.config or {}
    config = AgentConfig(**config_data)
    
    return {
        "id": agent.id,
        "name": agent.name,
        "icon": agent.icon,
        "description": agent.description or "",
        "welcomeMessage": agent.welcome_message or "",
        "model": agent.model,
        "modelName": model_name if model_name is not None else agent.model,
        "config": config.model_dump(),
        "sortOrder": agent.sort_order,
        "agentMode": agent.agent_mode,
        "status": agent.status,
        "usageCount": agent.usage_count,
        "createTime": agent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updateTime": agent.updated_at.strftime("%Y-%m-%d %H:%M:%S") if agent.updated_at else "",
        "skillIds": agent.skill_ids,
        "skillVariables": agent.skill_variables,
        "routingDescription": agent.routing_description or "",
        "isRoutingEnabled": agent.is_routing_enabled,
        "isSystem": agent.is_system,
    }


def agent_to_response(
    agent: Agent,
    model_name: Optional[str] = None,
    *,
    viewer_scoped_tenant_id: Optional[int] = None,
) -> dict:
    """将 Agent 模型转换为响应格式
    
    Args:
        agent: Agent 模型实例
        model_name: 可选，模型显示名称（用于列表展示，不传则前端可继续用 model ID）
        viewer_scoped_tenant_id: 当前管理员的数据范围租户 ID；
            非空且智能体 tenant_id 为空时表示「全租户公用」，对租户管理员只读展示。
    """
    config_data = agent.config or {}
    config = AgentConfig(**config_data)

    read_only = viewer_scoped_tenant_id is not None and getattr(agent, "tenant_id", None) is None
    
    result = {
        "id": str(agent.id),
        "name": agent.name,
        "icon": agent.icon,
        "description": agent.description or "",
        "welcomeMessage": agent.welcome_message or "",
        "systemPrompt": agent.system_prompt,
        "model": agent.model,
        "modelName": model_name if model_name is not None else agent.model,
        "config": config.model_dump(),
        "sortOrder": agent.sort_order,
        # 智能体模式：0-普通模式, 1-Skill 组装模式
        "agentMode": agent.agent_mode,
        "status": agent.status,
        "usageCount": agent.usage_count,
        "createTime": agent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updateTime": agent.updated_at.strftime("%Y-%m-%d %H:%M:%S") if agent.updated_at else "",
        # 技能组装模式字段（向后兼容）
        "skillIds": agent.skill_ids,
        "skillVariables": agent.skill_variables,
        # 系统自用标识
        "isSystem": agent.is_system,
        "tenantId": agent.tenant_id,
        "readOnly": read_only,
    }
    return result


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


