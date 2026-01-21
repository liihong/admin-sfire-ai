"""
路由模块数据类型定义
使用Pydantic BaseModel定义所有数据结构
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RoutingRequest(BaseModel):
    """路由请求数据"""
    user_input: str = Field(..., description="用户输入")
    agent_skill_ids: List[int] = Field(..., description="Agent配置的所有技能ID")
    routing_description: str = Field(default="", description="路由特征描述")
    use_vector: bool = Field(default=True, description="是否使用向量检索")
    top_k: int = Field(default=3, ge=1, le=10, description="选择Top-K个技能")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")


class RoutingResult(BaseModel):
    """路由结果数据"""
    selected_skill_ids: List[int] = Field(..., description="选中的技能ID列表")
    static_skill_ids: List[int] = Field(default_factory=list, description="静态技能ID列表（非rule类型）")
    dynamic_skill_ids: List[int] = Field(default_factory=list, description="动态技能ID列表（rule类型）")
    routing_method: str = Field(default="static", description="使用的路由方法：static/vector/keywords/llm")
    debug_info: Optional[Dict] = Field(default=None, description="调试信息（可选）")


class PromptAssemblyRequest(BaseModel):
    """Prompt组装请求数据"""
    agent_id: int = Field(..., description="Agent ID")
    selected_skill_ids: List[int] = Field(..., description="选中的技能ID列表")
    skill_variables: Dict[int, Dict[str, str]] = Field(default_factory=dict, description="技能变量配置")
    persona_prompt: Optional[str] = Field(default=None, description="IP人设Prompt（可选）")
    user_input: str = Field(default="", description="用户输入")


class PromptAssemblyResult(BaseModel):
    """Prompt组装结果数据"""
    system_prompt: str = Field(..., description="系统提示词（IP人设 + Agent能力）")
    user_message: str = Field(..., description="用户消息")
    skills_applied: List[int] = Field(..., description="实际使用的技能ID列表")
    token_count: int = Field(default=0, description="Token数量统计")
    skills_detail: List[Dict] = Field(default_factory=list, description="技能详情列表")

