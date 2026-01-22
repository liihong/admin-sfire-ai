"""
Prompt组装引擎
负责根据技能配置组装完整的Prompt，支持变量渲染和安全防护
"""
import re
import json
import time
from typing import List, Dict, Tuple, Optional
from jinja2 import TemplateError
from jinja2.sandbox import SandboxedEnvironment
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.skill_library import SkillLibrary


# region agent log
# 调试日志配置：仅用于当前 DEBUG 会话，写入本地 NDJSON 文件
_DEBUG_LOG_PATH = r"e:\project\admin-sfire-ai\.cursor\debug.log"


def _debug_log(hypothesis_id: str, location: str, message: str, data: Dict):
    """
    调试日志工具：将关键调试信息写入 NDJSON 日志文件

    注意：
    - 不影响正常业务逻辑，所有异常都会被吞掉
    - 不记录敏感信息（如密码、Token 等）
    """
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": "pre-fix-1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # 避免因为调试日志影响正常功能
        pass
# endregion


# 允许使用的 Jinja2 过滤器（仅保留安全过滤器，移除可能导致 XSS 的过滤器）
_ALLOWED_FILTERS = {
    "upper",
    "lower",
    "capitalize",
    "title",
    "trim",
    "striptags",
    "escape",
}

# 创建安全的沙箱环境，并根据 _ALLOWED_FILTERS 限制可用过滤器
_SANDBOX_ENV = SandboxedEnvironment()
_SANDBOX_ENV.filters = {
    k: v for k, v in _SANDBOX_ENV.filters.items() if k in _ALLOWED_FILTERS
}

# region agent log
_debug_log(
    hypothesis_id="H1",
    location="services/prompt_builder.py:module",
    message="SandboxedEnvironment 初始化完成",
    data={
        "allowed_filters": sorted(list(_ALLOWED_FILTERS)),
        "env_filter_count": len(_SANDBOX_ENV.filters),
    },
)
# endregion


