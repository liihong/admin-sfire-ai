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

from db.session import init_db, async_session_maker, close_db
from models.menu import Menu
from models.admin_user import AdminUser
from models.role import Role
from core.security import hash_password


async def init_admin_user(session: AsyncSession) -> None:
    """
    初始化管理员用户
    
    创建默认超级管理员：
    - 用户名: admin
    - 密码: admin123 (使用 passlib 加密)
    """
    # 检查是否已存在管理员用户
    result = await session.execute(
        select(AdminUser).where(AdminUser.username == "admin")
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("管理员用户已存在，跳过创建")
        return
    
    logger.info("正在创建管理员用户...")
    
    # 创建管理员用户
    admin = AdminUser(
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
    - 智能体配置
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
        logger.warning("菜单数据已存在，将更新智能体配置菜单（如果不存在）")
        # 继续执行，确保智能体菜单存在
    
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
        # 智能体配置
        {
            "name": "agentManage",
            "path": "/agent/index",
            "component": "/agent/index",
            "title": "智能体配置",
            "icon": "ChatDotRound",
            "sort_order": 2,
            "is_keep_alive": True,
        },
        # 用户管理
        {
            "name": "userManage",
            "path": "/user/index",
            "component": "/user/index",
            "title": "用户管理",
            "icon": "User",
            "sort_order": 3,
            "is_keep_alive": True,
        },
        # 财务管理 (父级)
        {
            "name": "finance",
            "path": "/finance",
            "title": "财务管理",
            "icon": "Money",
            "sort_order": 4,
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
            "sort_order": 5,
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
            logger.info(f"菜单 {name} 已存在，更新配置")
            menu = created_menus[name]
            # 更新菜单配置
            menu.path = menu_data["path"]
            menu.component = menu_data.get("component")
            menu.redirect = menu_data.get("redirect")
            menu.title = menu_data["title"]
            menu.icon = menu_data.get("icon", "Menu")
            menu.sort_order = menu_data.get("sort_order", 0)
            menu.is_link = menu_data.get("is_link", "")
            menu.is_hide = menu_data.get("is_hide", False)
            menu.is_full = menu_data.get("is_full", False)
            menu.is_affix = menu_data.get("is_affix", False)
            menu.is_keep_alive = menu_data.get("is_keep_alive", True)
            menu.is_enabled = True  # 确保启用
            menu.parent_id = parent_id
            await session.flush()
            return menu
        
        # 检查数据库中是否已存在
        result = await session.execute(select(Menu).where(Menu.name == name))
        db_menu = result.scalar_one_or_none()
        if db_menu:
            logger.info(f"菜单 {name} 在数据库中已存在，更新配置")
            # 更新菜单配置
            db_menu.path = menu_data["path"]
            db_menu.component = menu_data.get("component")
            db_menu.redirect = menu_data.get("redirect")
            db_menu.title = menu_data["title"]
            db_menu.icon = menu_data.get("icon", "Menu")
            db_menu.sort_order = menu_data.get("sort_order", 0)
            db_menu.is_link = menu_data.get("is_link", "")
            db_menu.is_hide = menu_data.get("is_hide", False)
            db_menu.is_full = menu_data.get("is_full", False)
            db_menu.is_affix = menu_data.get("is_affix", False)
            db_menu.is_keep_alive = menu_data.get("is_keep_alive", True)
            db_menu.is_enabled = True  # 确保启用
            db_menu.parent_id = parent_id
            await session.flush()
            created_menus[name] = db_menu
            return db_menu
        
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


async def init_roles(session: AsyncSession) -> None:
    """
    初始化角色数据
    
    创建三个默认角色：
    - normal: 普通用户
    - member: 会员用户
    - partner: 合伙人
    
    角色代码（code）对应users表的level字段
    """
    logger.info("正在初始化角色数据...")
    
    # 定义默认角色数据
    roles_data = [
        {
            "code": "normal",
            "name": "普通用户",
            "description": "普通用户角色",
            "sort_order": 0,
        },
        {
            "code": "member",
            "name": "会员",
            "description": "会员用户角色",
            "sort_order": 1,
        },
        {
            "code": "partner",
            "name": "合伙人",
            "description": "合伙人角色",
            "sort_order": 2,
        },
    ]
    
    # 创建或更新角色
    for role_data in roles_data:
        code = role_data["code"]
        
        # 检查角色是否已存在
        result = await session.execute(
            select(Role).where(Role.code == code)
        )
        existing_role = result.scalar_one_or_none()
        
        if existing_role:
            logger.info(f"角色 {code} 已存在，更新配置")
            # 更新角色信息
            existing_role.name = role_data["name"]
            existing_role.description = role_data["description"]
            existing_role.sort_order = role_data["sort_order"]
        else:
            logger.info(f"创建角色: {role_data['name']} (code={code})")
            # 创建新角色
            role = Role(
                code=code,
                name=role_data["name"],
                description=role_data["description"],
                sort_order=role_data["sort_order"],
            )
            session.add(role)
    
    await session.commit()
    logger.info("角色数据初始化完成")


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
        from db.session import create_tables
        await create_tables()
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 初始化管理员用户
                await init_admin_user(session)
                
                # 初始化角色数据
                await init_roles(session)
                
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

