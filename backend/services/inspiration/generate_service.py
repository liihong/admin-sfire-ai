"""
Inspiration Generate Service - 灵感生成服务

实现一键生成口播文案功能，集成算力消耗、内容安全检测等
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.inspiration import Inspiration
from schemas.inspiration import InspirationGenerateRequest
from services.inspiration.inspiration_service import InspirationService
from services.system.security import SecurityService
from services.coin import CoinServiceFactory
from services.resource import ProjectService
from services.resource import LLMModelService
from services.agent import AgentService
from services.conversation.business import ConversationBusinessService
from services.shared.llm_service import LLMFactory
from constants.agent import get_agent_config, AgentType, DEFAULT_MODEL_ID
from utils.exceptions import BadRequestException, NotFoundException, ServerErrorException


class InspirationGenerateService:
    """灵感生成服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inspiration_service = InspirationService(db)
        self.coin_service = CoinServiceFactory(db)
        self.project_service = ProjectService(db)
        self.llm_model_service = LLMModelService(db)
        self.agent_service = AgentService(db)
    
    async def generate_script(
        self,
        user_id: int,
        request: InspirationGenerateRequest
    ) -> dict:
        """
        生成口播文案
        
        Args:
            user_id: 用户ID
            request: 生成请求
        
        Returns:
            生成结果字典，包含生成的内容、使用的模型等信息
        """
        # 1. 获取灵感
        inspiration = await self.inspiration_service.get_inspiration_by_id(
            request.inspiration_id,
            user_id
        )
        
        # 2. 内容安全检测（输入）
        security_result = await SecurityService.msg_sec_check(content=inspiration.content)
        if not security_result['pass']:
            raise BadRequestException("灵感内容包含违规信息，无法生成")
        
        # 3. 构建生成提示词
        prompt = self._build_generate_prompt(inspiration)
        
        # 4. 获取项目信息（如果有）
        project = None
        if inspiration.project_id:
            project = await self.project_service.get_project_by_id(
                inspiration.project_id,
                user_id
            )
        
        # 5. 获取智能体配置
        agent_config, agent_model_type = await self._get_agent_config(request.agent_type)
        
        # 6. 获取模型配置
        model_id = await self._get_model_id(agent_model_type, request.model_type)
        llm_model = await self.llm_model_service.get_model_by_id(model_id)
        if not llm_model:
            raise NotFoundException(f"模型ID {model_id} 不存在")
        
        # 7. 构建系统提示词（包含IP人设）
        system_prompt = self._build_system_prompt(agent_config, project)
        
        # 8. 预冻结算力
        task_id = str(uuid.uuid4())
        request_id = f"inspiration_generate_{request.inspiration_id}_{task_id}"
        
        estimated_output_tokens = request.max_tokens or 2048
        freeze_result = await self.coin_service.check_and_freeze(
            user_id=user_id,
            model_id=model_id,
            input_text=prompt,
            task_id=request_id,
            estimated_output_tokens=estimated_output_tokens
        )
        
        # 9. 调用LLM生成
        try:
            llm_client = LLMFactory.create_client(
                model_type=llm_model.model_type,
                api_key=llm_model.api_key
            )
            
            # 非流式生成（一次性返回完整内容）
            generated_content = await llm_client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 2048
            )
            
            # 10. 内容安全检测（输出）
            output_security_result = await SecurityService.msg_sec_check(content=generated_content)
            if not output_security_result['pass']:
                # 生成内容违规，需要退款
                await self.coin_service.refund_amount_atomic(
                    user_id=user_id,
                    request_id=request_id,
                    reason="生成内容违规"
                )
                raise BadRequestException("生成的内容包含违规信息，已退款")
            
            # 11. 计算实际消耗并结算
            from constants.coin_config import CoinConfig
            input_tokens = CoinConfig.estimate_tokens_from_text(prompt)
            output_tokens = CoinConfig.estimate_tokens_from_text(generated_content)
            
            actual_cost = await self.coin_service.calculator.calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id
            )
            
            # 结算算力
            await self.coin_service.settle_and_deduct(
                user_id=user_id,
                request_id=request_id,
                model_id=model_id,
                model_name=llm_model.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                actual_cost=actual_cost,
                task_id=task_id
            )
            
            # 12. 更新灵感表中的生成内容
            await self.inspiration_service.update_generated_content(
                inspiration_id=request.inspiration_id,
                user_id=user_id,
                generated_content=generated_content,
                generated_at=None  # 使用默认当前时间
            )
            
            logger.info(
                f"灵感生成成功: inspiration_id={request.inspiration_id}, "
                f"user_id={user_id}, cost={actual_cost}"
            )
            
            return {
                "success": True,
                "content": generated_content,
                "inspiration_id": request.inspiration_id,
                "agent_type": request.agent_type,
                "model_type": llm_model.model_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": float(actual_cost),
            }
            
        except Exception as e:
            # 生成失败，退款
            logger.error(f"灵感生成失败: {str(e)}")
            try:
                await self.coin_service.refund_amount_atomic(
                    user_id=user_id,
                    request_id=request_id,
                    reason=f"生成失败: {str(e)}"
                )
            except Exception as refund_error:
                logger.error(f"退款失败: {str(refund_error)}")
            
            raise ServerErrorException(f"生成失败: {str(e)}")
    
    def _build_generate_prompt(self, inspiration: Inspiration) -> str:
        """
        构建生成提示词
        
        Args:
            inspiration: 灵感对象
        
        Returns:
            提示词字符串
        """
        prompt_parts = [
            "请基于以下灵感，生成一段适合拍摄的口播文案：",
            "",
            f"【灵感内容】",
            inspiration.content,
            "",
            "要求：",
            "1. 文案要自然流畅，适合口播",
            "2. 语言要生动有趣，能吸引观众",
            "3. 结构清晰，有开头、主体、结尾",
            "4. 长度适中，适合1-3分钟的视频",
        ]
        
        # 如果有标签，添加到提示词中
        tags = inspiration.get_tags_list()
        if tags:
            prompt_parts.append(f"\n【标签】{', '.join(tags)}")
        
        return "\n".join(prompt_parts)
    
    async def _get_agent_config(self, agent_type: Optional[str]) -> tuple:
        """
        获取智能体配置
        
        Args:
            agent_type: 智能体类型
        
        Returns:
            (agent_config字典, model_type字符串)
        """
        if not agent_type:
            agent_type = AgentType.IP_COLLECTOR.value
        
        # 尝试从数据库获取智能体
        if agent_type and agent_type.isdigit():
            agent_id = int(agent_type)
            from sqlalchemy import select
            from models.agent import Agent
            
            result = await self.db.execute(
                select(Agent).where(Agent.id == agent_id)
            )
            db_agent = result.scalar_one_or_none()
            
            if db_agent:
                agent_config = {
                    "system_prompt": db_agent.system_prompt,
                    "temperature": db_agent.config.get("temperature", 0.7) if db_agent.config else 0.7,
                    "max_tokens": db_agent.config.get("max_tokens", 2048) if db_agent.config else 2048,
                }
                return agent_config, db_agent.model
        
        # 使用预设智能体配置
        agent_config = get_agent_config(agent_type)
        if not agent_config:
            raise BadRequestException(f"无效的智能体类型: {agent_type}")
        
        return agent_config, agent_config.get("model_type", "deepseek")
    
    async def _get_model_id(self, agent_model_type: str, request_model_type: Optional[str]) -> int:
        """
        获取模型ID
        
        Args:
            agent_model_type: 智能体配置的模型类型
            request_model_type: 请求中的模型类型（可选）
        
        Returns:
            模型ID
        """
        model_type = request_model_type or agent_model_type
        
        # 从数据库查询模型
        llm_model = await self.llm_model_service.get_model_by_type(model_type)
        if llm_model:
            return llm_model.id
        
        # 如果找不到，使用默认模型
        return DEFAULT_MODEL_ID
    
    def _build_system_prompt(self, agent_config: dict, project) -> str:
        """
        构建系统提示词（包含IP人设）
        
        Args:
            agent_config: 智能体配置
            project: 项目对象（可选）
        
        Returns:
            系统提示词字符串
        """
        system_prompt = agent_config.get("system_prompt", "")
        
        # 如果有项目，添加IP人设信息
        if project:
            ip_persona_prompt = self._build_ip_persona_prompt(project)
            if ip_persona_prompt:
                system_prompt += "\n\n" + "=" * 40
                system_prompt += "\n在创作时，请严格遵循以下IP人设设定：\n"
                system_prompt += ip_persona_prompt
                system_prompt += "\n" + "=" * 40
        
        return system_prompt
    
    def _build_ip_persona_prompt(self, project) -> str:
        """
        从项目信息构建IP人设提示词
        
        Args:
            project: 项目对象
        
        Returns:
            IP人设提示词字符串
        """
        if not project:
            return ""
        
        persona = project.get_persona_settings_dict()
        parts = []
        
        parts.append(f"【IP信息】")
        parts.append(f"- IP名称：{project.name}")
        parts.append(f"- 所属赛道：{project.industry}")
        
        if persona.get("introduction"):
            parts.append(f"- IP简介：{persona['introduction']}")
        
        if persona.get("tone"):
            parts.append(f"- 语气风格：{persona['tone']}")
        
        if persona.get("target_audience"):
            parts.append(f"- 目标受众：{persona['target_audience']}")
        
        if persona.get("content_style"):
            parts.append(f"- 内容风格：{persona['content_style']}")
        
        if persona.get("catchphrase"):
            parts.append(f"- 常用口头禅：{persona['catchphrase']}")
        
        if persona.get("keywords"):
            parts.append(f"- 常用关键词：{', '.join(persona['keywords'])}")
        
        if persona.get("taboos"):
            parts.append(f"- 内容禁忌：{', '.join(persona['taboos'])}")
        
        if persona.get("benchmark_accounts"):
            parts.append(f"- 对标账号：{', '.join(persona['benchmark_accounts'])}")
        
        return "\n".join(parts)

