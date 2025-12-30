"""
数据库初始化脚本
初始化管理员用户和菜单数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, async_session_maker, close_db
from app.models.menu import Menu
from app.models.user import User
from app.core.security import hash_password


async def init_admin_user(session: AsyncSession) -> None:
    """
    初始化管理员用户
    
    创建默认超级管理员：
    - 用户名: admin
    - 密码: admin123 (使用 passlib 加密)
    """
    # 检查是否已存在管理员用户
    result = await session.execute(
        select(User).where(User.username == "admin")
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("管理员用户已存在，跳过创建")
        return
    
    logger.info("正在创建管理员用户...")
    
    # 创建管理员用户
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        is_active=True,
        is_deleted=False,
    )
    
    session.add(admin)
    await session.flush()
    
    logger.info(f"管理员用户创建成功: username=admin, password=admin123")


async def init_menus(session: AsyncSession) -> None:
    """
    初始化菜单数据
    
    菜单结构：
    - 首页/控制台
    - 用户管理
    - 财务管理 (父级)
      - 算力流水 (子级)
    - 应用配置 (父级)
      - 首页配置 (子级)
    """
    # 检查是否已存在菜单数据
    result = await session.execute(select(Menu).limit(1))
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("菜单数据已存在，跳过初始化")
        return
    
    logger.info("正在初始化菜单数据...")
    
    # 定义菜单数据
    menus_data = [
        # 首页/控制台
        {
            "name": "home",
            "path": "/home/index",
            "component": "/home/index",
            "title": "首页",
            "icon": "HomeFilled",
            "sort_order": 1,
            "is_affix": True,
            "is_keep_alive": True,
        },
        # 用户管理
        {
            "name": "userManage",
            "path": "/user/index",
            "component": "/user/index",
            "title": "用户管理",
            "icon": "User",
            "sort_order": 2,
            "is_keep_alive": True,
        },
        # 财务管理 (父级)
        {
            "name": "finance",
            "path": "/finance",
            "title": "财务管理",
            "icon": "Money",
            "sort_order": 3,
            "is_keep_alive": True,
            "children": [
                # 算力流水 (子级)
                {
                    "name": "computeLog",
                    "path": "/finance/compute-log",
                    "component": "/finance/compute-log",
                    "title": "算力明细",
                    "icon": "Menu",
                    "sort_order": 1,
                    "is_keep_alive": True,
                },
            ],
        },
        # 应用配置 (父级)
        {
            "name": "app",
            "path": "/app",
            "title": "小程序装修",
            "icon": "Management",
            "sort_order": 4,
            "is_keep_alive": True,
            "children": [
                # 首页配置 (子级)
                {
                    "name": "appConfig",
                    "path": "/app/config",
                    "component": "/app/config",
                    "title": "首页装修",
                    "icon": "Menu",
                    "sort_order": 1,
                    "is_keep_alive": True,
                },
            ],
        },
    ]
    
    # 创建菜单（递归处理父子关系）
    created_menus = {}  # 用于存储已创建的菜单，key 为 name
    
    async def create_menu_item(menu_data: dict, parent_id: int = None) -> Menu:
        """
        递归创建菜单项
        
        Args:
            menu_data: 菜单数据字典
            parent_id: 父菜单ID
        
        Returns:
            Menu: 创建的菜单对象
        """
        # 检查菜单是否已存在（通过 name 判断）
        name = menu_data["name"]
        if name in created_menus:
            logger.warning(f"菜单 {name} 已存在，跳过创建")
            return created_menus[name]
        
        # 提取子菜单数据（不修改原字典）
        children_data = menu_data.get("children")
        
        # 创建菜单对象
        menu = Menu(
            parent_id=parent_id,
            name=menu_data["name"],
            path=menu_data["path"],
            component=menu_data.get("component"),
            redirect=menu_data.get("redirect"),
            title=menu_data["title"],
            icon=menu_data.get("icon", "Menu"),
            sort_order=menu_data.get("sort_order", 0),
            is_link=menu_data.get("is_link", ""),
            is_hide=menu_data.get("is_hide", False),
            is_full=menu_data.get("is_full", False),
            is_affix=menu_data.get("is_affix", False),
            is_keep_alive=menu_data.get("is_keep_alive", True),
            is_enabled=True,
        )
        
        session.add(menu)
        await session.flush()  # 刷新以获取 ID
        
        # 保存到字典中
        created_menus[name] = menu
        
        logger.info(f"创建菜单: {menu.title} (name={menu.name}, path={menu.path})")
        
        # 递归创建子菜单
        if children_data:
            for child_data in children_data:
                await create_menu_item(child_data.copy(), parent_id=menu.id)
        
        return menu
    
    # 创建所有菜单
    for menu_data in menus_data:
        await create_menu_item(menu_data.copy())
    
    await session.commit()
    logger.info("菜单数据初始化完成")


async def main():
    """
    主函数：执行数据库初始化
    """
    logger.info("=" * 60)
    logger.info("开始数据库初始化...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        await init_db()
        
        # 创建数据库表（如果不存在）
        from app.db.session import create_tables
        await create_tables()
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 初始化管理员用户
                await init_admin_user(session)
                
                # 初始化菜单数据
                await init_menus(session)
                
                logger.info("=" * 60)
                logger.info("数据库初始化完成！")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"初始化失败: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"数据库初始化过程中发生错误: {e}")
        raise
    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

