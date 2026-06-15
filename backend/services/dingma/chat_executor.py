"""
顶妈（dingma）对话执行器

Fork 自 routers/client/creation.py generate_chat（2026-06-11），
仅增加产品知识库注入，不修改主程序 creation.py。
"""
from __future__ import annotations

import json
import uuid
from typing import List, Optional

import httpx
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.agent import Agent
from models.llm_model import LLMModel
from models.user import User
from routers.client.creation import (
    ChatRequest,
    ChatResponse,
    build_final_system_prompt,
    create_or_get_conversation,
    get_latest_user_message,
    increment_agent_usage_background_task,
    refund_frozen_coin,
    save_conversation_background_task,
    settle_coin_cost,
)
from services.coin import CoinServiceFactory
from services.content import AIService
from services.conversation.business import ConversationBusinessService
from services.dingma.constants import KnowledgeInjectMode
from services.dingma.knowledge import DingmaKnowledgeService
from services.resource import ProjectService
from services.shared.prompt_builder import PromptBuilder
from services.system.permission import PermissionService
from utils.exceptions import (
    BadRequestException,
    NotFoundException,
    RoutingMatchFailedException,
    ServerErrorException,
)


# dingma 专用：知识块最大长度保护（与其余 prompt 分开计算）
MAX_KNOWLEDGE_BLOCK_LENGTH = 4000
MAX_REST_SYSTEM_PROMPT_LENGTH = 12000


