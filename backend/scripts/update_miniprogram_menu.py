# -*- coding: utf-8 -*-
"""
更新小程序管理菜单
将"首页装修"菜单重命名为"小程序管理"，并更新子菜单路径
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


async def update_miniprogram_menu():
    """
    更新小程序管理菜单
    """
    logger.info("开始更新小程序管理菜单...")
    
    try:
        # 初始化数据库连接
        await init_db()
        logger.info("数据库连接成功")
        
        # 重新导入 async_session_maker（在 init_db() 之后）
        from db.session import async_session_maker
        if async_session_maker is None:
            raise RuntimeError("async_session_maker 未初始化")
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 查找"首页装修"菜单（name="app"）
                app_menu_result = await session.execute(
                    select(Menu).where(Menu.name == "app")
                )
                app_menu = app_menu_result.scalar_one_or_none()
                
                if not app_menu:
                    logger.warning("未找到'首页装修'菜单，可能已经更新或不存在")
                    return
                
                logger.info(f"找到菜单: {app_menu.title} (ID: {app_menu.id})")
                
                # 更新主菜单
                app_menu.name = "miniprogram"
                app_menu.path = "/miniprogram"
                app_menu.redirect = "/miniprogram/users"
                app_menu.title = "小程序管理"
                app_menu.icon = "Iphone"
                
                await session.flush()
                logger.info("主菜单更新成功")
                
                # 查找并更新子菜单
                children_result = await session.execute(
                    select(Menu).where(Menu.parent_id == app_menu.id).order_by(Menu.sort_order)
                )
                children = children_result.scalars().all()
                
                logger.info(f"找到 {len(children)} 个子菜单")
                
                # 检查是否已有用户管理菜单
                user_manage_exists = False
                for child in children:
                    if child.name == "miniprogramUserManage":
                        user_manage_exists = True
                        break
                
                # 如果没有用户管理菜单，创建它
                if not user_manage_exists:
                    user_manage_menu = Menu(
                        parent_id=app_menu.id,
                        name="miniprogramUserManage",
                        path="/miniprogram/users",
                        component="/system/userManage/index",
                        title="用户管理",
                        icon="User",
                        sort_order=0,
                        is_hide=False,
                        is_enabled=True,
                        is_keep_alive=True,
                    )
                    session.add(user_manage_menu)
                    logger.info("创建用户管理子菜单")
                
                # 更新现有子菜单
                for child in children:
                    if child.name == "appConfig":
                        child.name = "homeConfig"
                        child.path = "/miniprogram/config"
                        child.component = "/miniprogram/config/index"
                        child.title = "首页配置"
                        child.icon = "Setting"
                        child.sort_order = 20
                        logger.info(f"更新菜单: {child.title}")
                    elif child.name == "bannerManage":
                        child.path = "/miniprogram/banner"
                        child.component = "/miniprogram/banner/index"
                        child.icon = "Picture"
                        child.sort_order = 10
                        logger.info(f"更新菜单: {child.title}")
                    elif child.name == "moduleManage":
                        # 可以选择删除或保留模块管理
                        # 这里选择删除，因为计划中没有包含
                        logger.info(f"删除菜单: {child.title}")
                        await session.delete(child)
                
                await session.commit()
                
                logger.info("=" * 60)
                logger.info("小程序管理菜单更新成功！")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"更新菜单失败: {e}")
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
    logger.info("开始更新小程序管理菜单...")
    logger.info("=" * 60)
    
    await update_miniprogram_menu()
    
    logger.info("=" * 60)
    logger.info("完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

