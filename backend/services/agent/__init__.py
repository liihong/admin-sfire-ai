"""
Agent领域服务模块
包含Agent核心执行、业务服务和管理服务
"""
from .core import AgentExecutor
from .business import AgentBusinessService
from .admin import AgentAdminService, AgentServiceV2

# 向后兼容：导入旧的AgentService（如果存在）
# 使用 importlib 直接导入模块文件，避免循环导入
try:
    import importlib.util
    import os
    # 获取 services/agent.py 文件的绝对路径
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    agent_module_path = os.path.join(parent_dir, "agent.py")
    
    if os.path.exists(agent_module_path):
        # 使用 importlib 直接加载模块文件
        spec = importlib.util.spec_from_file_location("services.agent_module", agent_module_path)
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)
        AgentService = agent_module.AgentService
    else:
        raise ImportError(f"Module file not found: {agent_module_path}")
except (ImportError, AttributeError):
    # 如果旧的AgentService不存在，使用AgentAdminService作为别名
    AgentService = AgentAdminService

__all__ = [
    "AgentExecutor",
    "AgentBusinessService",
    "AgentAdminService",
    "AgentServiceV2",  # 向后兼容别名
    "AgentService",  # 向后兼容别名
]

