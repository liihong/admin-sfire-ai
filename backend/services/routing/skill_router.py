"""
Skill Router：技能分类与路由
纯函数式设计，不涉及业务逻辑（会话、算力、LLM调用等）
"""
import json
import re
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from models.skill_library import SkillLibrary
from models.agent import Agent
from models.llm_model import LLMModel
from services.prompt_builder import PromptBuilder
from services.llm_service import LLMFactory
from services.llm_model import LLMModelService
from sqlalchemy import select
from .types import RoutingResult


class SkillRouter:
    """技能路由器：负责技能分类和路由选择"""
    
    @staticmethod
    async def classify_skills(
        db: AsyncSession,
        skill_ids: List[int]
    ) -> Dict[str, List[int]]:
        """
        分类技能：将技能分为静态技能和动态规则技能
        
        Args:
            db: 异步数据库会话
            skill_ids: 技能ID列表
        
        Returns:
            字典，包含：
            - static_skills: 静态技能ID列表（非rule类型）
            - dynamic_rule_skills: 动态规则技能ID列表（rule类型且meta_description不为空）
        """
        if not skill_ids:
            return {
                "static_skills": [],
                "dynamic_rule_skills": []
            }
        
        # 批量查询所有技能
        result = await db.execute(
            select(SkillLibrary).filter(
                SkillLibrary.id.in_(skill_ids),
                SkillLibrary.status == 1  # 只查询启用的技能
            )
        )
        skills = result.scalars().all()
        skills_map = {s.id: s for s in skills}
        
        static_skills = []
        dynamic_rule_skills = []
        
        for skill_id in skill_ids:
            skill = skills_map.get(skill_id)
            if not skill:
                logger.warning(f"技能 ID={skill_id} 不存在，跳过")
                continue
            
            # 分类逻辑：
            # - rule类型且meta_description不为空：动态规则技能
            # - 其他类型：静态技能
            if skill.category == "rule" and skill.meta_description:
                dynamic_rule_skills.append(skill_id)
            else:
                static_skills.append(skill_id)
        
        logger.debug(
            f"技能分类完成: 静态={len(static_skills)}个, "
            f"动态规则={len(dynamic_rule_skills)}个"
        )
        
        return {
            "static_skills": static_skills,
            "dynamic_rule_skills": dynamic_rule_skills
        }
    
    @staticmethod
    async def route_skills(
        db: AsyncSession,
        agent_skill_ids: List[int],
        user_input: str,
        routing_description: str,
        use_vector: bool = True,
        top_k: int = 3,
        threshold: float = 0.7,
        router_agent_id: Optional[int] = None
    ) -> RoutingResult:
        """
        路由技能：根据用户输入选择最合适的技能
        
        Args:
            db: 异步数据库会话
            agent_skill_ids: Agent配置的所有技能ID
            user_input: 用户输入
            routing_description: 路由特征描述
            use_vector: 是否使用向量检索（默认True）
            top_k: 选择最相关的K个技能（默认3）
            threshold: 相似度阈值（默认0.7）
        
        Returns:
            RoutingResult: 路由结果
        """
        if not agent_skill_ids:
            logger.info("技能路由: 技能ID列表为空")
            return RoutingResult(
                selected_skill_ids=[],
                static_skill_ids=[],
                dynamic_skill_ids=[],
                routing_method="static"
            )
        
        # 1. 分类技能
        classification = await SkillRouter.classify_skills(db, agent_skill_ids)
        static_skill_ids = classification["static_skills"]
        dynamic_rule_skill_ids = classification["dynamic_rule_skills"]
        
        # 2. 静态技能直接加入结果
        selected_skill_ids = static_skill_ids.copy()
        
        # 3. 动态规则技能进行路由选择
        if dynamic_rule_skill_ids:
            selected_dynamic_skills = []
            routing_method = "static"
            
            # 策略1: 向量检索（如果启用）
            if use_vector:
                try:
                    selected_dynamic_skills = await PromptBuilder.intelligent_routing(
                        db=db,
                        user_input=user_input,
                        agent_skill_ids=dynamic_rule_skill_ids,
                        routing_description=routing_description,
                        use_vector=True,
                        top_k=top_k,
                        threshold=threshold
                    )
                    # 检查是否返回了全部技能（说明没有筛选，应该尝试LLM路由）
                    if selected_dynamic_skills and len(selected_dynamic_skills) == len(dynamic_rule_skill_ids):
                        # 返回了全部技能，说明向量检索没有筛选效果，尝试LLM路由
                        logger.warning(
                            f"向量检索返回了全部{len(selected_dynamic_skills)}个技能，"
                            f"未进行筛选，尝试LLM路由"
                        )
                        raise ValueError("向量检索返回全部技能，未进行筛选")
                    elif selected_dynamic_skills:
                        # 向量检索有筛选结果
                        routing_method = "vector"
                        logger.info(
                            f"向量路由完成: 从{len(dynamic_rule_skill_ids)}个规则中选择了"
                            f"{len(selected_dynamic_skills)}个"
                        )
                    else:
                        # 向量检索无结果，尝试LLM路由
                        logger.warning("向量检索返回空列表，尝试LLM路由")
                        raise ValueError("向量检索无结果")
                except Exception as e:
                    logger.warning(f"向量检索失败: {e}，尝试LLM路由")
                    # 降级到LLM路由
                    if router_agent_id:
                        logger.info(
                            f"开始LLM路由: 路由Agent ID={router_agent_id}, "
                            f"动态规则数量={len(dynamic_rule_skill_ids)}"
                        )
                        try:
                            selected_dynamic_skills = await SkillRouter._route_with_llm(
                                db=db,
                                router_agent_id=router_agent_id,
                                dynamic_skill_ids=dynamic_rule_skill_ids,
                                user_input=user_input,
                                routing_description=routing_description,
                                top_k=top_k
                            )
                            routing_method = "llm"
                            logger.info(
                                f"LLM路由完成: 从{len(dynamic_rule_skill_ids)}个规则中选择了"
                                f"{len(selected_dynamic_skills)}个技能，"
                                f"选中的技能ID={selected_dynamic_skills}"
                            )
                        except Exception as llm_error:
                            logger.warning(f"LLM路由失败: {llm_error}，使用全部规则")
                            # LLM路由失败，直接使用全部规则
                            selected_dynamic_skills = dynamic_rule_skill_ids
                            routing_method = "fallback"
                    else:
                        # LLM路由不可用，直接使用全部规则
                        logger.warning("未配置ROUTER_AGENT_ID，跳过LLM路由，使用全部规则")
                        selected_dynamic_skills = dynamic_rule_skill_ids
                        routing_method = "fallback"
            else:
                # 不使用向量检索，直接使用全部规则
                logger.info("未启用向量检索，使用全部规则")
                selected_dynamic_skills = dynamic_rule_skill_ids
                routing_method = "fallback"
            
            selected_skill_ids.extend(selected_dynamic_skills)
        else:
            routing_method = "static"
        
        return RoutingResult(
            selected_skill_ids=selected_skill_ids,
            static_skill_ids=static_skill_ids,
            dynamic_skill_ids=dynamic_rule_skill_ids,
            routing_method=routing_method
        )
    
    @staticmethod
    async def _route_with_llm(
        db: AsyncSession,
        router_agent_id: int,
        dynamic_skill_ids: List[int],
        user_input: str,
        routing_description: str,
        top_k: int = 3
    ) -> List[int]:
        """
        使用LLM进行智能路由（私有方法）
        
        Args:
            db: 异步数据库会话
            router_agent_id: 路由Agent的ID（存储Prompt模板和模型配置）
            dynamic_skill_ids: 动态规则技能ID列表
            user_input: 用户输入
            routing_description: 路由特征描述
            top_k: 选择最相关的K个技能
        
        Returns:
            选中的技能ID列表
        
        Raises:
            Exception: 如果路由失败，会抛出异常（触发降级策略）
        """
        # 1. 读取路由Agent配置（包含system_prompt和model）
        result = await db.execute(
            select(Agent).filter(Agent.id == router_agent_id)
        )
        router_agent = result.scalar_one_or_none()
        if not router_agent:
            raise ValueError(f"路由Agent ID={router_agent_id} 不存在")
        
        if router_agent.status != 1:
            raise ValueError(f"路由Agent ID={router_agent_id} 未上架")
        
        if not router_agent.model:
            raise ValueError(f"路由Agent ID={router_agent_id} 未配置模型")
        
        logger.info(
            f"使用LLM路由: Agent={router_agent.name} (ID={router_agent_id}), "
            f"模型={router_agent.model}, "
            f"动态规则数量={len(dynamic_skill_ids)}"
        )
        
        # 2. 构建技能清单字符串
        result = await db.execute(
            select(SkillLibrary).filter(
                SkillLibrary.id.in_(dynamic_skill_ids),
                SkillLibrary.status == 1
            )
        )
        skills = result.scalars().all()
        skills_map = {s.id: s for s in skills}
        
        module_list_parts = []
        for skill_id in dynamic_skill_ids:
            skill = skills_map.get(skill_id)
            if not skill:
                continue
            module_list_parts.append(
                f"技能ID: {skill.id}\n"
                f"名称: {skill.name}\n"
                f"分类: {skill.category}\n"
                f"特征描述: {skill.meta_description or '无'}\n"
                f"---"
            )
        module_list = "\n".join(module_list_parts)
        
        # 3. 使用PromptBuilder._safe_render_template渲染Prompt模板
        template_variables = {
            "module_list": module_list,
            "user_input": user_input,
            "routing_description": routing_description or "",
            "top_k": top_k
        }
        
        try:
            rendered_prompt = PromptBuilder._safe_render_template(
                router_agent.system_prompt,
                template_variables
            )
        except Exception as e:
            logger.error(f"渲染路由Prompt模板失败: {e}")
            raise ValueError(f"渲染路由Prompt模板失败: {str(e)}")
        
        # 4. 使用Agent配置的model查询llm_models表获取模型配置，然后创建LLM客户端
        try:
            # 先查询数据库获取LLMModel对象
            # router_agent.model 可能是模型ID（数据库主键）、model_id（模型标识）或provider
            llm_model = None
            
            # 尝试作为数据库ID查询
            if router_agent.model.isdigit():
                try:
                    llm_model_service = LLMModelService(db)
                    llm_model = await llm_model_service.get_llm_model_by_id(int(router_agent.model))
                except Exception:
                    llm_model = None
            
            # 如果还没找到，尝试通过model_id字段查询
            if not llm_model:
                llm_model_service = LLMModelService(db)
                llm_model = await llm_model_service.get_llm_model_by_model_id(router_agent.model)
            
            # 如果还是找不到，尝试通过provider查询
            if not llm_model:
                result = await db.execute(
                    select(LLMModel).where(
                        LLMModel.provider == router_agent.model.lower(),
                        LLMModel.is_enabled == True
                    ).order_by(LLMModel.sort_order).limit(1)
                )
                llm_model = result.scalar_one_or_none()
            
            if not llm_model:
                raise ValueError(f"路由Agent配置的模型 '{router_agent.model}' 在llm_models表中不存在或未启用")
            
            if not llm_model.is_enabled:
                raise ValueError(f"路由Agent配置的模型 '{llm_model.name}' 未启用")
            
            if not llm_model.api_key:
                raise ValueError(f"路由Agent配置的模型 '{llm_model.name}' 未配置API Key")
            
            logger.info(
                f"从llm_models表查询到模型配置: {llm_model.name} "
                f"(ID={llm_model.id}, provider={llm_model.provider}, model_id={llm_model.model_id})"
            )
            
            # 使用查询到的模型ID创建LLM客户端
            llm_client = await LLMFactory.create_from_db(db, llm_model.id)
        except Exception as e:
            logger.error(f"创建路由LLM客户端失败: Agent模型={router_agent.model}, 错误={e}")
            raise ValueError(f"创建路由LLM客户端失败: {str(e)}")
        
        # 5. 直接调用llm_client.generate_text（非流式，不涉及会话和算力）
        try:
            # 构建用户消息（如果需要，可以从模板中提取，这里简化处理）
            user_message = f"用户输入：{user_input}"
            
            logger.info(
                f"开始调用LLM进行路由: 用户输入长度={len(user_input)}, "
                f"Prompt长度={len(rendered_prompt)}"
            )
            
            response = await llm_client.generate_text(
                prompt=user_message,
                system_prompt=rendered_prompt,
                temperature=0.3,  # 较低温度，更确定性
                max_tokens=500  # 足够返回JSON
            )
            
            logger.info(f"LLM路由调用成功: 返回内容长度={len(response)}")
            logger.debug(f"LLM路由返回内容: {response[:500]}...")  # 只记录前500字符
        except Exception as e:
            logger.error(f"LLM路由调用失败: {e}", exc_info=True)
            raise ValueError(f"LLM路由调用失败: {str(e)}")
        
        # 6. 解析JSON返回结果，提取target_ids
        logger.info("开始解析LLM返回的JSON结果")
        try:
            # 尝试直接解析JSON
            parsed_result = json.loads(response)
            logger.debug(f"JSON解析成功: {parsed_result}")
        except json.JSONDecodeError:
            # 尝试提取markdown代码块中的JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    parsed_result = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    # 尝试使用正则表达式提取target_ids数组
                    ids_match = re.search(r'"target_ids"\s*:\s*\[([^\]]+)\]', response)
                    if ids_match:
                        ids_str = ids_match.group(1)
                        # 提取数字ID
                        ids = [int(x.strip()) for x in re.findall(r'\d+', ids_str)]
                        parsed_result = {"target_ids": ids}
                    else:
                        raise ValueError("无法解析LLM返回的JSON")
            else:
                # 尝试使用正则表达式提取target_ids数组
                ids_match = re.search(r'"target_ids"\s*:\s*\[([^\]]+)\]', response)
                if ids_match:
                    ids_str = ids_match.group(1)
                    ids = [int(x.strip()) for x in re.findall(r'\d+', ids_str)]
                    parsed_result = {"target_ids": ids}
                else:
                    raise ValueError("无法解析LLM返回的JSON")
        
        # 7. 验证技能ID有效性（过滤不在dynamic_skills中的ID）
        target_ids = parsed_result.get("target_ids", [])
        if not isinstance(target_ids, list):
            logger.warning(f"LLM返回的target_ids不是列表: {target_ids}")
            target_ids = []
        
        logger.info(
            f"LLM返回的target_ids: {target_ids}, "
            f"候选技能ID: {dynamic_skill_ids}"
        )
        
        # 过滤有效的技能ID
        valid_skill_ids = [sid for sid in target_ids if sid in dynamic_skill_ids]
        invalid_ids = [sid for sid in target_ids if sid not in dynamic_skill_ids]
        
        if invalid_ids:
            logger.warning(f"LLM返回了无效的技能ID: {invalid_ids}，已过滤")
        
        if not valid_skill_ids:
            logger.warning(
                f"LLM路由未返回有效的技能ID，返回的技能ID: {target_ids}, "
                f"候选技能ID: {dynamic_skill_ids}"
            )
            raise ValueError("LLM路由未返回有效的技能ID")
        
        logger.info(
            f"LLM路由完成: 从{len(dynamic_skill_ids)}个动态规则中选择了"
            f"{len(valid_skill_ids)}个技能，选中的技能ID={valid_skill_ids}"
        )
        
        return valid_skill_ids

