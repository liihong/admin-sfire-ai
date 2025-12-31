# -*- coding: utf-8 -*-
"""
添加用户管理菜单到系统管理菜单下
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


async def add_user_manage_menu():
    """
    添加用户管理菜单项
    """
    logger.info("开始添加用户管理菜单...")
    
    try:
        # 初始化数据库连接
        await init_db()
        logger.info("数据库连接成功")
        
        # 重新导入 async_session_maker（在 init_db() 之后）
        from app.db.session import async_session_maker
        if async_session_maker is None:
            raise RuntimeError("async_session_maker 未初始化")
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 查找系统管理菜单（父菜单）
                system_menu_result = await session.execute(
                    select(Menu).where(Menu.name == "system")
                )
                system_menu = system_menu_result.scalar_one_or_none()
                
                if not system_menu:
                    logger.error("系统管理菜单不存在，请先运行数据库初始化脚本")
                    return
                
                logger.info(f"找到系统管理菜单，ID: {system_menu.id}")
                
                # 检查用户管理菜单是否已存在
                existing_result = await session.execute(
                    select(Menu).where(Menu.name == "userManage")
                )
                existing_menu = existing_result.scalar_one_or_none()
                
                if existing_menu:
                    logger.warning("用户管理菜单已存在，跳过创建")
                    # 检查是否在系统管理菜单下
                    if existing_menu.parent_id == system_menu.id:
                        logger.info("用户管理菜单已在系统管理菜单下")
                    else:
                        logger.info("更新用户管理菜单的父菜单为系统管理")
                        existing_menu.parent_id = system_menu.id
                        existing_menu.sort_order = 5
                        await session.commit()
                        logger.info("用户管理菜单已更新")
                    return
                
                # 创建用户管理菜单
                user_manage_menu = Menu(
                    parent_id=system_menu.id,
                    name="userManage",
                    path="/system/userManage",
                    component="/system/userManage/index",
                    title="用户管理",
                    icon="User",
                    sort_order=5,
                    is_hide=False,
                    is_enabled=True,
                    is_keep_alive=True,
                )
                
                session.add(user_manage_menu)
                await session.commit()
                
                logger.info("用户管理菜单创建成功！")
                logger.info(f"菜单路径: /system/userManage")
                logger.info(f"组件路径: /system/userManage/index")
                
            except Exception as e:
                logger.error(f"添加菜单失败: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"数据库操作过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # 关闭数据库连接
        await close_db()
        logger.info("数据库连接已关闭")


async def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("开始添加用户管理菜单...")
    logger.info("=" * 60)
    
    await add_user_manage_menu()
    
    logger.info("=" * 60)
    logger.info("完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

