"""
Project Service - 项目数据持久化服务

使用 SQLAlchemy 异步操作和 Redis 存储活跃项目
"""
import json
import random
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from loguru import logger

from models.project import Project, ProjectStatus
from models.user import User
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    PersonaSettings,
)
from db.redis import RedisCache
from utils.exceptions import (
    NotFoundException,
    BadRequestException,
)
from services.system.permission import PermissionService


class ProjectService:
    """项目管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_projects_by_user(
        self,
        user_id: int,
        include_deleted: bool = False
    ) -> List[Project]:
        """
        获取用户的所有项目，按更新时间倒序
        
        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的项目
        
        Returns:
            项目列表
        """
        query = select(Project).where(Project.user_id == user_id)
        
        if not include_deleted:
            query = query.where(Project.is_deleted == False)
        
        query = query.order_by(desc(Project.updated_at))
        
        result = await self.db.execute(query)
        projects = result.scalars().all()
        
        return list(projects)
    
    async def get_active_ip_count(self, user_id: int) -> int:
        """
        统计用户活跃IP数量（排除冻结和删除的）
        
        Args:
            user_id: 用户ID
        
        Returns:
            活跃IP数量
        """
        query = select(Project).where(
            Project.user_id == user_id,
            Project.is_deleted == False,
            Project.status == ProjectStatus.ACTIVE.value
        )
        
        result = await self.db.execute(query)
        projects = result.scalars().all()
        
        return len(projects)
    
    async def get_project_by_id(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Optional[Project]:
        """
        根据 ID 获取项目
        
        Args:
            project_id: 项目ID
            user_id: 可选的用户ID（用于权限验证）
            include_deleted: 是否包含已删除的项目
        
        Returns:
            项目对象，如果不存在则返回 None
        """
        query = select(Project).where(Project.id == project_id)
        
        if user_id is not None:
            query = query.where(Project.user_id == user_id)
        
        if not include_deleted:
            query = query.where(Project.is_deleted == False)
        
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        
        return project
    
    async def create_project(
        self,
        user_id: int,
        data: ProjectCreate
    ) -> Project:
        """
        创建新项目（带权限检查和并发控制）
        
        支持两种传参方式：
        1. 嵌套方式: persona_settings: { tone: "xxx", introduction: "xxx" }
        2. 扁平方式: 直接传递人设字段（与 persona_settings 字段一一对应）
        
        并发安全：
        - 使用数据库事务+SELECT FOR UPDATE锁定用户记录
        - 在事务内检查权限并创建，确保原子性
        
        Args:
            user_id: 用户ID
            data: 项目创建数据
        
        Returns:
            创建的项目对象
        
        Raises:
            BadRequestException: 权限检查失败（IP数量超限）
        """
        # 1. 检查用户是否可以创建IP（实时检查VIP状态）
        permission_service = PermissionService(self.db)
        can_create, error_msg = await permission_service.check_can_create_ip(user_id)
        
        if not can_create:
            raise BadRequestException(error_msg)
        
        # 2. 使用SELECT FOR UPDATE锁定用户记录，防止并发创建IP
        # 锁定用户记录（SELECT FOR UPDATE），确保在检查权限和创建项目之间不会有其他请求插入
        user_query = select(User).where(
            User.id == user_id,
            User.is_deleted == False
        ).with_for_update()
        
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException("用户不存在")
        
        # 再次检查权限（在锁内检查，确保准确性）
        can_create, error_msg = await permission_service.check_can_create_ip(user_id)
        if not can_create:
            raise BadRequestException(error_msg)
        
        # 3. 创建项目
        # 提取首字母作为头像显示
        avatar_letter = data.name[0].upper() if data.name else 'P'
        
        # 随机选择一个颜色（科技蓝色系）
        colors = ['#3B82F6', '#6366F1', '#8B5CF6', '#0EA5E9', '#14B8A6', '#F97316']
        avatar_color = data.avatar_color or random.choice(colors)
        
        # 处理人设配置（支持嵌套和扁平两种方式）
        persona_settings = {}
        
        # 方式1: 如果传入了嵌套的 persona_settings，直接使用
        if data.persona_settings:
            persona_settings = data.persona_settings.model_dump()
        
        # 方式2: 处理扁平化字段（与 persona_settings 字段一一对应）
        persona_settings, _ = self._merge_persona_fields(persona_settings, data)
        
        project = Project(
            user_id=user_id,
            name=data.name,
            industry=data.industry or "通用",
            avatar_letter=avatar_letter,
            avatar_color=avatar_color,
            persona_settings=persona_settings,
            status=ProjectStatus.ACTIVE.value,  # 新创建的项目默认为正常状态
        )
        
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        
        logger.info(f"Created project {project.id} for user {user_id}")
        
        # 确保 updated_at 已加载，避免后续访问时触发延迟加载
        _ = project.updated_at
        
        # 4. 生成Master Prompt（异步，失败不影响项目创建）
        try:
            from services.project.master_prompt import MasterPromptService, IPFormData
            
            # 辅助函数：从persona_settings和data中提取字段
            def get_field(key: str, default: str = "") -> str:
                """从persona_settings或data中获取字段值"""
                value = persona_settings.get(key)
                if value:
                    return str(value) if value else default
                value = getattr(data, key, None)
                return str(value) if value else default
            
            def get_list_field(key: str, default: list = None) -> list:
                """从persona_settings或data中获取列表字段值"""
                if default is None:
                    default = []
                value = persona_settings.get(key)
                if value and isinstance(value, list):
                    return value
                value = getattr(data, key, None)
                return value if isinstance(value, list) else default
            
            # 构建表单数据字典（从persona_settings和data中提取）
            form_data: IPFormData = {
                "name": data.name,
                "industry": data.industry or "通用",
                "introduction": get_field("introduction"),
                "tone": get_field("tone"),
                "target_audience": get_field("target_audience"),
                "target_pains": get_field("target_pains"),
                "keywords": get_list_field("keywords"),
                "industry_understanding": get_field("industry_understanding"),
                "unique_views": get_field("unique_views"),
                "catchphrase": get_field("catchphrase"),
            }
            
            # 生成Master Prompt
            master_prompt_service = MasterPromptService(self.db)
            master_prompt = await master_prompt_service.generate_master_prompt(
                user_id=user_id,
                form_data=form_data
            )
            
            # 如果生成成功，保存到独立的 master_prompt 字段
            if master_prompt:
                project.master_prompt = master_prompt
                await self.db.flush()
                logger.info(f"Master Prompt已生成并保存: 项目ID={project.id}, 长度={len(master_prompt)}字符")
            else:
                logger.warning(f"Master Prompt生成失败，项目仍可正常使用: 项目ID={project.id}")
        except Exception as e:
            # Master Prompt生成失败不影响项目创建
            logger.error(f"Master Prompt生成异常（项目创建成功）: {e}", exc_info=True)
        
        return project
    
    def _merge_persona_fields(self, current_persona: dict, data) -> tuple[dict, bool]:
        """
        合并扁平化的人设字段到 persona_settings
        
        Args:
            current_persona: 当前的 persona_settings 字典
            data: 包含扁平化人设字段的数据对象
        
        Returns:
            (更新后的 persona_settings, 是否有更新)
        """
        persona_updated = False
        
        # 定义扁平化字段到 persona_settings 的映射
        persona_fields = [
            "introduction",           # IP简介
            "tone",                   # 语气风格
            "target_audience",        # 目标受众
            "content_style",          # 内容风格
            "catchphrase",            # 常用口头禅
            "keywords",               # 常用关键词
            "taboos",                 # 内容禁忌
            "benchmark_accounts",     # 对标账号
            "industry_understanding", # 行业理解（扩展字段）
            "unique_views",           # 独特观点（扩展字段）
            "target_pains",           # 目标人群痛点（扩展字段）
        ]
        
        for field in persona_fields:
            value = getattr(data, field, None)
            if value is not None:
                current_persona[field] = value
                persona_updated = True
                logger.debug(f"Merging persona field: {field} = {value}")
        
        logger.info(f"Persona merge result: updated={persona_updated}, fields={list(current_persona.keys())}")
        return current_persona, persona_updated

    async def update_project(
        self,
        project_id: int,
        user_id: int,
        data: ProjectUpdate
    ) -> Project:
        """
        更新项目
        
        支持两种传参方式：
        1. 嵌套方式: persona_settings: { tone: "xxx", introduction: "xxx" }
        2. 扁平方式: 直接传递人设字段（与 persona_settings 字段一一对应）
        
        Args:
            project_id: 项目ID
            user_id: 用户ID（用于权限验证）
            data: 项目更新数据
        
        Returns:
            更新后的项目对象
        
        Raises:
            NotFoundException: 项目不存在或无权访问
        """
        project = await self.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        
        # 更新基础字段
        if data.name is not None:
            project.name = data.name
            # 如果未单独指定 avatar_letter，则根据名称自动生成
            if data.avatar_letter is None:
                project.avatar_letter = data.name[0].upper() if data.name else 'P'
        
        if data.industry is not None:
            project.industry = data.industry
        
        # 更新头像相关字段
        if data.avatar_letter is not None:
            project.avatar_letter = data.avatar_letter
        
        if data.avatar_color is not None:
            project.avatar_color = data.avatar_color
        
        # 处理人设配置（支持嵌套和扁平两种方式）
        current_persona = project.get_persona_settings_dict()
        persona_updated = False
        
        # 方式1: 如果传入了嵌套的 persona_settings，直接使用
        if data.persona_settings is not None:
            current_persona = data.persona_settings.model_dump()
            # 确保移除 master_prompt（如果存在），因为它是独立字段
            if "master_prompt" in current_persona:
                del current_persona["master_prompt"]
            persona_updated = True
        
        # 方式2: 处理扁平化字段（与 persona_settings 字段一一对应）
        current_persona, flat_updated = self._merge_persona_fields(current_persona, data)
        persona_updated = persona_updated or flat_updated
        
        # 确保从 persona_settings 中移除 master_prompt（如果存在），因为它是独立字段
        if "master_prompt" in current_persona:
            del current_persona["master_prompt"]
            persona_updated = True
        
        # 如果有任何人设配置更新，保存到数据库
        if persona_updated:
            project.persona_settings = current_persona
            # 显式标记 JSON 字段已修改，确保 SQLAlchemy 检测到变化
            flag_modified(project, "persona_settings")
            logger.info(f"Updated persona_settings for project {project_id}: {current_persona}")
        
        await self.db.flush()
        await self.db.refresh(project)
        
        logger.info(f"Updated project {project_id} for user {user_id}")
        
        return project
    
    async def delete_project(
        self,
        project_id: int,
        user_id: int
    ) -> bool:
        """
        删除项目（软删除）
        
        Args:
            project_id: 项目ID
            user_id: 用户ID（用于权限验证）
        
        Returns:
            是否删除成功
        
        Raises:
            NotFoundException: 项目不存在或无权访问
        """
        project = await self.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        
        project.is_deleted = True
        await self.db.flush()
        
        # 如果删除的是活跃项目，清除活跃项目缓存
        active_id = await self.get_active_project(user_id)
        if active_id == project_id:
            await self.set_active_project(user_id, None)
        
        logger.info(f"Deleted project {project_id} for user {user_id}")
        
        return True
    
    async def get_active_project(self, user_id: int) -> Optional[int]:
        """
        获取用户当前激活的项目ID
        
        Args:
            user_id: 用户ID
        
        Returns:
            项目ID，如果没有激活的项目则返回 None
        """
        key = f"user:{user_id}:active_project"
        project_id_str = await RedisCache.get(key)
        
        if project_id_str:
            try:
                return int(project_id_str)
            except (ValueError, TypeError):
                return None
        
        return None
    
    async def set_active_project(
        self,
        user_id: int,
        project_id: Optional[int]
    ) -> bool:
        """
        设置用户当前激活的项目
        
        Args:
            user_id: 用户ID
            project_id: 项目ID，如果为 None 则清除活跃项目
        
        Returns:
            是否设置成功
        
        Raises:
            NotFoundException: 项目不存在或无权访问（当 project_id 不为 None 时）
        """
        key = f"user:{user_id}:active_project"
        
        if project_id is None:
            # 清除活跃项目
            await RedisCache.delete(key)
            logger.info(f"Cleared active project for user {user_id}")
            return True
        
        # 验证项目是否存在且属于该用户
        project = await self.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        
        # 设置活跃项目（缓存7天）
        await RedisCache.set(key, str(project_id), expire=7 * 24 * 3600)
        
        logger.info(f"Set active project {project_id} for user {user_id}")
        
        return True
    
    async def get_user_by_openid(self, openid: str) -> Optional[User]:
        """
        通过 openid 查找用户
        
        Args:
            openid: 微信 openid
        
        Returns:
            用户对象，如果不存在则返回 None
        """
        query = select(User).where(
            User.openid == openid,
            User.is_deleted == False
        )
        
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        return user
    
    async def compress_ip_info(self, raw_info: dict) -> dict:
        """
        压缩IP信息到极限字数
        
        使用AI将收集到的IP信息压缩到以下限制：
        - IP简介：200字以内
        - 目标受众：50字以内
        - 关键词：最多8个
        - 口头禅：保持简短
        
        Args:
            raw_info: 原始IP信息字典，包含：
                - name: 项目名称
                - industry: 赛道
                - introduction: IP简介（可能很长）
                - tone: 语气风格
                - target_audience: 目标受众（可能很长）
                - catchphrase: 口头禅
                - keywords: 关键词列表（可能很多）
                - 其他字段
        
        Returns:
            压缩后的IP信息字典
        """
        from services.content import AIService
        import json
        
        # 构建压缩提示词
        compress_prompt = """你是一个IP信息压缩专家。请将用户提供的IP信息压缩到以下限制：