async def generate_dingma_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User,
    db: AsyncSession,
    scoped_public_tenant_id: Optional[int] = None,
):
    """
    dingma 专用对话接口：在 system prompt 顶部注入产品知识库（copywriting 模式）。
    """
    try:
        permission_service = PermissionService(db)
        permission = await permission_service.get_user_permission(current_user.id)
        if permission.get("is_vip_expired"):
            raise BadRequestException("会员已到期，请联系管理员。")

        conversation_service = ConversationBusinessService(db)

        agent_id = request.agent_id
        if agent_id is None and request.agent_type and request.agent_type.isdigit():
            agent_id = int(request.agent_type)

        if agent_id is None:
            raise BadRequestException("dingma 对话必须指定智能体 ID")

        agent_tenant_visible = [
            Agent.tenant_id == current_user.tenant_id,
            Agent.tenant_id.is_(None),
        ]
        if scoped_public_tenant_id is not None:
            agent_tenant_visible.append(Agent.tenant_id == scoped_public_tenant_id)

        result = await db.execute(
            select(Agent).where(
                and_(
                    Agent.id == agent_id,
                    or_(*agent_tenant_visible),
                    or_(Agent.is_system == 1, Agent.status == 1),
                )
            )
        )
        db_agent = result.scalar_one_or_none()
        if not db_agent:
            raise BadRequestException(f"智能体 ID {agent_id} 不存在或已下架")

        agent_config = {
            "system_prompt": db_agent.system_prompt,
            "temperature": db_agent.config.get("temperature", 0.7) if db_agent.config else 0.7,
            "max_tokens": db_agent.config.get("max_tokens", 2048) if db_agent.config else 2048,
        }
        agent_model_type = db_agent.model

        conversation_id = await create_or_get_conversation(
            conversation_service=conversation_service,
            request=request,
            current_user=current_user,
            db=db,
            agent_model_type=agent_model_type,
            agent_id=agent_id,
            db_agent=db_agent,
        )

        # IP 人设
        ip_persona_prompt = ""
        effective_project_id = request.project_id
        if effective_project_id is None and conversation_id:
            try:
                conv = await conversation_service.get_conversation(
                    conversation_id=conversation_id,
                    user_id=current_user.id,
                )
                effective_project_id = conv.project_id
            except Exception:
                pass

        if effective_project_id:
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(
                effective_project_id, user_id=current_user.id
            )
            if project and project.persona_settings:
                ip_persona_prompt = PromptBuilder.extract_persona_prompt(
                    project.persona_settings or {},
                    master_prompt="",
                    project_name=project.name or "",
                    project_industry=project.industry or "通用",
                )

        user_prompt = get_latest_user_message(request.messages)
        if not user_prompt:
            raise BadRequestException("消息列表不能为空")

        # 技能组装
        if getattr(db_agent, "agent_mode", 0) == 1:
            from services.routing import MasterRouter, PromptEngine

            master_router = MasterRouter()
            prompt_engine = PromptEngine()
            strict_routing = bool(getattr(db_agent, "is_routing_enabled", 0) == 1)
            try:
                routing_result = await master_router.route(
                    db=db,
                    agent=db_agent,
                    user_input=user_prompt,
                    strict_routing=strict_routing,
                )
            except RoutingMatchFailedException as e:
                routing_failed_msg = e.msg
                if request.stream:

                    async def _stream_routing_failed():
                        yield f"data: {json.dumps({'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'content': routing_failed_msg}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

                    return StreamingResponse(
                        _stream_routing_failed(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "X-Accel-Buffering": "no",
                        },
                    )
                return ChatResponse(
                    success=True,
                    content=routing_failed_msg,
                    agent_type=request.agent_type,
                    model_type=agent_model_type,
                )

            prompt_result = await prompt_engine.assemble_prompt(
                db=db,
                agent=db_agent,
                selected_skill_ids=routing_result.selected_skill_ids,
                skill_variables=(db_agent.skill_variables or {}),
                persona_prompt=ip_persona_prompt or None,
                user_input=user_prompt,
            )
            base_system_prompt = prompt_result.system_prompt
        else:
            base_system_prompt = agent_config["system_prompt"]

        # ===== dingma 专属：注入产品知识库（copywriting 模式）=====
        knowledge_block = await DingmaKnowledgeService.resolve_prompt_block(
            db=db,
            user_input=user_prompt,
            scoped_tenant_id=scoped_public_tenant_id,
            inject_mode=KnowledgeInjectMode.COPYWRITING,
        )
        if len(knowledge_block) > MAX_KNOWLEDGE_BLOCK_LENGTH:
            knowledge_block = knowledge_block[: MAX_KNOWLEDGE_BLOCK_LENGTH - 50] + "\n…（产品事实已截断）"

        base_system_prompt = DingmaKnowledgeService.prepend_knowledge(
            base_system_prompt, knowledge_block
        )

        # 构建最终 system prompt
        if db_agent and getattr(db_agent, "agent_mode", 0) == 1:
            final_system_prompt = base_system_prompt
        else:
            final_system_prompt = build_final_system_prompt(
                agent_system_prompt=base_system_prompt,
                ip_persona_prompt=ip_persona_prompt,
            )

        # 截断时保护知识块（只截断后半段 agent 能力部分）
        if len(final_system_prompt) > MAX_KNOWLEDGE_BLOCK_LENGTH + MAX_REST_SYSTEM_PROMPT_LENGTH:
            k_len = min(len(knowledge_block), MAX_KNOWLEDGE_BLOCK_LENGTH)
            knowledge_part = final_system_prompt[:k_len] if knowledge_block else ""
            rest = final_system_prompt[k_len:].lstrip("=" * 40).lstrip()
            if len(rest) > MAX_REST_SYSTEM_PROMPT_LENGTH:
                rest = rest[: MAX_REST_SYSTEM_PROMPT_LENGTH - 100]
            final_system_prompt = (
                f"{knowledge_part}\n\n{'=' * 40}\n\n{rest}" if knowledge_part else rest
            )
            logger.warning("[DingmaChat] system prompt 过长，已保护知识块并截断后半段")

        temperature = (
            request.temperature
            if request.temperature is not None
            else agent_config.get("temperature", 0.7)
        )
        max_tokens = request.max_tokens or agent_config.get("max_tokens", 2048)

        result = await db.execute(
            select(LLMModel)
            .where(
                and_(
                    or_(
                        LLMModel.provider == agent_model_type.lower(),
                        LLMModel.model_id == agent_model_type,
                        LLMModel.id == int(agent_model_type) if agent_model_type.isdigit() else False,
                    ),
                    LLMModel.is_enabled == True,
                )
            )
            .order_by(LLMModel.sort_order)
            .limit(1)
        )
        llm_model = result.scalar_one_or_none()
        if not llm_model:
            raise BadRequestException(f"未找到启用的模型 '{agent_model_type}'，请在管理后台配置模型")
        if not llm_model.api_key:
            raise BadRequestException(f"模型 {llm_model.name} 未配置 API Key")

        task_id = str(uuid.uuid4())
        request_id = f"dingma_chat_{current_user.id}_{task_id}"
        coin_service = CoinServiceFactory(db)
        freeze_info = None

        try:
            full_input_parts = [final_system_prompt or ""]
            for msg in request.messages or []:
                if msg.content:
                    full_input_parts.append(str(msg.content))
            estimated_cost = await coin_service.estimate_max_cost(
                model_id=llm_model.id,
                input_text="".join(full_input_parts),
                estimated_output_tokens=request.max_tokens or 2048,
            )
            freeze_result = await coin_service.freeze_amount_atomic(
                user_id=current_user.id,
                amount=estimated_cost,
                request_id=request_id,
                model_id=llm_model.id,
                conversation_id=conversation_id,
            )
            if not freeze_result["success"]:
                if freeze_result.get("insufficient_balance"):
                    raise BadRequestException("余额不足，请充值后再试。")
                raise BadRequestException("算力冻结失败，请稍后重试")
            freeze_info = {
                "task_id": task_id,
                "request_id": request_id,
                "frozen_amount": estimated_cost,
            }
        except BadRequestException:
            raise
        except Exception as e:
            logger.warning(f"[DingmaChat] 算力预冻结失败（降级）: {e}")
            task_id = None
            freeze_info = None

        messages_for_ai: List[dict] = []
        if final_system_prompt:
            messages_for_ai.append({"role": "system", "content": final_system_prompt})
        for msg in request.messages:
            messages_for_ai.append({"role": msg.role, "content": msg.content})

        ai_service = AIService(db)
        model_id_for_ai = llm_model.model_id
        assistant_content = ""

        if request.stream:

            async def generate_stream():
                nonlocal assistant_content
                usage_from_api = None
                try:
                    yield f"data: {json.dumps({'conversation_id': conversation_id}, ensure_ascii=False)}\n\n"
                    async for chunk_json in ai_service.stream_chat(
                        messages=messages_for_ai,
                        model=model_id_for_ai,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ):
                        try:
                            chunk_data = json.loads(chunk_json)
                            if "error" in chunk_data:
                                yield f"data: {chunk_json}\n\n"
                                if task_id and freeze_info and freeze_info.get("request_id"):
                                    await refund_frozen_coin(
                                        user_id=current_user.id,
                                        request_id=freeze_info["request_id"],
                                        reason="AI服务返回错误",
                                    )
                                return
                            if "usage" in chunk_data:
                                usage_from_api = chunk_data["usage"]
                            delta = chunk_data.get("delta", {})
                            content = delta.get("content", "")
                            reasoning_piece = delta.get("reasoning_content", "")
                            if content:
                                assistant_content += content
                            if content or reasoning_piece:
                                out = {}
                                if content:
                                    out["content"] = content
                                if reasoning_piece:
                                    out["reasoning_content"] = reasoning_piece
                                yield f"data: {json.dumps(out, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            assistant_content += chunk_json
                            yield f"data: {json.dumps({'content': chunk_json}, ensure_ascii=False)}\n\n"

                    yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

                    if task_id and freeze_info and freeze_info.get("request_id"):
                        await settle_coin_cost(
                            user_id=current_user.id,
                            request_id=freeze_info["request_id"],
                            user_prompt=user_prompt,
                            assistant_content=assistant_content,
                            system_prompt=final_system_prompt,
                            messages_for_ai=messages_for_ai,
                            llm_model=llm_model,
                            coin_service=coin_service,
                            db_agent=db_agent,
                            agent_type=request.agent_type,
                            is_stream=True,
                            usage_from_api=usage_from_api,
                        )

                    background_tasks.add_task(
                        save_conversation_background_task,
                        conversation_id=conversation_id,
                        user_message=user_prompt,
                        assistant_message=assistant_content,
                    )
                    if agent_id is not None:
                        background_tasks.add_task(
                            increment_agent_usage_background_task, agent_id
                        )

                except Exception as e:
                    if task_id and freeze_info and freeze_info.get("request_id"):
                        await refund_frozen_coin(
                            user_id=current_user.id,
                            request_id=freeze_info["request_id"],
                            reason="AI生成失败",
                        )
                    error_chunk = {
                        "error": {"message": f"生成错误: {str(e)}", "type": type(e).__name__}
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # 非流式
        result = await ai_service.chat(
            messages=messages_for_ai,
            model=model_id_for_ai,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        assistant_content = result.get("message", {}).get("content", "")

        if task_id and freeze_info and freeze_info.get("request_id"):
            await settle_coin_cost(
                user_id=current_user.id,
                request_id=freeze_info["request_id"],
                user_prompt=user_prompt,
                assistant_content=assistant_content,
                system_prompt=final_system_prompt,
                messages_for_ai=messages_for_ai,
                llm_model=llm_model,
                coin_service=coin_service,
                db_agent=db_agent,
                agent_type=request.agent_type,
                is_stream=False,
                usage_from_api=result.get("usage"),
            )

        background_tasks.add_task(
            save_conversation_background_task,
            conversation_id=conversation_id,
            user_message=user_prompt,
            assistant_message=assistant_content,
        )
        if agent_id is not None:
            background_tasks.add_task(increment_agent_usage_background_task, agent_id)

        return ChatResponse(
            success=True,
            content=assistant_content,
            agent_type=request.agent_type,
            model_type=agent_model_type,
        )

    except (BadRequestException, NotFoundException, ServerErrorException):
        raise
    except Exception as e:
        if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException)):
            raise ServerErrorException("AI服务暂时不可用，请稍后重试")
        logger.exception(f"[DingmaChat] 未预期错误: {e}")
        raise ServerErrorException("生成失败，请稍后重试")
