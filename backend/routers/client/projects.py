"""
Client Project Endpoints
C端项目管理接口（小程序 & PC官网）
支持项目的创建、查询、更新、删除、切换等功能
"""
import json
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user, get_current_miniprogram_user_optional
from core.config import settings
from services.resource import ProjectService
from services.system import DictionaryService
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSwitchRequest,
    ProjectResponse,
    INDUSTRY_OPTIONS,
    TONE_OPTIONS,
    IPCollectRequest,
    IPCollectResponse,
    IPReportRequest,
    IPReportResponse,
    IPReportData,
)
from utils.response import success
from utils.exceptions import NotFoundException, BadRequestException
from services.agent.core import AgentExecutor
from services.routing import PromptEngine
from services.content import AIService
from models.agent import Agent
from sqlalchemy import select
from loguru import logger

router = APIRouter()


def _build_frontend_project(project_dict: dict) -> dict:
    """
    将项目数据转换为前端期望的格式
    
    同时保留嵌套的 persona_settings 对象和扁平化字段，确保前端可以正确加载数据
    """
    persona_settings = project_dict.get("persona_settings", {})
    if not isinstance(persona_settings, dict):
        persona_settings = {}
    
    # 处理 ID：如果是 UUID，保持字符串；如果是数字，转换为数字
    project_id = project_dict.get("id", "")
    try:
        project_id_num = int(project_id) if str(project_id).isdigit() else project_id
    except (ValueError, TypeError):
        project_id_num = project_id
    
    return {
        "id": project_id_num,
        "name": project_dict.get("name", ""),
        "industry": project_dict.get("industry", ""),
        # 头像相关字段
        "avatar_letter": project_dict.get("avatar_letter", ""),
        "avatar_color": project_dict.get("avatar_color", "#3B82F6"),
        # 嵌套格式：完整的人设配置对象（前端需要此字段来加载表单数据）
        "persona_settings": persona_settings,
        # 扁平化字段（向后兼容，与 persona_settings 一一对应）
        "introduction": persona_settings.get("introduction", ""),
        "tone": persona_settings.get("tone", ""),
        "target_audience": persona_settings.get("target_audience", ""),
        "content_style": persona_settings.get("content_style", ""),
        "catchphrase": persona_settings.get("catchphrase", ""),
        "keywords": persona_settings.get("keywords", []),
        "taboos": persona_settings.get("taboos", []),
        "benchmark_accounts": persona_settings.get("benchmark_accounts", []),
        # 扩展字段
        "industry_understanding": persona_settings.get("industry_understanding", ""),
        "unique_views": persona_settings.get("unique_views", ""),
        "target_pains": persona_settings.get("target_pains", ""),
        # 其他字段
        "isActive": project_dict.get("is_active", False),
        "createdAt": project_dict.get("created_at", "").isoformat() if project_dict.get("created_at") else "",
        "updatedAt": project_dict.get("updated_at", "").isoformat() if project_dict.get("updated_at") else ""
    }


