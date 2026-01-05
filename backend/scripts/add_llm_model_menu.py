# -*- coding: utf-8 -*-
"""
添加大模型管理菜单项
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import init_db, async_session_maker, close_db
from models.menu import Menu


async def add_llm_model_menu():
    """添加大模型管理菜单项"""
    logger.info("开始添加大模型管理菜单项...")
    
    # 初始化数据库连接
    await init_db()
    
    # 导入 async_session_maker（在 init_db 之后）
    from db.session import async_session_maker
    
    async with async_session_maker() as session:
        try:
            # 查找系统管理菜单（父菜单）
            result = await session.execute(
                select(Menu).where(Menu.name == "system")
            )
            system_menu = result.scalar_one_or_none()
            
            if not system_menu:
                logger.error("未找到系统管理菜单，请先运行完整初始化脚本")
                return
            
            # 检查菜单是否已存在
            result = await session.execute(
                select(Menu).where(Menu.name == "llmModelManage")
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info("大模型管理菜单已存在，跳过创建")
                return
            
            # 创建大模型管理菜单
            menu = Menu(
                parent_id=system_menu.id,
                name="llmModelManage",
                path="/system/llmModelManage",
                component="/system/llmModelManage/index",
                title="大模型管理",
                icon="Cpu",
                sort_order=15,
                is_hide=False,
                is_full=False,
                is_affix=False,
                is_keep_alive=True,
                is_enabled=True,
            )
            
            session.add(menu)
            await session.commit()
            
            logger.info(f"成功创建大模型管理菜单: {menu.title} (path={menu.path})")
            
        except Exception as e:
            logger.error(f"添加菜单失败: {e}")
            await session.rollback()
            raise
    
    await close_db()


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始添加大模型管理菜单项...")
    logger.info("=" * 60)
    
    try:
        await add_llm_model_menu()
        logger.info("=" * 60)
        logger.info("菜单添加完成！")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

