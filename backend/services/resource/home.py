"""
首页内容 Service
首页内容聚合服务层（独立于文章管理，专门为小程序首页提供数据）
"""
import json
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.article import Article, ArticleCategory
from models.banner import Banner, BannerPosition
from models.home_config import HomeConfig
from services.resource import BannerService, ArticleService


class HomeService:
    """首页内容服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.banner_service = BannerService(db)
        self.article_service = ArticleService(db)
    
    async def get_home_content(self) -> Dict:
        """
        获取首页内容（聚合接口）
        
        返回：
            - banners: Banner列表（按位置分组）
            - founder_stories: 创始人故事列表（用于轮播）
            - operation_articles: 运营干货列表（用于横向滚动）
            - announcements: 公告列表（最新公告）
            - customer_cases: 客户案例列表（可选）
            - featured_modules: 推荐模块列表（功能入口）
        
        Returns:
            首页内容字典
        """
        # 并行获取所有数据
        banners_task = self._get_enabled_banners()
        founder_stories_task = self._get_articles_by_category(ArticleCategory.FOUNDER_STORY, limit=5)
        operation_articles_task = self._get_articles_by_category(ArticleCategory.OPERATION_ARTICLE, limit=10)
        announcements_task = self._get_articles_by_category(ArticleCategory.ANNOUNCEMENT, limit=3)
        customer_cases_task = self._get_articles_by_category(ArticleCategory.CUSTOMER_CASE, limit=5)
        featured_modules_task = self._get_featured_modules()
        
        # 等待所有任务完成
        banners = await banners_task
        founder_stories = await founder_stories_task
        operation_articles = await operation_articles_task
        announcements = await announcements_task
        customer_cases = await customer_cases_task
        featured_modules = await featured_modules_task
        
        return {
            "banners": banners,
            "founder_stories": founder_stories,
            "operation_articles": operation_articles,
            "announcements": announcements,
            "customer_cases": customer_cases,
            "featured_modules": featured_modules,
        }
    
    async def _get_enabled_banners(self) -> Dict[str, List[Dict]]:
        """
        获取启用的Banner（按位置分组）
        
        Returns:
            按位置分组的Banner字典
        """
        now = datetime.now()
        
        # 查询启用的Banner，且时间范围内有效
        query = select(Banner).where(
            and_(
                Banner.is_enabled == True,
                # 时间范围检查：如果没有设置时间，或者当前时间在时间范围内
                (
                    (Banner.start_time.is_(None)) | (Banner.start_time <= now)
                ),
                (
                    (Banner.end_time.is_(None)) | (Banner.end_time >= now)
                )
            )
        ).order_by(asc(Banner.sort_order), desc(Banner.created_at))
        
        result = await self.db.execute(query)
        banners = result.scalars().all()
        
        # 按位置分组
        banners_by_position: Dict[str, List[Dict]] = {
            "home_top": [],
            "home_middle": [],
            "home_bottom": [],
        }
        
        for banner in banners:
            position = banner.position.value
            if position in banners_by_position:
                banners_by_position[position].append({
                    "id": banner.id,
                    "title": banner.title,
                    "image_url": banner.image_url,
                    "link_url": banner.link_url,
                    "link_type": banner.link_type.value,
                    "position": position,
                    "sort_order": banner.sort_order,
                })
        
        return banners_by_position
    
    async def _get_articles_by_category(
        self,
        category: ArticleCategory,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取指定类型的已发布文章
        
        Args:
            category: 文章类型
            limit: 限制数量
        
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
        
        result = await self.db.execute(query)
        articles = result.scalars().all()
        
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
            
            article_list.append({
                "id": article.id,
                "category": article.category.value,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "cover_image": article.cover_image,
                "tags": tags if isinstance(tags, list) else [],
                "sort_order": article.sort_order,
                "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                "view_count": article.view_count,
                "created_at": article.created_at.isoformat() if article.created_at else None,
            })
        
        return article_list
    
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
            try:
                modules_data = json.loads(config.config_value)
                if not isinstance(modules_data, list):
                    logger.warning("featured_modules 配置格式错误：应为数组")
                    return []
                
                # 转换为小程序需要的格式
                # 数据库格式: { name, icon, link }
                # 小程序格式: { icon, label, route, iconSize }
                featured_modules = []
                for module in modules_data:
                    if isinstance(module, dict):
                        featured_modules.append({
                            "icon": module.get("icon", ""),
                            "label": module.get("name", ""),
                            "route": module.get("link", ""),
                            "iconSize": 20  # 默认图标大小，与组件默认值保持一致
                        })
                
                return featured_modules
            except json.JSONDecodeError as e:
                logger.error(f"解析 featured_modules 配置失败: {e}")
                return []
        except Exception as e:
            logger.error(f"获取 featured_modules 配置失败: {e}")
            return []

