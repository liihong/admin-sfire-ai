"""
Prompt Engine：Prompt组装引擎
纯函数式设计，负责组装最终的Prompt
"""
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.agent import Agent
from services.prompt_builder import PromptBuilder
from .types import PromptAssemblyResult


class PromptEngine:
    """Prompt组装引擎：负责三明治式Prompt组装"""
    
    @staticmethod
    async def assemble_prompt(
        db: AsyncSession,
        agent: Agent,
        selected_skill_ids: List[int],
        skill_variables: Dict[int, Dict[str, str]],
        persona_prompt: Optional[str] = None,
        user_input: str = ""
    ) -> PromptAssemblyResult:
        """
        组装Prompt：按照IP人设 → Agent能力 → 用户输入的顺序组装
        
        Args:
            db: 异步数据库会话
            agent: Agent对象
            selected_skill_ids: 选中的技能ID列表
            skill_variables: 技能变量配置
            persona_prompt: IP人设Prompt（可选）
            user_input: 用户输入
        
        Returns:
            PromptAssemblyResult: 组装结果
        """
        # 1. 组装Agent能力Prompt
        agent_prompt = ""
        skills_applied = []
        token_count = 0
        skills_detail = []
        
        if agent.agent_mode == 1 and selected_skill_ids:
            # 技能组装模式：使用选中的技能组装Prompt
            try:
                agent_prompt, token_count, skills_used = await PromptBuilder.build_prompt(
                    db=db,
                    skill_ids=selected_skill_ids,
                    skill_variables=skill_variables
                )
                skills_applied = selected_skill_ids
                skills_detail = skills_used
                logger.debug(f"Agent Prompt组装完成: {token_count} tokens, {len(skills_applied)}个技能")
            except Exception as e:
                logger.error(f"Agent Prompt组装失败: {e}")
                # 降级：使用system_prompt
                agent_prompt = agent.system_prompt
                skills_applied = []
        else:
            # 普通模式：直接使用system_prompt
            agent_prompt = agent.system_prompt
            skills_applied = []
        
        # 2. 组装system_prompt（不包含用户输入）
        # 用户输入应该作为user消息，而不是system消息的一部分
        prompt_parts = []
        
        # IP人设（如果提供）
        if persona_prompt:
            prompt_parts.append(persona_prompt)
        
        # Agent能力
        if agent_prompt:
            prompt_parts.append(agent_prompt)
        
        # 组合成最终的system_prompt（不包含用户输入）
        system_prompt = "\n\n".join(prompt_parts) if prompt_parts else ""
        
        # user_message就是用户输入
        user_message = user_input
        
        return PromptAssemblyResult(
            system_prompt=system_prompt,
            user_message=user_message,
            skills_applied=skills_applied,
            token_count=token_count,
            skills_detail=skills_detail
        )

