"""
添加智能体调试中心（Playground）菜单
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, close_db
from app.models.menu import Menu


async def add_playground_menu(session: AsyncSession) -> None:
    """
    添加智能体调试中心菜单（作为智能体管理的子菜单，隐藏）
    """
    # 查找智能体管理菜单（父菜单）
    result = await session.execute(
        select(Menu).where(Menu.name == "agentManage")
    )
    parent_menu = result.scalar_one_or_none()

    if not parent_menu:
        logger.warning("未找到智能体管理菜单，请先创建智能体管理菜单")
        return

    # 检查是否已存在
    result = await session.execute(
        select(Menu).where(Menu.name == "agentPlayground")
    )
    existing_menu = result.scalar_one_or_none()

    if existing_menu:
        logger.info(f"智能体调试中心菜单已存在 (ID: {existing_menu.id})")
        # 更新现有菜单
        existing_menu.path = "/agent/playground/:id"
        existing_menu.component = "/agent/playground/index"
        existing_menu.title = "智能体调试中心"
        existing_menu.icon = "ChatDotRound"
        existing_menu.is_hide = True  # 隐藏菜单（因为是动态路由）
        existing_menu.is_keep_alive = True
        existing_menu.sort_order = 10
        await session.flush()
        logger.info("智能体调试中心菜单已更新")
        return

    # 创建新菜单
    playground_menu = Menu(
        parent_id=parent_menu.id,
        name="agentPlayground",
        path="/agent/playground/:id",
        component="/agent/playground/index",
        title="智能体调试中心",
        icon="ChatDotRound",
        sort_order=10,
        is_hide=True,  # 隐藏菜单（因为是动态路由，通过ID访问）
        is_keep_alive=True,
        is_enabled=True,
    )

    session.add(playground_menu)
    await session.flush()
    await session.refresh(playground_menu)

    logger.info(f"智能体调试中心菜单创建成功 (ID: {playground_menu.id}, 父菜单: {parent_menu.name})")


async def main():
    """
    主函数
    """
    logger.info("=" * 50)
    logger.info("开始添加智能体调试中心菜单...")
    logger.info("=" * 50)

    # 初始化数据库连接
    await init_db()

    # 导入 async_session_maker（在 init_db 之后）
    from app.db.session import async_session_maker

    # 获取数据库会话
    async with async_session_maker() as session:
        try:
            await add_playground_menu(session)
            await session.commit()
            logger.info("=" * 50)
            logger.info("菜单添加完成！")
            logger.info("=" * 50)
        except Exception as e:
            logger.error(f"添加菜单失败: {e}")
            await session.rollback()
            raise

    # 关闭数据库连接
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())