@router.get("")
async def list_projects(
    current_user: Optional[User] = Depends(get_current_miniprogram_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的所有项目列表，按最后修改时间倒序排列（支持游客模式）"""
    project_service = ProjectService(db)

    # 游客模式：返回空列表
    if current_user is None:
        return success(
            data={
                "success": True,
                "projects": [],
                "active_project_id": None,
                "is_guest": True
            },
            msg="获取成功（游客模式）"
        )

    # 已登录用户：获取项目列表
    projects = await project_service.get_projects_by_user(current_user.id)
    active_project_id = await project_service.get_active_project(current_user.id)

    # 转换为响应格式（扁平化人设字段）
    project_list = []
    for project in projects:
        is_active = (active_project_id is not None and project.id == active_project_id)
        project_response = ProjectResponse.from_orm_with_active(project, is_active=is_active)
        project_dict = project_response.model_dump()
        frontend_project = _build_frontend_project(project_dict)
        project_list.append(frontend_project)

    return success(
        data={
            "success": True,
            "projects": project_list,
            "active_project_id": str(active_project_id) if active_project_id else None,
            "is_guest": False
        },
        msg="获取成功"
    )


@router.post("")
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    project_service = ProjectService(db)
    
    project = await project_service.create_project(current_user.id, data)
    project_response = ProjectResponse.from_orm_with_active(project, is_active=False)
    project_dict = project_response.model_dump()
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="创建成功")


@router.get("/active")
async def get_active_project_info(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前激活的项目详情"""
    project_service = ProjectService(db)
    
    active_id = await project_service.get_active_project(current_user.id)
    if not active_id:
        raise NotFoundException("没有激活的项目")
    
    project = await project_service.get_project_by_id(active_id, user_id=current_user.id)
    if not project:
        raise NotFoundException("激活的项目不存在")
    
    project_response = ProjectResponse.from_orm_with_active(project, is_active=True)
    project_dict = project_response.model_dump()
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="获取成功")


@router.post("/switch")
async def switch_project(
    data: ProjectSwitchRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """切换当前激活的项目"""
    project_service = ProjectService(db)
    
    try:
        project_id = int(data.project_id)
    except (ValueError, TypeError):
        raise NotFoundException("无效的项目ID格式")
    
    # 验证项目是否存在且属于当前用户
    project = await project_service.get_project_by_id(project_id, user_id=current_user.id)
    if not project:
        raise NotFoundException("项目不存在或无权访问")
    
    # 检查项目状态，冻结的项目不能切换
    from models.project import ProjectStatus
    if project.status == ProjectStatus.FROZEN.value:
        raise BadRequestException("该项目已冻结，无法切换。请续费会员以解锁。")
    
    await project_service.set_active_project(current_user.id, project_id)
    
    return success(
        data={
            "success": True,
            "message": f"已切换到项目: {project.name}",
            "project": ProjectResponse.from_orm_with_active(project, is_active=True).model_dump()
        },
        msg="切换成功"
    )


@router.get("/options")
async def get_project_options(
    db: AsyncSession = Depends(get_db)
):
    """
    获取项目配置选项（行业赛道和语气风格）
    
    优先从数据库读取，如果数据库中没有数据则使用默认值
    """
    dict_service = DictionaryService(db)
    
    # 从数据库获取行业赛道选项
    industries = await dict_service.get_items_by_code("industry", enabled_only=True)
    # 从数据库获取语气风格选项
    tones = await dict_service.get_items_by_code("tone", enabled_only=True)
    
    # 如果数据库中没有数据，使用默认值
    if not industries:
        industries = [{"label": item, "value": item} for item in INDUSTRY_OPTIONS]
    else:
        industries = [item.model_dump() for item in industries]
    
    if not tones:
        tones = [{"label": item, "value": item} for item in TONE_OPTIONS]
    else:
        tones = [item.model_dump() for item in tones]
    
    return success(
        data={
            "success": True,
            "industries": industries,
            "tones": tones
        },
        msg="获取成功"
    )


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定项目详情"""
    project_service = ProjectService(db)
    
    project = await project_service.get_project_by_id(project_id, user_id=current_user.id)
    if not project:
        raise NotFoundException("项目不存在或无权访问")
    
    active_id = await project_service.get_active_project(current_user.id)
    is_active = (active_id == project_id)
    
    project_response = ProjectResponse.from_orm_with_active(project, is_active=is_active)
    project_dict = project_response.model_dump()
    # 转换为前端期望的扁平化格式，确保 id 为 number 类型
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="获取成功")


@router.put("/{project_id}")
async def update_project_info(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """更新项目信息"""
    project_service = ProjectService(db)
    
    project = await project_service.update_project(project_id, current_user.id, data)
    
    # 获取当前激活的项目ID，确保返回正确的 is_active 状态
    active_id = await project_service.get_active_project(current_user.id)
    is_active = (active_id == project_id)
    
    project_response = ProjectResponse.from_orm_with_active(project, is_active=is_active)
    project_dict = project_response.model_dump()
    frontend_project = _build_frontend_project(project_dict)
    
    return success(data=frontend_project, msg="更新成功")


@router.delete("/{project_id}")
async def delete_project_by_id(
    project_id: int,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """删除项目"""
    project_service = ProjectService(db)
    
    await project_service.delete_project(project_id, current_user.id)
    
    return success(data={"success": True, "message": "项目已删除"}, msg="删除成功")


@router.post("/ai-collect", summary="AI智能填写 - IP信息采集对话")
async def ai_collect_ip_info(
    request: IPCollectRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    IP信息采集对话接口
    
    通过智能体对话的形式收集IP信息，使用数据库中配置的IP_COLLECTOR智能体进行引导式问答
    不注入IP基因，直接使用agent的system_prompt进行对话
    """
    try:
        # 1. 从数据库获取IP采集智能体配置
        from core.config import settings
        
        agent = None
        
        # 优先使用配置的agent ID
        if settings.IP_COLLECTOR_AGENT_ID:
            from sqlalchemy import or_
            agent_id = int(settings.IP_COLLECTOR_AGENT_ID)  # 确保是整数类型
            logger.info(f"尝试查找IP采集Agent: ID={agent_id}, 配置值={settings.IP_COLLECTOR_AGENT_ID}")
            
            # 先查询是否存在该Agent（不限制状态）
            result = await db.execute(
                select(Agent).filter(Agent.id == agent_id)
            )
            agent_check = result.scalar_one_or_none()
            
            if agent_check:
                logger.info(
                    f"找到Agent ID={agent_id}: name={agent_check.name}, "
                    f"is_system={agent_check.is_system}, status={agent_check.status}"
                )
                # 系统自用智能体可以绕过上架检查，普通智能体必须上架
                if agent_check.is_system == 1 or agent_check.status == 1:
                    agent = agent_check
                    logger.info(f"使用配置的IP_COLLECTOR_AGENT_ID={agent_id}")
                else:
                    logger.warning(
                        f"Agent ID={agent_id} 既不是系统自用（is_system=0）也未上架（status=0），"
                        f"无法使用"
                    )
            else:
                logger.warning(f"未找到Agent ID={agent_id}，将尝试通过名称查找")
        
        # 如果配置的ID不存在或不可用，通过名称查找
        if not agent:
            from sqlalchemy import or_
            logger.info("尝试通过名称'IP信息采集'查找Agent")
            result = await db.execute(
                select(Agent).filter(
                    Agent.name == "IP信息采集",
                    # 系统自用智能体可以绕过上架检查，普通智能体必须上架
                    or_(Agent.is_system == 1, Agent.status == 1)
                ).order_by(Agent.created_at.desc())
            )
            agent = result.scalar_one_or_none()
            if agent:
                logger.info(f"通过名称找到IP信息采集Agent: ID={agent.id}, is_system={agent.is_system}, status={agent.status}")
        
        # 如果还是找不到，抛出错误
        if not agent:
            error_msg = (
                f"未找到IP信息采集智能体配置。"
                f"配置的IP_COLLECTOR_AGENT_ID={settings.IP_COLLECTOR_AGENT_ID}，"
                f"请检查数据库中是否存在ID={settings.IP_COLLECTOR_AGENT_ID}的智能体，"
                f"且该智能体为系统自用（is_system=1）或已上架（status=1），"
                f"或者创建名称为'IP信息采集'的智能体"
            )
            logger.error(error_msg)
            raise NotFoundException(msg=error_msg)
        
        # 2. 构建历史对话消息列表
        conversation_messages = []
        
        # 处理历史对话消息
        for msg in request.messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    conversation_messages.append({"role": role, "content": content})
        
        # 如果没有用户消息，添加一个初始提示
        if not any(msg.get("role") == "user" for msg in conversation_messages):
            conversation_messages.append({
                "role": "user",
                "content": "你好，我想创建一个新的IP项目，请帮我收集相关信息。"
            })
        
        # 获取最后一条用户消息（用于路由决策）
        user_input = ""
        for msg in reversed(conversation_messages):
            if msg.get("role") == "user":
                user_input = msg.get("content", "")
                break
        
        # 3. 使用AgentExecutor的路由和Prompt组装功能（不注入IP基因）
        executor = AgentExecutor(db)
        prompt_engine = PromptEngine()
        
        # 路由决策
        routing_result = await executor.master_router.route(
            db=db,
            agent=agent,
            user_input=user_input
        )
        
        # Prompt组装（不注入IP基因）
        prompt_result = await prompt_engine.assemble_prompt(
            db=db,
            agent=agent,
            selected_skill_ids=routing_result.selected_skill_ids,
            skill_variables=agent.skill_variables or {},
            persona_prompt=None,  # 不注入IP基因
            user_input=user_input
        )
        
        # 获取agent配置参数
        agent_config = agent.config or {}
        temperature = agent_config.get("temperature", 0.7)
        max_tokens = agent_config.get("maxTokens", agent_config.get("max_tokens", 2048))
        
        # 4. 构建完整的消息列表（包含系统提示词和历史对话）
        messages = [
            {"role": "system", "content": prompt_result.system_prompt}
        ]
        
        # 添加历史对话消息（排除system角色，因为已经添加了）
        for msg in conversation_messages:
            if msg.get("role") != "system":
                messages.append(msg)
        
        # 5. 使用AIService执行对话（支持历史消息）
        ai_service = AIService(db)
        
        # 解析模型ID（agent.model可能是数据库ID或模型标识）
        model_id = agent.model
        
        # 调用AI服务
        response = await ai_service.chat(
            messages=messages,
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 提取AI回复
        ai_reply = ""
        if isinstance(response, dict):
            if response.get("message"):
                ai_reply = response["message"].get("content", "")
            elif response.get("choices") and len(response["choices"]) > 0:
                ai_reply = response["choices"][0].get("message", {}).get("content", "")
            elif response.get("content"):
                ai_reply = response["content"]
        
        if not ai_reply:
            ai_reply = "抱歉，我暂时无法回复，请稍后再试。"
        
        # 获取token统计（如果有）
        token_count = 0
        if isinstance(response, dict) and response.get("usage"):
            usage = response["usage"]
            token_count = usage.get("total_tokens", 0)
        
        # 4. 判断是否收集完成（简单判断：如果AI提到"完成"、"总结"等关键词）
        is_complete = any(keyword in ai_reply for keyword in ["完成", "总结", "确认", "以上", "这些信息"])
        
        # 5. 构建响应
        response_data = IPCollectResponse(
            reply=ai_reply,
            next_step=request.step + 1 if request.step is not None else None,
            collected_info=request.context,
            is_complete=is_complete
        )
        
        logger.debug(f"IP信息采集对话完成: token_count={token_count}, is_complete={is_complete}")
        
        return success(data=response_data.model_dump(), msg="对话成功")
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"AI采集对话失败: {e}", exc_info=True)
        raise BadRequestException(f"AI对话失败: {str(e)}")


@router.post("/generate-ip-report", summary="生成IP定位报告")
async def generate_ip_report(
    request: IPReportRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    IP定位报告生成接口
    
    使用agent ID=13生成IP定位报告，包含：
    - 数字化人格画像
    - 内容护城河
    - 语言指纹分析
    - 商业潜力与避坑指南
    - 专家寄语
    - IP数字化程度评分（0-100）
    """
    try:
        # 1. 获取配置的agent ID
        agent_id = settings.IP_REPORT_AGENT_ID
        result = await db.execute(
            select(Agent).filter(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise NotFoundException(f"Agent ID={agent_id} 不存在")
        
        # 检查agent状态（系统自用或已上架）
        if agent.is_system != 1 and agent.status != 1:
            raise BadRequestException(
                f"Agent ID={agent_id} 既不是系统自用（is_system={agent.is_system}）也未上架（status={agent.status}）"
            )
        
        # 2. 清理用户输入，防止Prompt注入
        def sanitize_prompt_input(text: Optional[str], max_length: int = 500) -> str:
            """清理用户输入，防止Prompt注入"""
            if not text:
                return "未填写"
            # 移除可能的指令字符
            text = text.replace("```", "").replace("```json", "").replace("```python", "")
            text = text.replace("\n\n\n", "\n\n")  # 限制连续换行
            # 限制长度
            return text[:max_length] if len(text) > max_length else text
        
        # 清理关键词
        keywords_clean = []
        if request.keywords:
            for kw in request.keywords[:10]:  # 限制关键词数量
                cleaned = sanitize_prompt_input(kw, 20)
                if cleaned and cleaned != "未填写":
                    keywords_clean.append(cleaned)
        keywords_str = "、".join(keywords_clean) if keywords_clean else "无"
        
        # 3. 准备IP信息变量（用于替换提示词模板中的占位符）
        ip_variables = {
            "ip_name": sanitize_prompt_input(request.name, 100),
            "ip_industry": sanitize_prompt_input(request.industry, 50),
            "ip_introduction": sanitize_prompt_input(request.introduction, 1000),
            "ip_tone": sanitize_prompt_input(request.tone, 50),
            "ip_target_audience": sanitize_prompt_input(request.target_audience, 500),
            "ip_target_pains": sanitize_prompt_input(request.target_pains, 500),
            "ip_keywords": keywords_str,
            "ip_industry_understanding": sanitize_prompt_input(request.industry_understanding, 500),
            "ip_unique_views": sanitize_prompt_input(request.unique_views, 500),
            "ip_catchphrase": sanitize_prompt_input(request.catchphrase, 100),
        }
        
        # 4. 使用数据库中的提示词模板（agent.system_prompt）
        # 如果提示词中包含占位符（如 {ip_name}），则替换后作为user_input传入
        # 如果提示词中不包含占位符，则将IP信息格式化后作为user_input传入
        prompt_template = agent.system_prompt
        if not prompt_template:
            raise BadRequestException("Agent配置的提示词为空，无法生成报告")
        
        # 检查提示词中是否包含占位符
        has_placeholders = any(f"{{{key}}}" in prompt_template for key in ip_variables.keys())
        
        if has_placeholders:
            # 如果包含占位符，替换后作为user_input传入
            try:
                user_input = prompt_template.format(**ip_variables)
            except KeyError as e:
                logger.warning(f"提示词模板中包含未定义的占位符: {e}")
                # 如果替换失败，降级处理：将IP信息格式化后作为user_input传入
                ip_info_text = f"""请根据以下IP信息，生成一份IP数字化人格定位报告。

IP信息：
- 名称：{ip_variables['ip_name']}
- 行业：{ip_variables['ip_industry']}
- IP简介：{ip_variables['ip_introduction']}
- 语气风格：{ip_variables['ip_tone']}
- 目标受众：{ip_variables['ip_target_audience']}
- 目标人群痛点：{ip_variables['ip_target_pains']}
- 关键词：{ip_variables['ip_keywords']}
- 行业理解：{ip_variables['ip_industry_understanding']}
- 独特观点：{ip_variables['ip_unique_views']}
- 口头禅：{ip_variables['ip_catchphrase']}"""
                user_input = ip_info_text
        else:
            # 如果提示词中不包含占位符，将IP信息格式化后作为user_input传入
            # agent.system_prompt 会作为系统提示词自动使用
            ip_info_text = f"""请根据以下IP信息，生成一份IP数字化人格定位报告。

IP信息：
- 名称：{ip_variables['ip_name']}
- 行业：{ip_variables['ip_industry']}
- IP简介：{ip_variables['ip_introduction']}
- 语气风格：{ip_variables['ip_tone']}
- 目标受众：{ip_variables['ip_target_audience']}
- 目标人群痛点：{ip_variables['ip_target_pains']}
- 关键词：{ip_variables['ip_keywords']}
- 行业理解：{ip_variables['ip_industry_understanding']}
- 独特观点：{ip_variables['ip_unique_views']}
- 口头禅：{ip_variables['ip_catchphrase']}"""
            user_input = ip_info_text
        
        # 5. 调用AgentExecutor执行agent（非流式，不注入IP基因）
        executor = AgentExecutor(db)
        logger.info(f"开始生成IP定位报告: 用户ID={current_user.id}, IP名称={request.name}, Agent ID={agent_id}")
        
        try:
            response, system_prompt, skills_applied, token_count = await executor.execute_non_stream(
                agent=agent,
                user_input=user_input,
                persona_prompt=None,  # 不注入IP基因，报告只负责生成报告信息
                temperature=0.7,
                max_tokens=3000  # 报告较长，需要更多tokens
            )
            
            logger.debug(f"AI响应接收完成: 响应长度={len(response)}, Token数={token_count}, 使用技能数={len(skills_applied)}")
            
            # 检查响应是否异常：如果响应包含提示词标记，说明返回了错误的响应
            if not response or len(response.strip()) == 0:
                raise BadRequestException("AI返回的响应为空，请重试")
            
            # 检测是否返回了提示词而不是生成的内容
            prompt_markers = ["<<<START_PROMPT>>>", "<<<END_PROMPT>>>", "你现在彻底数字化成为了"]
            if any(marker in response for marker in prompt_markers):
                logger.error(f"检测到AI返回了提示词而非生成内容: 响应前200字符={response[:200]}")
                raise BadRequestException("AI返回了错误的响应格式（返回了提示词而非生成内容），请检查Agent配置或重试")
            
            # 检查响应是否过短（可能是错误响应）
            if len(response.strip()) < 50:
                logger.warning(f"AI响应过短: 响应内容={response[:200]}")
                raise BadRequestException(f"AI返回的响应过短，可能生成失败。响应内容: {response[:200]}")
                
        except BadRequestException:
            raise
        except Exception as e:
            logger.error(f"调用AgentExecutor失败: {e}", exc_info=True)
            raise BadRequestException(f"调用AI服务失败: {str(e)}。请重试。")
        
        # 4. 解析返回的JSON格式报告（增强容错性）
        def extract_json_from_text(text: str) -> dict:
            """
            从文本中提取JSON对象，支持多种格式
            
            Args:
                text: 包含JSON的文本
                
            Returns:
                解析后的JSON字典
                
            Raises:
                ValueError: 无法提取有效的JSON
            """
            if not text:
                raise ValueError("响应文本为空")
            
            text = text.strip()
            
            # 预检查：如果文本看起来不像JSON（没有大括号），提前返回错误
            if '{' not in text:
                raise ValueError(f"响应中未找到JSON对象标记。响应前200字符: {text[:200]}")
            
            # 方法1: 查找JSON代码块（```json ... ```）
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError as e:
                    logger.debug(f"方法1解析失败: {e}")
            
            # 方法2: 查找普通代码块（``` ... ```）
            code_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
            if code_match:
                try:
                    return json.loads(code_match.group(1))
                except json.JSONDecodeError as e:
                    logger.debug(f"方法2解析失败: {e}")
            
            # 方法3: 查找第一个完整的JSON对象（通过括号匹配）
            brace_count = 0
            start_idx = text.find('{')
            if start_idx == -1:
                raise ValueError(f"未找到JSON对象起始标记。响应前200字符: {text[:200]}")
            
            # 找到第一个完整的JSON对象
            json_str = None
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = text[start_idx:i+1]
                        break
            
            if json_str:
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # 如果解析失败，尝试清理后重试
                    json_str_clean = re.sub(r'[^\x20-\x7E\n\r\t]', '', json_str)  # 移除非ASCII字符
                    try:
                        return json.loads(json_str_clean)
                    except json.JSONDecodeError as e:
                        logger.debug(f"方法3清理后解析失败: {e}")
            
            # 方法4: 尝试直接解析整个文本
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.debug(f"方法4直接解析失败: {e}")
            
            # 如果所有方法都失败，返回详细错误信息
            raise ValueError(f"无法从响应中提取有效的JSON对象。响应前500字符: {text[:500]}")
        
        report_data = None
        try:
            report_data = extract_json_from_text(response)
            logger.debug(f"JSON提取成功: 包含字段={list(report_data.keys()) if isinstance(report_data, dict) else 'N/A'}")
        except ValueError as e:
            error_msg = str(e)
            logger.error(
                f"IP定位报告JSON提取失败: {error_msg}\n"
                f"原始响应长度={len(response)}, 前500字符: {response[:500]}\n"
                f"后500字符: {response[-500:] if len(response) > 500 else response}"
            )
            raise BadRequestException(
                f"报告生成失败：无法解析AI返回的JSON格式。\n"
                f"错误详情：{error_msg}\n"
                f"请检查Agent配置，确保返回格式为JSON。如问题持续，请联系管理员。"
            )
        except Exception as e:
            logger.error(
                f"IP定位报告JSON解析异常: {e}\n"
                f"原始响应长度={len(response)}, 前500字符: {response[:500]}",
                exc_info=True
            )
            raise BadRequestException(f"报告生成失败：JSON解析异常（{str(e)}）。请重试。")
        
        # 5. 验证和构建响应
        if not isinstance(report_data, dict) or "report" not in report_data:
            raise BadRequestException("报告生成失败：返回数据格式不正确")
        
        report_dict = report_data.get("report", {})
        score = report_data.get("score", 0)
        score_reason = report_data.get("score_reason", "未提供评分理由")
        
        # 验证评分范围
        if not isinstance(score, int) or score < 0 or score > 100:
            score = 0
            score_reason = "评分数据异常，已重置为0"
        
        # 构建响应对象
        try:
            report_response = IPReportResponse(
                report=IPReportData(**report_dict),
                score=score,
                score_reason=score_reason
            )
        except Exception as e:
            logger.error(f"IP定位报告数据验证失败: {e}, 数据: {report_dict}")
            raise BadRequestException(f"报告生成失败：数据格式验证失败。请重试。")
        
        logger.info(f"IP定位报告生成成功: 用户ID={current_user.id}, IP名称={request.name}, 评分={score}")
        
        return success(data=report_response.model_dump(), msg="报告生成成功")
        
    except NotFoundException:
        raise
    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"IP定位报告生成失败: {e}", exc_info=True)
        raise BadRequestException(f"报告生成失败: {str(e)}")

