"""
Agent Constants - 智能体配置常量

定义不同智能体的 System Prompt 预设，用于对话式创作
兼容原有的 PROMPT_TEMPLATES 和 AVAILABLE_MODELS 常量
"""

from enum import Enum
from typing import Dict, Any, List


class AgentType(str, Enum):
    """智能体类型枚举"""
    IP_COLLECTOR = "ip_collector"           # IP信息采集


# 智能体配置字典
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    AgentType.IP_COLLECTOR: {
        "name": "IP信息采集",
        "icon": "🤖",
        "description": "专业的IP人设采集助手，通过引导式问答帮助用户完善IP信息",
        "system_prompt": """你是一个专业的IP人设采集助手。通过引导式问答帮助用户完善IP信息。

【采集步骤】
1. 项目名称和赛道：询问项目名称和所属行业
2. IP简介：引导用户描述IP定位、特色、核心价值
3. 语气风格和目标受众：询问语气风格偏好和目标用户特征
4. 口头禅和关键词：收集常用口头禅和关键词

【采集原则】
- 每次只问1-2个问题，不要一次性问太多
- 根据用户回答进行深入追问，挖掘更多细节
- 用友好的语气引导用户，让对话自然流畅
- 确保信息完整但不冗余，避免重复提问
- 如果用户回答不完整，可以适当追问补充

【输出要求】
- 用简洁友好的语言提问
- 根据用户回答给出适当的反馈和引导
- 逐步收集完整的IP信息
- 在收集到足够信息后，可以总结确认""",
        "temperature": 0.7,
        "max_tokens": 1024,
    },
}


def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """
    获取智能体配置
    
    Args:
        agent_type: 智能体类型
        
    Returns:
        智能体配置字典
        
    Raises:
        ValueError: 如果智能体类型不存在
    """
    if agent_type not in AGENT_CONFIGS:
        available = ", ".join(AGENT_CONFIGS.keys())
        raise ValueError(f"未知的智能体类型: '{agent_type}'。可用类型: {available}")
    
    return AGENT_CONFIGS[agent_type]


def get_all_agents() -> list:
    """
    获取所有智能体的简要信息列表
    
    Returns:
        智能体信息列表
    """
    return [
        {
            "type": agent_type,
            "name": config["name"],
            "icon": config["icon"],
            "description": config["description"],
        }
        for agent_type, config in AGENT_CONFIGS.items()
    ]


# ============== 兼容原有接口的常量 ==============

# 预设模板列表（兼容原有接口）
PROMPT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "type": agent_type,
        "name": config["name"],
        "icon": config["icon"],
        "description": config["description"],
        "systemPrompt": config["system_prompt"],
        "temperature": config.get("temperature", 0.7),
        "maxTokens": config.get("max_tokens", 2048),
    }
    for agent_type, config in AGENT_CONFIGS.items()
]

# 可用模型列表（占位符，实际从数据库读取）
AVAILABLE_MODELS: List[Dict[str, Any]] = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "maxTokens": 4096,
    },
    {
        "id": "claude",
        "name": "Claude",
        "maxTokens": 4096,
    },
    {
        "id": "doubao",
        "name": "豆包（火山引擎）",
        "maxTokens": 4096,
    },
]

# 默认模型ID（用于回退）
DEFAULT_MODEL_ID = "deepseek"
