"""
Master Prompt 生成服务

负责根据IP表单数据生成Master Prompt（200字描述）
使用配置的agent ID执行生成任务
"""
from typing import Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from core.config import settings
from models.agent import Agent
from services.agent.core import AgentExecutor
from utils.exceptions import NotFoundException, BadRequestException


class IPFormData(TypedDict, total=False):
    """IP表单数据类型定义"""
    name: str
    industry: str
    introduction: str
    tone: str
    target_audience: str
    target_pains: str
    keywords: list[str]
    industry_understanding: str
    unique_views: str
    catchphrase: str


class MasterPromptService:
    """Master Prompt生成服务类"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化Master Prompt服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.executor = AgentExecutor(db)
    
    async def generate_master_prompt(
        self,
        user_id: int,
        form_data: IPFormData
    ) -> str:
        """
        生成Master Prompt（200字描述）
        
        根据IP表单数据，使用agent ID=14生成一段200字的Master Prompt描述
        
        Args:
            user_id: 用户ID（用于日志记录）
            form_data: IP表单数据字典，包含以下字段：
                - name: 项目名称
                - industry: 行业
                - introduction: IP简介
                - tone: 语气风格
                - target_audience: 目标受众
                - target_pains: 目标人群痛点
                - keywords: 关键词列表
                - industry_understanding: 行业理解
                - unique_views: 独特观点
                - catchphrase: 口头禅
                - 等其他字段
        
        Returns:
            Master Prompt文本（200字左右），如果生成失败则返回空字符串
        """
        try:
            # 1. 获取配置的agent ID
            agent_id = settings.MASTER_PROMPT_AGENT_ID
            result = await self.db.execute(
                select(Agent).filter(Agent.id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                logger.warning(f"Master Prompt生成失败: Agent ID={agent_id} 不存在")
                return ""
            
            # 检查agent状态（系统自用或已上架）
            if agent.is_system != 1 and agent.status != 1:
                logger.warning(
                    f"Master Prompt生成失败: Agent ID={agent_id} "
                    f"既不是系统自用（is_system={agent.is_system}）也未上架（status={agent.status}）"
                )
                return ""
            
            # 2. 构建包含表单数据的Prompt
            prompt_text = self._build_prompt(form_data)
            
            # 3. 调用AgentExecutor执行agent（非流式，不注入IP基因）
            # 注意：这里不扣除算力，因为Master Prompt生成失败不应该阻止项目创建
            # 增加 max_tokens 以支持更长的 Master Prompt（不限制长度）
            response, _, _, _ = await self.executor.execute_non_stream(
                agent=agent,
                user_input=prompt_text,
                persona_prompt=None,  # 不注入IP基因
                temperature=0.7,
                max_tokens=2000  # 增加token限制以支持更长的Master Prompt
            )
            
            # 4. 清理和验证响应
            master_prompt = response.strip()
            
            # 验证最小长度（确保有内容）
            if len(master_prompt) < 50:
                logger.warning(f"Master Prompt生成结果过短: {len(master_prompt)}字符")
                return ""
            
            # 不再限制最大长度，允许完整保存以便后续智能体使用
            logger.info(f"Master Prompt生成成功: 用户ID={user_id}, 长度={len(master_prompt)}字符")
            return master_prompt
            
        except Exception as e:
            logger.error(f"Master Prompt生成失败: {e}", exc_info=True)
            # 失败时返回空字符串，允许项目创建继续
            return ""
    
    def _build_prompt(self, form_data: IPFormData) -> str:
        """
        构建生成Master Prompt的Prompt文本
        
        Args:
            form_data: IP表单数据字典
        
        Returns:
            Prompt文本
        """
        # 提取关键字段并清理输入（防止Prompt注入）
        def sanitize_input(text: str, max_length: int = 500) -> str:
            """清理用户输入，防止Prompt注入"""
            if not text:
                return ""
            # 移除可能的指令字符和控制字符
            text = text.replace("```", "").replace("```json", "").replace("```python", "")
            text = text.replace("\n\n\n", "\n\n")  # 限制连续换行
            # 限制长度
            return text[:max_length] if len(text) > max_length else text
        
        name = sanitize_input(form_data.get("name", ""), 100)
        industry = sanitize_input(form_data.get("industry", ""), 50)
        introduction = sanitize_input(form_data.get("introduction", ""), 1000)
        tone = sanitize_input(form_data.get("tone", ""), 50)
        target_audience = sanitize_input(form_data.get("target_audience", ""), 500)
        target_pains = sanitize_input(form_data.get("target_pains", ""), 500)
        keywords = form_data.get("keywords", []) or []
        industry_understanding = sanitize_input(form_data.get("industry_understanding", ""), 500)
        unique_views = sanitize_input(form_data.get("unique_views", ""), 500)
        catchphrase = sanitize_input(form_data.get("catchphrase", ""), 100)
        
        # 构建关键词字符串（限制关键词数量）
        keywords_limited = keywords[:10] if len(keywords) > 10 else keywords
        keywords_str = "、".join([sanitize_input(k, 20) for k in keywords_limited]) if keywords_limited else "无"
        
        # 构建Prompt
        prompt = f"""请根据以下IP信息，生成一段约200字的Master Prompt描述。

IP信息：
- 名称：{name}
- 行业：{industry}
- IP简介：{introduction}
- 语气风格：{tone}
- 目标受众：{target_audience}
- 目标人群痛点：{target_pains}
- 关键词：{keywords_str}
- 行业理解：{industry_understanding}
- 独特观点：{unique_views}
- 口头禅：{catchphrase}

要求：
1. 用一段连贯的文字描述这个IP的核心特征和定位
2. 字数控制在200字左右（180-220字）
3. 语言简洁有力，突出IP的独特性和价值
4. 直接输出描述文本，不要添加任何前缀、后缀或格式标记
5. 不要使用"这个IP"、"该IP"等指代词，直接描述特征

Master Prompt："""
        
        return prompt

