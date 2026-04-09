"""
首页内容 Service
首页内容聚合服务层（独立于文章管理，专门为小程序首页提供数据）
"""
import json
import ast
import re
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.orm import load_only
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.article import (
    Article,
    ARTICLE_CATEGORY_FOUNDER,
    ARTICLE_CATEGORY_TRAFFIC,
    ARTICLE_CATEGORY_BUSINESS,
    ARTICLE_CATEGORY_MANUAL,
    ARTICLE_CATEGORY_RECENT_LANDING,
    ARTICLE_CATEGORY_LABELS,
)
from models.banner import Banner, BannerPosition
from models.home_config import HomeConfig
from services.resource import BannerService, ArticleService


class HomeService:
    """首页内容服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.banner_service = BannerService(db)
        self.article_service = ArticleService(db)
    
    async def get_home_content(self, position: Optional[str] = None) -> Dict:
        """
        获取首页内容（聚合接口）
        
        Args:
            position: Banner位置筛选，可选 home_top/home_middle/home_bottom/web，不传则返回所有位置
        
        返回：
            - banners: Banner列表（按位置分组）
            - founder_stories: 创始人故事列表（用于轮播）
            - operation_articles: 运营干货列表（category 02，横向滚动）
            - recent_landing_articles: 最近落地列表（category 05）
            - announcements: 公告列表（最新公告）
            - customer_cases: 客户案例列表（可选）
            - featured_modules: 推荐模块列表（功能入口）
        
        Returns:
            首页内容字典
        """
        # 同一 AsyncSession 上不可并发 execute（asyncio.gather 会触发 isce）；
        # 字典、Banner、推荐模块与各类文章均顺序执行。
        category_labels = await self.article_service.get_article_category_label_map()
        banners = await self._get_enabled_banners(position=position)
        featured_modules = await self._get_featured_modules()

        founder_stories = await self._get_articles_by_category(
            ARTICLE_CATEGORY_FOUNDER,
            limit=5,
            category_labels=category_labels,
            include_content=False,
        )
        operation_articles = await self._get_articles_by_category(
            ARTICLE_CATEGORY_TRAFFIC,
            limit=10,
            category_labels=category_labels,
            include_content=False,
        )
        recent_landing_articles = await self._get_articles_by_category(
            ARTICLE_CATEGORY_RECENT_LANDING,
            limit=8,
            category_labels=category_labels,
            include_content=False,
        )
        announcements = await self._get_articles_by_category(
            ARTICLE_CATEGORY_BUSINESS,
            limit=3,
            category_labels=category_labels,
            include_content=False,
        )
        customer_cases = await self._get_articles_by_category(
            ARTICLE_CATEGORY_MANUAL,
            limit=5,
            category_labels=category_labels,
            include_content=False,
        )

        return {
            "banners": banners,
            "founder_stories": founder_stories,
            "operation_articles": operation_articles,
            "recent_landing_articles": recent_landing_articles,
            "announcements": announcements,
            "customer_cases": customer_cases,
            "featured_modules": featured_modules,
        }
    
    async def _get_enabled_banners(self, position: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        获取启用的Banner（按位置分组）
        
        Args:
            position: 位置筛选，可选 home_top/home_middle/home_bottom/web，不传则返回所有位置
        
        Returns:
            按位置分组的Banner字典
        """
        now = datetime.now()
        
        # 查询启用的Banner，且时间范围内有效
        conditions = [
            Banner.is_enabled == True,
            (
                (Banner.start_time.is_(None)) | (Banner.start_time <= now)
            ),
            (
                (Banner.end_time.is_(None)) | (Banner.end_time >= now)
            ),
        ]
        filter_position: Optional[str] = None
        if position:
            try:
                position_enum = BannerPosition(position)
                conditions.append(Banner.position == position_enum)
                filter_position = position
            except ValueError:
                pass  # 无效的 position 值则忽略筛选
        
        query = select(Banner).where(and_(*conditions)).order_by(
            asc(Banner.sort_order), desc(Banner.created_at)
        )
        
        result = await self.db.execute(query)
        banners = result.scalars().all()
        
        # 按位置分组（支持按 position 筛选时只返回该位置）
        all_positions = ["home_top", "home_middle", "home_bottom", "web"]
        banners_by_position: Dict[str, List[Dict]] = {
            p: [] for p in (all_positions if not filter_position else [filter_position])
        }
        
        for banner in banners:
            pos = banner.position.value
            if pos in banners_by_position:
                banners_by_position[pos].append({
                    "id": banner.id,
                    "title": banner.title,
                    "image_url": banner.image_url,
                    "link_url": banner.link_url,
                    "link_type": banner.link_type.value,
                    "position": pos,
                    "sort_order": banner.sort_order,
                })
        
        return banners_by_position
    
    async def _get_articles_by_category(
        self,
        category: str,
        limit: int = 10,
        category_labels: Optional[Dict[str, str]] = None,
        include_content: bool = True,
    ) -> List[Dict]:
        """
        获取指定类型的已发布文章（category 为 sys_dict article_category 的 item_value）
        
        Args:
            category: 文章类型（字典 article_category 的 item_value）
            limit: 限制数量
            category_labels: item_value -> item_label，与文章列表接口 category_name 一致
            include_content: 是否查询正文。首页列表仅需卡片字段，排除 content 可显著减少 DB/网络开销
        
        Returns:
            文章列表
        """
        query = select(Article).where(
            and_(
                Article.category == category,
                Article.is_published == True,
                Article.is_enabled == True,
            )
        ).order_by(
            desc(Article.publish_time),
            desc(Article.created_at),
            asc(Article.sort_order)
        ).limit(limit)
        if not include_content:
            # 不 SELECT 富文本正文列，避免大字段 IO（首页仅展示标题/摘要/封面等）
            query = query.options(
                load_only(
                    Article.id,
                    Article.category,
                    Article.author,
                    Article.title,
                    Article.summary,
                    Article.cover_image,
                    Article.tags,
                    Article.sort_order,
                    Article.publish_time,
                    Article.view_count,
                    Article.is_published,
                    Article.is_enabled,
                    Article.created_at,
                )
            )

        result = await self.db.execute(query)
        articles = result.scalars().all()

        labels = category_labels if category_labels is not None else ARTICLE_CATEGORY_LABELS

        # 格式化响应
        article_list = []
        for article in articles:
            # 处理标签
            tags = article.tags
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            elif tags is None:
                tags = []

            category_name = labels.get(article.category) or ARTICLE_CATEGORY_LABELS.get(
                article.category, article.category
            )

            article_list.append({
                "id": article.id,
                "category": article.category,
                "category_name": category_name,
                "author": article.author,
                "title": article.title,
                "content": article.content if include_content else "",
                "summary": article.summary,
                "cover_image": article.cover_image,
                "tags": tags if isinstance(tags, list) else [],
                "sort_order": article.sort_order,
                "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                "view_count": article.view_count,
                "created_at": article.created_at.isoformat() if article.created_at else None,
            })
        
        return article_list
    
    def _normalize_js_object_to_json(self, js_str: str) -> str:
        """
        将 JavaScript 对象字面量格式转换为有效的 JSON 格式
        
        处理情况：
        1. 属性名没有引号: { icon: "value" } -> { "icon": "value" }
        2. 单引号字符串: { 'icon': 'value' } -> { "icon": "value" }
        3. 混合格式
        
        Args:
            js_str: JavaScript 对象字面量字符串
            
        Returns:
            有效的 JSON 字符串
        """
        # 移除首尾空白
        js_str = js_str.strip()
        
        # 如果已经是有效的 JSON，直接返回
        try:
            json.loads(js_str)
            return js_str
        except json.JSONDecodeError:
            pass
        
        # 处理属性名没有引号的情况
        # 匹配模式: 属性名（字母、数字、下划线）后跟冒号
        # 例如: icon: 或 iconSize: 或 icon_size:
        # 注意：这个正则表达式会匹配所有属性名，包括字符串内的，但通过后续处理可以避免问题
        
        def add_quotes_to_keys(match):
            key = match.group(1)
            # 如果属性名已经包含引号，不处理
            if key.startswith('"') or key.startswith("'"):
                return match.group(0)
            # 为属性名添加双引号
            return f'"{key}":'
        
        # 匹配对象中的属性名（支持驼峰命名和下划线命名）
        # 模式: 字母或下划线开头，后跟字母、数字、下划线的组合，然后是可选空白和冒号
        # 例如: icon:, iconSize:, icon_size:
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
        
        # 替换属性名，添加引号
        # 注意：这个替换可能会错误地匹配字符串内的内容，但对于常见格式应该足够
        json_str = re.sub(pattern, add_quotes_to_keys, js_str)
        
        # 将单引号字符串转换为双引号字符串
        # 注意：需要避免替换字符串内的单引号
        # 简单处理：将 '...' 替换为 "..."
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
        
        return json_str
    
    async def _get_featured_modules(self) -> List[Dict]:
        """
        获取推荐模块配置（功能入口）
        
        从 home_configs 表中读取 featured_modules 配置项
        数据库格式: [{ name: string, icon: string, link: string }]
        返回格式: [{ icon: string, label: string, route?: string, iconSize?: number }]
        
        Returns:
            推荐模块列表
        """
        try:
            # 查询 featured_modules 配置
            query = select(HomeConfig).where(
                and_(
                    HomeConfig.config_key == "featured_modules",
                    HomeConfig.is_enabled == True
                )
            )
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()
            
            if not config or not config.config_value:
                return []
            
            # 解析 JSON 配置值
            config_value = config.config_value.strip()
            
            # 先尝试标准 JSON 解析
            try:
                modules_data = json.loads(config_value)
            except json.JSONDecodeError as e:
                # JSON 解析失败，尝试修复 JavaScript 对象字面量格式
                logger.warning(f"JSON 解析失败，尝试修复 JavaScript 对象字面量格式: {e}")
                try:
                    # 尝试将 JavaScript 对象字面量转换为 JSON
                    normalized_json = self._normalize_js_object_to_json(config_value)
                    modules_data = json.loads(normalized_json)
                    logger.info("成功将 JavaScript 对象字面量转换为 JSON")
                except (json.JSONDecodeError, ValueError) as json_error:
                    # 如果修复失败，尝试使用 ast.literal_eval 解析 Python 字面量（支持单引号）
                    logger.warning(f"JSON 修复失败，尝试使用 Python 字面量解析: {json_error}")
                    try:
                        modules_data = ast.literal_eval(config_value)
                        logger.info("使用 Python 字面量解析成功")
                    except (ValueError, SyntaxError) as ast_error:
                        # 记录详细错误信息，包括原始配置值（截取前200字符）
                        config_preview = config_value[:200] if config_value else "None"
                        logger.error(
                            f"解析 featured_modules 配置失败: JSON错误={e}, "
                            f"JSON修复错误={json_error}, Python字面量错误={ast_error}\n"
                            f"配置值预览: {config_preview}"
                        )
                        return []
            
            # 验证数据类型
            if not isinstance(modules_data, list):
                logger.warning(f"featured_modules 配置格式错误：应为数组，实际类型为 {type(modules_data)}")
                return []
            
            # 转换为小程序需要的格式
            # 数据库格式: { name, icon, link } 或 { icon, label, route, iconSize, agent_id }
            # 小程序格式: { icon, label, route, iconSize }
            featured_modules = []
            for module in modules_data:
                if isinstance(module, dict):
                    route = module.get("route") or module.get("link", "")
                    agent_id = module.get("agent_id") or module.get("agentId")
                    # 当 route 为 aichat 页面且配置了 agent_id 时，自动追加 agentId 参数
                    if agent_id is not None and "/pages/aichat/index" in route:
                        sep = "&" if "?" in route else "?"
                        route = f"{route}{sep}agentId={agent_id}"
                    # 兼容两种格式：
                    # 1. 旧格式: { name, icon, link }
                    # 2. 新格式: { icon, label, route, iconSize, agent_id }
                    featured_modules.append({
                        "icon": module.get("icon", ""),
                        "label": module.get("label") or module.get("name", ""),  # 优先使用 label，兼容 name
                        "route": route,
                        "iconSize": module.get("iconSize", 20)  # 默认图标大小，与组件默认值保持一致
                    })
            
            return featured_modules
        except Exception as e:
            logger.error(f"获取 featured_modules 配置失败: {e}")
            return []

