"""
数据库初始化脚本
初始化菜单数据和其他基础数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, async_session_maker, close_db
from app.models.menu import Menu
from app.models.user import User, UserLevel
from app.core.security import get_password_hash


# 初始菜单数据
INITIAL_MENUS = [
    # ========== 首页 ==========
    {
        "name": "home",
        "path": "/home/index",
        "component": "/home/index",
        "title": "数据看板",
        "icon": "HomeFilled",
        "sort_order": 0,
        "is_affix": True,
        "is_keep_alive": True,
    },
    
    # ========== 用户管理 ==========
    {
        "name": "user",
        "path": "/user",
        "redirect": "/user/index",
        "title": "用户管理",
        "icon": "User",
        "sort_order": 10,
        "children": [
            {
                "name": "userManage",
                "path": "/user/index",
                "component": "/user/index",
                "title": "用户列表",
                "icon": "Menu",
                "sort_order": 0,
            },
        ],
    },
    
    # ========== 财务管理 ==========
    {
        "name": "finance",
        "path": "/finance",
        "redirect": "/finance/compute-log",
        "title": "财务管理",
        "icon": "Money",
        "sort_order": 20,
        "children": [
            {
                "name": "computeLog",
                "path": "/finance/compute-log",
                "component": "/finance/compute-log",
                "title": "算力日志",
                "icon": "Menu",
                "sort_order": 0,
            },
        ],
    },
    
    # ========== 小程序管理 ==========
    {
        "name": "miniprogram",
        "path": "/miniprogram",
        "redirect": "/miniprogram/users",
        "title": "小程序管理",
        "icon": "Iphone",
        "sort_order": 30,
        "children": [
            {
                "name": "miniprogramUserManage",
                "path": "/miniprogram/users",
                "component": "/system/userManage/index",
                "title": "用户管理",
                "icon": "User",
                "sort_order": 0,
            },
            {
                "name": "bannerManage",
                "path": "/miniprogram/banner",
                "component": "/miniprogram/banner/index",
                "title": "Banner管理",
                "icon": "Picture",
                "sort_order": 10,
            },
            {
                "name": "homeConfig",
                "path": "/miniprogram/config",
                "component": "/miniprogram/config/index",
                "title": "首页配置",
                "icon": "Setting",
                "sort_order": 20,
            },
        ],
    },
    
    # ========== 智能体管理 ==========
    {
        "name": "agent",
        "path": "/agent",
        "redirect": "/agent/manage",
        "title": "智能体管理",
        "icon": "ChatDotRound",
        "sort_order": 40,
        "children": [
            {
                "name": "agentManage",
                "path": "/agent/manage",
                "component": "/system/agentManage/index",
                "title": "智能体列表",
                "icon": "Menu",
                "sort_order": 0,
            },
        ],
    },
    
    # ========== 系统管理 ==========
    {
        "name": "system",
        "path": "/system",
        "redirect": "/system/menuMange",
        "title": "系统管理",
        "icon": "Tools",
        "sort_order": 100,
        "children": [
            {
                "name": "menuMange",
                "path": "/system/menuMange",
                "component": "/system/menuMange/index",
                "title": "菜单管理",
                "icon": "Menu",
                "sort_order": 0,
            },
            {
                "name": "roleManage",
                "path": "/system/roleManage",
                "component": "/system/roleManage/index",
                "title": "角色管理",
                "icon": "Menu",
                "sort_order": 10,
            },
            {
                "name": "dictManage",
                "path": "/system/dictManage",
                "component": "/system/dictManage/index",
                "title": "字典管理",
                "icon": "Menu",
                "sort_order": 20,
            },
            {
                "name": "systemLog",
                "path": "/system/systemLog",
                "component": "/system/systemLog/index",
                "title": "系统日志",
                "icon": "Menu",
                "sort_order": 30,
            },
        ],
    },
]


async def create_menu(
    session: AsyncSession,
    menu_data: dict,
    parent_id: int = None,
) -> Menu:
    """
    递归创建菜单
    
    Args:
        session: 数据库会话
        menu_data: 菜单数据
        parent_id: 父菜单ID
    
    Returns:
        Menu: 创建的菜单对象
    """
    children_data = menu_data.pop("children", None)
    
    # 创建菜单
    menu = Menu(
        parent_id=parent_id,
        name=menu_data.get("name"),
        path=menu_data.get("path"),
        component=menu_data.get("component"),
        redirect=menu_data.get("redirect"),
        title=menu_data.get("title"),
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
    await session.flush()
    
    logger.info(f"Created menu: {menu.name} - {menu.title}")
    
    # 递归创建子菜单
    if children_data:
        for child_data in children_data:
            await create_menu(session, child_data.copy(), menu.id)
    
    return menu


async def init_menus(session: AsyncSession) -> None:
    """
    初始化菜单数据
    """
    # 检查是否已有菜单数据
    result = await session.execute(select(Menu).limit(1))
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("Menus already exist, skipping initialization")
        return
    
    logger.info("Initializing menus...")
    
    for menu_data in INITIAL_MENUS:
        await create_menu(session, menu_data.copy())
    
    await session.commit()
    logger.info("Menus initialized successfully")


async def init_admin_user(session: AsyncSession) -> None:
    """
    初始化管理员用户
    """
    # 检查是否已有管理员
    result = await session.execute(
        select(User).where(User.username == "admin")
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("Admin user already exists, skipping")
        return
    
    logger.info("Creating admin user...")
    
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        level=UserLevel.PARTNER,
        nickname="管理员",
        is_active=True,
        is_deleted=False,
    )
    
    session.add(admin)
    await session.commit()
    
    logger.info("Admin user created: admin / admin123")


async def main():
    """
    主函数
    """
    logger.info("=" * 50)
    logger.info("Starting database initialization...")
    logger.info("=" * 50)
    
    # 初始化数据库连接
    await init_db()
    
    # 创建数据库表
    from app.db.session import create_tables
    await create_tables()
    
    # 获取数据库会话
    async with async_session_maker() as session:
        try:
            # 初始化管理员用户
            await init_admin_user(session)
            
            # 初始化菜单数据
            await init_menus(session)
            
            logger.info("=" * 50)
            logger.info("Database initialization completed!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            await session.rollback()
            raise
    
    # 关闭数据库连接
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())