class PromptBuilder:
    """
    Prompt组装引擎

    功能：
    1. 根据skill_ids组装Prompt
    2. 使用jinja2安全渲染变量
    3. 计算token数量
    4. 智能路由：根据输入选择最合适的技能
    """

    # 使用预先在模块级初始化好的沙箱环境，避免类体中作用域问题
    _env = _SANDBOX_ENV

    @staticmethod
    async def build_prompt(
        db: AsyncSession,
        skill_ids: List[int],
        skill_variables: Optional[Dict[int, Dict[str, str]]] = None
    ) -> Tuple[str, int, List[Dict]]:
        """
        组装Prompt（异步版本）

        Args:
            db: 异步数据库会话
            skill_ids: 技能ID数组（按顺序）
            skill_variables: 变量配置 {skill_id: {var: value}}

        Returns:
            (full_prompt, token_count, skills_used)
        """
        # region agent log
        _debug_log(
            hypothesis_id="H2",
            location="services/prompt_builder.py:build_prompt:start",
            message="进入 build_prompt",
            data={
                "skill_ids": skill_ids,
                "has_variables": bool(skill_variables),
            },
        )
        # endregion

        if not skill_ids:
            logger.info("技能ID列表为空，返回空Prompt")
            return "", 0, []

        skill_variables = skill_variables or {}
        prompt_parts = []
        skills_used = []

        # 批量加载所有技能（提高性能）
        result = await db.execute(
            select(SkillLibrary).filter(SkillLibrary.id.in_(skill_ids))
        )
        all_skills = result.scalars().all()
        skills_map = {s.id: s for s in all_skills}

        # 按顺序处理技能
        for order, skill_id in enumerate(skill_ids):
            skill = skills_map.get(skill_id)
            if not skill:
                logger.warning(f"技能 ID={skill_id} 不存在，跳过")
                continue

            if not skill.is_active:
                logger.warning(f"技能 ID={skill_id} ({skill.name}) 已禁用，跳过")
                continue

            # 获取该技能的变量值
            variables = skill_variables.get(skill_id, {})

            # 渲染变量
            try:
                rendered_content = PromptBuilder._safe_render_template(
                    skill.content,
                    variables
                )
            except Exception as e:
                rendered_content = skill.content  # 失败则使用原始内容

            prompt_parts.append(f"## {skill.name}\n{rendered_content}")
            skills_used.append({
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "order": order + 1
            })

        full_prompt = "\n\n".join(prompt_parts)
        token_count = PromptBuilder._estimate_tokens(full_prompt)
        
        logger.info(f"Prompt组装完成: {len(skills_used)}个技能, {token_count}个token")

        # region agent log
        _debug_log(
            hypothesis_id="H2",
            location="services/prompt_builder.py:build_prompt:end",
            message="build_prompt 完成",
            data={
                "skills_used": len(skills_used),
                "token_count": token_count,
            },
        )
        # endregion

        return full_prompt, token_count, skills_used

    @staticmethod
    def _safe_render_template(template_str: str, variables: Dict) -> str:
        """
        安全地渲染模板（防止注入攻击）

        Args:
            template_str: 模板字符串
            variables: 变量字典

        Returns:
            渲染后的字符串

        Raises:
            ValueError: 如果模板包含不安全的操作
        """
        try:
            # 使用沙箱环境解析模板
            template = PromptBuilder._env.from_string(template_str)
            result = template.render(**variables)

            # 额外的安全检查：确保结果中不包含未解析的标签
            if "{{" in result or "{%" in result:
                # 检查是否是未解析的变量（如果是，可能是变量名错误）
                unresolved_vars = re.findall(r'\{\{([^}]+)\}\}', result)
                if unresolved_vars:
                    logger.warning(f"未解析的变量: {unresolved_vars}")

            return result

        except TemplateError as e:
            raise ValueError(f"模板包含不安全的操作或语法错误: {e}")
        except Exception as e:
            raise ValueError(f"模板渲染失败: {e}")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        估算token数量

        Args:
            text: 文本内容

        Returns:
            预估的token数量
        """
        if not text:
            return 0

        # 简化计算：
        # - 中文字符：约1.5字符/token
        # - 英文字符：约4字符/token
        # - 混合文本：取平均值
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars

        tokens = int(chinese_chars / 1.5 + other_chars / 4)
        return max(1, tokens)  # 至少1个token

    @staticmethod
    def extract_persona_prompt(persona_settings: Dict) -> str:
        """
        从 persona_settings 提取IP人设Prompt

        Args:
            persona_settings: IP人设配置

        Returns:
            格式化的IP人设Prompt
        """
        parts = []

        # 基本信息
        introduction = persona_settings.get("introduction", "")
        if introduction:
            parts.append(f"## 自我介绍\n{introduction}")

        # 语气风格
        tone = persona_settings.get("tone", "")
        if tone:
            parts.append(f"## 语气风格\n{tone}")

        # 内容风格
        content_style = persona_settings.get("content_style", "")
        if content_style:
            parts.append(f"## 内容风格\n{content_style}")

        # 目标受众
        target_audience = persona_settings.get("target_audience", "")
        if target_audience:
            parts.append(f"## 目标受众\n{target_audience}")

        # 口头禅
        catchphrase = persona_settings.get("catchphrase", "")
        if catchphrase:
            parts.append(f"## 口头禅\n{catchphrase}")

        # 禁忌
        taboos = persona_settings.get("taboos", [])
        if taboos:
            parts.append(f"## 禁忌\n{', '.join(taboos)}")

        # 关键词
        keywords = persona_settings.get("keywords", [])
        if keywords:
            parts.append(f"## 关键词\n{', '.join(keywords)}")

        # 参考账号
        benchmark_accounts = persona_settings.get("benchmark_accounts", [])
        if benchmark_accounts:
            parts.append(f"## 参考账号\n{', '.join(benchmark_accounts)}")

        if not parts:
            return ""

        return "## IP人设\n\n" + "\n\n".join(parts)

    @staticmethod
    async def intelligent_routing(
        db: AsyncSession,
        user_input: str,
        agent_skill_ids: List[int],
        routing_description: str,
        use_vector: bool = True,
        top_k: int = 3,
        threshold: float = 0.7
    ) -> List[int]:
        """
        智能路由：根据用户输入和路由描述，选择最合适的技能（异步版本）

        Args:
            db: 异步数据库会话
            user_input: 用户输入
            agent_skill_ids: Agent配置的所有技能ID
            routing_description: 路由特征描述
            use_vector: 是否使用向量检索（默认True），False则返回全部技能
            top_k: 选择最相关的K个技能（默认3）
            threshold: 相似度阈值（默认0.7）

        Returns:
            选中的技能ID列表（按优先级排序）
        """
        # region agent log
        _debug_log(
            hypothesis_id="H3",
            location="services/prompt_builder.py:intelligent_routing:start",
            message="进入 intelligent_routing",
            data={
                "agent_skill_ids": agent_skill_ids,
                "user_input_length": len(user_input or ""),
                "use_vector": use_vector,
                "top_k": top_k,
            },
        )
        # endregion

        if not agent_skill_ids:
            logger.info("智能路由: 技能ID列表为空")
            return []

        # 优先使用向量检索
        if use_vector:
            try:
                return await PromptBuilder._intelligent_routing_vector(
                    db=db,
                    user_input=user_input,
                    agent_skill_ids=agent_skill_ids,
                    routing_description=routing_description,
                    top_k=top_k,
                    threshold=threshold
                )
            except Exception as e:
                logger.warning(f"向量检索失败: {e}，返回全部技能")
                # 向量检索失败，返回全部技能
                return agent_skill_ids

        # 不使用向量检索时，直接返回全部技能
        logger.info("未启用向量检索，返回全部技能")
        return agent_skill_ids

    @staticmethod
    async def _intelligent_routing_vector(
        db: AsyncSession,
        user_input: str,
        agent_skill_ids: List[int],
        routing_description: str,
        top_k: int,
        threshold: float
    ) -> List[int]:
        """
        基于向量检索的智能路由（私有方法）

        Args:
            db: 数据库会话
            user_input: 用户输入
            agent_skill_ids: Agent配置的技能ID
            routing_description: 路由描述
            top_k: 选择Top-K
            threshold: 相似度阈值

        Returns:
            选中的技能ID列表
        """
        logger.info(f"使用向量检索进行智能路由 (top_k={top_k}, threshold={threshold})")

        # 获取技能Embedding服务（延迟导入避免循环导入）
        from services.skill import get_skill_embedding_service
        skill_embedding_service = get_skill_embedding_service()

        # 构建搜索查询（用户输入 + 路由描述）
        query = f"{user_input}\n{routing_description}"

        # 先搜索所有相似技能（不应用阈值），以便后续回退处理
        # 搜索更多结果以确保有足够的候选
        all_similar_skills = await skill_embedding_service.search_similar_skills(
            query_text=query,
            top_k=top_k * 3,  # 搜索更多结果
            threshold=0.0  # 不应用阈值，获取所有结果
        )
        
        logger.debug(f"向量检索获取到 {len(all_similar_skills)} 个候选技能（不应用阈值）")

        # 过滤出Agent配置的技能ID
        agent_skill_set = set(agent_skill_ids)
        selected_skills = []
        fallback_skills = []  # 低于阈值但可用的技能

        # 先尝试选择符合阈值的技能
        for skill_id, similarity, metadata in all_similar_skills:
            if skill_id in agent_skill_set:
                if similarity >= threshold:
                    selected_skills.append((skill_id, similarity))
                    logger.debug(f"向量路由: 技能 {metadata.get('name')} (ID={skill_id}) 相似度={similarity:.3f} (符合阈值)")

                    # 达到top_k个就停止
                    if len(selected_skills) >= top_k:
                        break
                else:
                    # 记录低于阈值但可用的技能（用于回退）
                    fallback_skills.append((skill_id, similarity, metadata))

        # 如果找到符合阈值的技能，直接返回
        if selected_skills:
            # 按相似度排序并返回ID列表
            selected_skills.sort(key=lambda x: x[1], reverse=True)
            selected_ids = [skill_id for skill_id, _ in selected_skills]
            logger.info(f"向量路由完成: 从{len(agent_skill_ids)}个技能中选择了{len(selected_ids)}个（符合阈值）")
            return selected_ids

        # 如果没有找到符合阈值的技能，尝试使用低于阈值的技能
        if fallback_skills:
            logger.warning(f"向量检索未找到符合阈值的技能（阈值={threshold}），使用低于阈值的技能")
            # 按相似度排序，选择top_k个
            fallback_skills.sort(key=lambda x: x[1], reverse=True)
            selected_skills = [(skill_id, similarity) for skill_id, similarity, _ in fallback_skills[:top_k]]
            selected_ids = [skill_id for skill_id, _ in selected_skills]
            logger.info(f"向量路由完成: 从{len(agent_skill_ids)}个技能中选择了{len(selected_ids)}个（低于阈值但可用）")
            return selected_ids

        # 如果完全没有相似结果，返回全部技能ID（保证至少有技能可用）
        logger.warning("向量检索无任何相似结果，返回全部Agent配置的技能")
        return agent_skill_ids


    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 文本内容

        Returns:
            关键词列表
        """
        if not text:
            return []

        # 简单的关键词提取：分词并过滤常见停用词
        # 移除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)

        # 分词（中文按字符，英文按单词）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())

        # 简单的停用词列表
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', '的', '了',
            '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这'
        }

        # 过滤停用词和短词
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords

    @staticmethod
    def _calculate_relevance(
        input_keywords: List[str],
        skill_keywords: List[str],
        routing_keywords: List[str]
    ) -> float:
        """
        计算相关性得分

        Args:
            input_keywords: 用户输入的关键词
            skill_keywords: 技能的关键词
            routing_keywords: 路由描述的关键词

        Returns:
            相关性得分（0-1之间）
        """
        if not input_keywords or not skill_keywords:
            return 0.0

        # 计算输入关键词和技能关键词的交集
        input_set = set(input_keywords)
        skill_set = set(skill_keywords)
        routing_set = set(routing_keywords)

        # 基础得分：输入和技能的匹配度
        intersection = input_set & skill_set
        if not intersection:
            return 0.0

        base_score = len(intersection) / len(skill_set)

        # 加权得分：如果技能也匹配路由描述，提升权重
        routing_intersection = intersection & routing_set
        if routing_intersection:
            routing_bonus = len(routing_intersection) / len(routing_set) if routing_set else 0
            base_score += routing_bonus * 0.5

        return min(base_score, 1.0)  # 确保得分不超过1