- IP简介：200字以内（保留核心定位和特色）
- 目标受众：50字以内（保留关键特征）
- 关键词：最多8个（选择最核心的）
- 口头禅：保持简短（如有）

要求：
1. 保留所有核心信息，不能丢失关键内容
2. 语言精炼，去除冗余描述
3. 保持原意不变
4. 输出JSON格式，包含以下字段：name, industry, introduction, tone, target_audience, catchphrase, keywords

原始信息：
"""
        
        # 构建原始信息文本
        raw_text = f"""项目名称：{raw_info.get('name', '')}
所属赛道：{raw_info.get('industry', '')}
IP简介：{raw_info.get('introduction', '')}
语气风格：{raw_info.get('tone', '')}
目标受众：{raw_info.get('target_audience', '')}
口头禅：{raw_info.get('catchphrase', '')}
关键词：{', '.join(raw_info.get('keywords', []))}
"""
        
        # 调用AI服务进行压缩
        ai_service = AIService(self.db)
        messages = [
            {"role": "system", "content": compress_prompt},
            {"role": "user", "content": raw_text + "\n请压缩上述IP信息，输出JSON格式。"}
        ]
        
        # 从环境变量读取模型配置，使用预定义的默认值
        from core.config import settings
        from constants.agent import DEFAULT_MODEL_ID
        model_id = settings.AI_COLLECT_MODEL_ID or DEFAULT_MODEL_ID
        
        try:
            response = await ai_service.chat(
                messages=messages,
                model=model_id,
                temperature=0.3,  # 较低温度，确保输出稳定
                max_tokens=1000
            )
            
            # 提取AI回复
            ai_reply = ""
            if response.get("message"):
                ai_reply = response["message"].get("content", "")
            elif response.get("choices") and len(response["choices"]) > 0:
                ai_reply = response["choices"][0].get("message", {}).get("content", "")
            
            # 尝试从回复中提取JSON
            compressed_info = {}
            
            # 尝试直接解析JSON
            try:
                # 查找JSON代码块
                if "```json" in ai_reply:
                    json_start = ai_reply.find("```json") + 7
                    json_end = ai_reply.find("```", json_start)
                    json_str = ai_reply[json_start:json_end].strip()
                elif "```" in ai_reply:
                    json_start = ai_reply.find("```") + 3
                    json_end = ai_reply.find("```", json_start)
                    json_str = ai_reply[json_start:json_end].strip()
                else:
                    # 尝试直接解析整个回复
                    json_str = ai_reply.strip()
                
                compressed_info = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                # 如果JSON解析失败，尝试手动提取字段
                logger.warning("AI返回的JSON解析失败，尝试手动提取")
                compressed_info = self._extract_info_from_text(ai_reply, raw_info)
            
            # 验证和限制字数
            compressed_info = self._validate_and_limit(compressed_info, raw_info)
            
            logger.info(f"IP信息压缩完成: {compressed_info}")
            return compressed_info
            
        except Exception as e:
            logger.error(f"AI压缩失败: {e}")
            # 如果AI压缩失败，使用简单的截断策略
            return self._simple_compress(raw_info)
    
    def _extract_info_from_text(self, text: str, raw_info: dict) -> dict:
        """从文本中提取信息（备用方案）"""
        import re
        
        result = {
            "name": raw_info.get("name", ""),
            "industry": raw_info.get("industry", "通用"),
            "introduction": raw_info.get("introduction", "")[:200],
            "tone": raw_info.get("tone", "专业亲和"),
            "target_audience": raw_info.get("target_audience", "")[:50],
            "catchphrase": raw_info.get("catchphrase", ""),
            "keywords": raw_info.get("keywords", [])[:8]
        }
        
        # 尝试从文本中提取字段
        intro_match = re.search(r'IP简介[：:]\s*(.+?)(?:\n|$)', text)
        if intro_match:
            result["introduction"] = intro_match.group(1).strip()[:200]
        
        audience_match = re.search(r'目标受众[：:]\s*(.+?)(?:\n|$)', text)
        if audience_match:
            result["target_audience"] = audience_match.group(1).strip()[:50]
        
        return result
    
    def _validate_and_limit(self, compressed_info: dict, raw_info: dict) -> dict:
        """验证和限制字数"""
        # 确保所有必需字段存在
        result = {
            "name": compressed_info.get("name", raw_info.get("name", "")),
            "industry": compressed_info.get("industry", raw_info.get("industry", "通用")),
            "introduction": compressed_info.get("introduction", raw_info.get("introduction", ""))[:200],
            "tone": compressed_info.get("tone", raw_info.get("tone", "专业亲和")),
            "target_audience": compressed_info.get("target_audience", raw_info.get("target_audience", ""))[:50],
            "catchphrase": compressed_info.get("catchphrase", raw_info.get("catchphrase", "")),
            "keywords": compressed_info.get("keywords", raw_info.get("keywords", []))[:8]
        }
        
        # 确保keywords是列表
        if not isinstance(result["keywords"], list):
            if isinstance(result["keywords"], str):
                result["keywords"] = [k.strip() for k in result["keywords"].split(",") if k.strip()][:8]
            else:
                result["keywords"] = []
        
        return result
    
    def _simple_compress(self, raw_info: dict) -> dict:
        """简单的截断压缩（备用方案）"""
        return {
            "name": raw_info.get("name", ""),
            "industry": raw_info.get("industry", "通用"),
            "introduction": raw_info.get("introduction", "")[:200],
            "tone": raw_info.get("tone", "专业亲和"),
            "target_audience": raw_info.get("target_audience", "")[:50],
            "catchphrase": raw_info.get("catchphrase", ""),
            "keywords": raw_info.get("keywords", [])[:8] if isinstance(raw_info.get("keywords"), list) else []
        }

