"""
顶妈（dingma）灵感口播生成服务

Fork 自 services/inspiration/generate_service.py，增加产品知识库注入。
主程序 InspirationGenerateService 不改动。
"""
from __future__ import annotations

import uuid
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from constants.agent import AgentType, DEFAULT_MODEL_ID, get_agent_config
from constants.coin_config import CoinConfig
from models.agent import Agent
from models.inspiration import Inspiration
from schemas.inspiration import InspirationGenerateRequest
from services.coin import CoinServiceFactory
from services.dingma.constants import KnowledgeInjectMode
from services.dingma.knowledge import DingmaKnowledgeService
from services.inspiration.inspiration_service import InspirationService
from services.resource import LLMModelService, ProjectService
from services.shared.llm_service import LLMFactory
from services.shared.prompt_builder import PromptBuilder
from services.system.security import SecurityService
from utils.exceptions import BadRequestException, NotFoundException, ServerErrorException

# 与 chat_executor 一致：保护知识块长度
MAX_KNOWLEDGE_BLOCK_LENGTH = 4000

# dingma 灵感默认智能体名称（agent_type 未传时按租户内名称匹配）
DEFAULT_INSPIRATION_AGENT_NAME = "灵感碎片大师"


class DingmaInspirationGenerateService:
    """顶妈灵感生成：注入 copywriting 产品事实 + 智能体技能组装"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.inspiration_service = InspirationService(db)
        self.coin_service = CoinServiceFactory(db)
        self.project_service = ProjectService(db)
        self.llm_model_service = LLMModelService(db)

    async def generate_script(
        self,
        user_id: int,
        request: InspirationGenerateRequest,
        scoped_public_tenant_id: Optional[int] = None,
    ) -> dict:
        """生成口播文案（dingma 专用，注入产品知识库）"""
        inspiration = await self.inspiration_service.get_inspiration_by_id(
            request.inspiration_id,
            user_id,
        )

        security_result = await SecurityService.msg_sec_check(content=inspiration.content)
        if not security_result["pass"]:
            raise BadRequestException("灵感内容包含违规信息，无法生成")

        prompt = self._build_generate_prompt(inspiration)

        project = None
        if inspiration.project_id:
            project = await self.project_service.get_project_by_id(
                inspiration.project_id,
                user_id,
            )

        db_agent, agent_model_type = await self._resolve_agent(
            request.agent_type,
            scoped_public_tenant_id,
        )
        agent_config_fallback = None
        if db_agent is None:
            agent_config_fallback = self._get_legacy_agent_config(request.agent_type)

        system_prompt = await self._build_system_prompt(
            db_agent=db_agent,
            agent_config_fallback=agent_config_fallback,
            project=project,
            user_input=inspiration.content,
            scoped_public_tenant_id=scoped_public_tenant_id,
        )

        model_id = await self._get_model_id(agent_model_type, request.model_type)
        llm_model = await self.llm_model_service.get_model_by_id(model_id)
        if not llm_model:
            raise NotFoundException(f"模型ID {model_id} 不存在")

        task_id = str(uuid.uuid4())
        request_id = f"dingma_inspiration_generate_{request.inspiration_id}_{task_id}"
        estimated_output_tokens = request.max_tokens or 2048

        await self.coin_service.check_and_freeze(
            user_id=user_id,
            model_id=model_id,
            input_text=prompt + (system_prompt or ""),
            task_id=request_id,
            estimated_output_tokens=estimated_output_tokens,
        )

        agent_type_label = str(db_agent.id) if db_agent else (request.agent_type or AgentType.IP_COLLECTOR.value)

        try:
            llm_client = LLMFactory.create_client(
                model_type=llm_model.model_type,
                api_key=llm_model.api_key,
            )
            generated_content = await llm_client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 2048,
            )

            output_security_result = await SecurityService.msg_sec_check(content=generated_content)
            if not output_security_result["pass"]:
                await self.coin_service.refund_amount_atomic(
                    user_id=user_id,
                    request_id=request_id,
                    reason="生成内容违规",
                )
                raise BadRequestException("生成的内容包含违规信息，已退款")

            input_tokens = CoinConfig.estimate_tokens_from_text(prompt + (system_prompt or ""))
            output_tokens = CoinConfig.estimate_tokens_from_text(generated_content)
            actual_cost = await self.coin_service.calculator.calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_id=model_id,
            )
            await self.coin_service.settle_and_deduct(
                user_id=user_id,
                request_id=request_id,
                model_id=model_id,
                model_name=llm_model.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                actual_cost=actual_cost,
                task_id=task_id,
            )

            await self.inspiration_service.update_generated_content(
                inspiration_id=request.inspiration_id,
                user_id=user_id,
                generated_content=generated_content,
                generated_at=None,
            )

            logger.info(
                f"[DingmaInspiration] 生成成功 inspiration_id={request.inspiration_id}, cost={actual_cost}"
            )
            return {
                "success": True,
                "content": generated_content,
                "inspiration_id": request.inspiration_id,
                "agent_type": agent_type_label,
                "model_type": llm_model.model_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": float(actual_cost),
            }
        except BadRequestException:
            raise
        except Exception as e:
            logger.error(f"[DingmaInspiration] 生成失败: {e}")
            try:
                await self.coin_service.refund_amount_atomic(
                    user_id=user_id,
                    request_id=request_id,
                    reason=f"生成失败: {str(e)}",
                )
            except Exception as refund_error:
                logger.error(f"[DingmaInspiration] 退款失败: {refund_error}")
            raise ServerErrorException(f"生成失败: {str(e)}")

    async def _resolve_agent(
        self,
        agent_type: Optional[str],
        scoped_public_tenant_id: Optional[int],
    ) -> Tuple[Optional[Agent], str]:
        """解析 dingma 租户下的智能体"""
        # ip_collector 为历史默认值，顶妈侧视为未指定，走名称匹配
        normalized_type = (agent_type or "").strip()
        if normalized_type in ("", "ip_collector"):
            normalized_type = ""

        agent_id: Optional[int] = None
        if normalized_type.isdigit():
            agent_id = int(normalized_type)

        tenant_filters = []
        if scoped_public_tenant_id is not None:
            tenant_filters.append(Agent.tenant_id == scoped_public_tenant_id)
            tenant_filters.append(Agent.tenant_id.is_(None))

        if agent_id is not None:
            result = await self.db.execute(
                select(Agent).where(
                    and_(
                        Agent.id == agent_id,
                        or_(*tenant_filters) if tenant_filters else True,
                        or_(Agent.is_system == 1, Agent.status == 1),
                    )
                )
            )
            db_agent = result.scalar_one_or_none()
            if db_agent:
                return db_agent, db_agent.model
            raise BadRequestException(f"智能体 ID {agent_id} 不存在或已下架")

        # 未传 ID：按默认名称在 dingma 租户内查找「灵感碎片大师」
        if scoped_public_tenant_id is not None:
            result = await self.db.execute(
                select(Agent).where(
                    and_(
                        Agent.name == DEFAULT_INSPIRATION_AGENT_NAME,
                        or_(Agent.tenant_id == scoped_public_tenant_id, Agent.tenant_id.is_(None)),
                        or_(Agent.is_system == 1, Agent.status == 1),
                    )
                ).limit(1)
            )
            db_agent = result.scalar_one_or_none()
            if db_agent:
                return db_agent, db_agent.model

        return None, AgentType.IP_COLLECTOR.value

    def _get_legacy_agent_config(self, agent_type: Optional[str]) -> dict:
        """无 DB 智能体时的兜底配置"""
        if not agent_type:
            agent_type = AgentType.IP_COLLECTOR.value
        agent_config = get_agent_config(agent_type)
        if not agent_config:
            raise BadRequestException(f"无效的智能体类型: {agent_type}")
        return agent_config

    async def _build_system_prompt(
        self,
        db_agent: Optional[Agent],
        agent_config_fallback: Optional[dict],
        project,
        user_input: str,
        scoped_public_tenant_id: Optional[int],
    ) -> str:
        """组装 system prompt：技能/普通模式 + IP 人设 + 产品知识库"""
        if db_agent and getattr(db_agent, "agent_mode", 0) == 1:
            from services.routing import MasterRouter, PromptEngine

            ip_persona_prompt = ""
            if project and project.persona_settings:
                ip_persona_prompt = PromptBuilder.extract_persona_prompt(
                    project.persona_settings or {},
                    master_prompt="",
                    project_name=project.name or "",
                    project_industry=project.industry or "通用",
                )

            master_router = MasterRouter()
            prompt_engine = PromptEngine()
            strict_routing = bool(getattr(db_agent, "is_routing_enabled", 0) == 1)
            routing_result = await master_router.route(
                db=self.db,
                agent=db_agent,
                user_input=user_input,
                strict_routing=strict_routing,
            )
            prompt_result = await prompt_engine.assemble_prompt(
                db=self.db,
                agent=db_agent,
                selected_skill_ids=routing_result.selected_skill_ids,
                skill_variables=(db_agent.skill_variables or {}),
                persona_prompt=ip_persona_prompt or None,
                user_input=user_input,
            )
            base_system_prompt = prompt_result.system_prompt
        else:
            fallback = agent_config_fallback or {}
            base_system_prompt = (
                db_agent.system_prompt
                if db_agent
                else fallback.get("system_prompt", "")
            )
            if project:
                ip_persona_prompt = PromptBuilder.get_ip_persona_prompt_from_project(project)
                if ip_persona_prompt:
                    base_system_prompt += "\n\n" + "=" * 40
                    base_system_prompt += "\n在创作时，请严格遵循以下IP人设设定：\n"
                    base_system_prompt += ip_persona_prompt
                    base_system_prompt += "\n" + "=" * 40

        knowledge_block = await DingmaKnowledgeService.resolve_prompt_block(
            db=self.db,
            user_input=user_input,
            scoped_tenant_id=scoped_public_tenant_id,
            inject_mode=KnowledgeInjectMode.COPYWRITING,
        )
        if len(knowledge_block) > MAX_KNOWLEDGE_BLOCK_LENGTH:
            knowledge_block = knowledge_block[: MAX_KNOWLEDGE_BLOCK_LENGTH - 50] + "\n…（产品事实已截断）"

        return DingmaKnowledgeService.prepend_knowledge(base_system_prompt, knowledge_block)

    async def _get_model_id(self, agent_model_type: str, request_model_type: Optional[str]) -> int:
        model_type = request_model_type or agent_model_type
        llm_model = await self.llm_model_service.get_model_by_type(model_type)
        if llm_model:
            return llm_model.id
        return DEFAULT_MODEL_ID

    def _build_generate_prompt(self, inspiration: Inspiration) -> str:
        """构建用户侧生成提示词"""
        prompt_parts = [
            "请基于以下灵感，生成一段适合拍摄的口播文案：",
            "",
            "【灵感内容】",
            inspiration.content,
            "",
            "要求：",
            "1. 文案要自然流畅，适合口播",
            "2. 语言要生动有趣，能吸引观众",
            "3. 结构清晰，有开头、主体、结尾",
            "4. 长度适中，适合1-3分钟的视频",
            "5. 若灵感涉及具体产品，只能使用【产品事实】中的配料与卖点，禁止编造",
        ]
        tags = inspiration.get_tags_list()
        if tags:
            prompt_parts.append(f"\n【标签】{', '.join(tags)}")
        return "\n".join(prompt_parts)
