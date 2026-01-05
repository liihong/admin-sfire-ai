"""
添加智能体配置菜单到数据库
确保菜单已写入menus表并启用
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import init_db, close_db
from models.menu import Menu


async def add_agent_menu(session: AsyncSession) -> None:
    """
    添加智能体配置菜单到数据库
    
    如果菜单已存在，则更新其配置确保启用
    """
    # 检查菜单是否已存在
    result = await session.execute(
        select(Menu).where(Menu.name == "agentManage")
    )
    existing_menu = result.scalar_one_or_none()
    
    if existing_menu:
        logger.info(f"智能体配置菜单已存在 (ID: {existing_menu.id})")
        
        # 确保菜单是启用状态
        if not existing_menu.is_enabled:
            existing_menu.is_enabled = True
            logger.info("已启用智能体配置菜单")
        
        # 更新菜单配置确保正确
        existing_menu.path = "/agent/index"
        existing_menu.component = "/agent/index"
        existing_menu.title = "智能体配置"
        existing_menu.icon = "ChatDotRound"
        existing_menu.sort_order = 2
        existing_menu.is_hide = False
        existing_menu.is_keep_alive = True
        existing_menu.is_affix = False
        existing_menu.is_full = False
        
        await session.flush()
        logger.info("已更新智能体配置菜单")
        return
    
    logger.info("正在创建智能体配置菜单...")
    
    # 创建新菜单
    agent_menu = Menu(
        parent_id=None,  # 顶级菜单
        name="agentManage",
        path="/agent/index",
        component="/agent/index",
        title="智能体配置",
        icon="ChatDotRound",
        sort_order=2,
        is_hide=False,
        is_full=False,
        is_affix=False,
        is_keep_alive=True,
        is_enabled=True,
    )
    
    session.add(agent_menu)
    await session.flush()
    await session.refresh(agent_menu)
    
    logger.info(f"智能体配置菜单创建成功 (ID: {agent_menu.id})")


async def update_menu_sort_orders(session: AsyncSession) -> None:
    """
    更新其他菜单的排序顺序，确保智能体配置在第二个位置
    """
    # 更新用户管理菜单的排序
    result = await session.execute(
        select(Menu).where(Menu.name == "userManage")
    )
    user_menu = result.scalar_one_or_none()
    if user_menu and user_menu.sort_order != 3:
        user_menu.sort_order = 3
        logger.info("已更新用户管理菜单排序为 3")
    
    # 更新财务管理菜单的排序
    result = await session.execute(
        select(Menu).where(Menu.name == "finance")
    )
    finance_menu = result.scalar_one_or_none()
    if finance_menu and finance_menu.sort_order != 4:
        finance_menu.sort_order = 4
        logger.info("已更新财务管理菜单排序为 4")
    
    # 更新应用配置菜单的排序
    result = await session.execute(
        select(Menu).where(Menu.name == "app")
    )
    app_menu = result.scalar_one_or_none()
    if app_menu and app_menu.sort_order != 5:
        app_menu.sort_order = 5
        logger.info("已更新应用配置菜单排序为 5")
    
    await session.flush()


async def main():
    """
    主函数：执行菜单添加
    """
    logger.info("=" * 60)
    logger.info("开始添加智能体配置菜单...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        await init_db()
        
        # 导入 async_session_maker（在 init_db 之后）
        from db.session import async_session_maker
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 添加智能体配置菜单
                await add_agent_menu(session)
                
                # 更新其他菜单的排序
                await update_menu_sort_orders(session)
                
                # 提交事务
                await session.commit()
                
                logger.info("=" * 60)
                logger.info("智能体配置菜单添加完成！")
                logger.info("=" * 60)
                logger.info("菜单已启用，admin用户现在可以访问智能体配置功能")
                
            except Exception as e:
                logger.error(f"添加菜单失败: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        raise
    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

