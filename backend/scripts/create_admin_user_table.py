# -*- coding: utf-8 -*-
"""
创建 admin_users 表的数据库脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, async_session_maker, close_db


async def create_admin_user_table():
    """
    创建 admin_users 表
    """
    logger.info("开始创建 admin_users 表...")
    
    try:
        # 初始化数据库连接
        await init_db()
        logger.info("数据库连接成功")
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 创建 admin_users 表的 SQL
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS admin_users (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(64) UNIQUE NOT NULL COMMENT '用户名',
                    password_hash VARCHAR(256) COMMENT '密码哈希值',
                    email VARCHAR(128) COMMENT '邮箱',
                    role_id BIGINT COMMENT '角色ID',
                    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
                    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否已删除（软删除）',
                    remark TEXT COMMENT '备注信息',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_role_id (role_id),
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员用户表';
                """
                
                # 执行 SQL
                await session.execute(text(create_table_sql))
                await session.commit()
                
                logger.info("admin_users 表创建成功！")
                
                # 检查 roles 表是否存在，如果不存在则提示
                check_roles_sql = """
                SELECT COUNT(*) as count FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = 'roles';
                """
                result = await session.execute(text(check_roles_sql))
                roles_exists = result.scalar() > 0
                
                if not roles_exists:
                    logger.warning("roles 表不存在，请先创建 roles 表后再创建 admin_users 表")
                else:
                    logger.info("roles 表已存在，外键关联正常")
                
            except Exception as e:
                logger.error(f"创建表失败: {e}")
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


async def create_default_admin_user():
    """
    创建默认管理员账户（可选）
    """
    logger.info("开始创建默认管理员账户...")
    
    try:
        # 初始化数据库连接
        await init_db()
        logger.info("数据库连接成功")
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                from app.models.admin_user import AdminUser
                from app.core.security import hash_password
                from sqlalchemy import select
                
                # 检查是否已存在 admin 用户
                result = await session.execute(
                    select(AdminUser).where(AdminUser.username == "admin")
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    logger.warning("默认管理员账户已存在，跳过创建")
                    return
                
                # 创建默认管理员账户
                admin_user = AdminUser(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    email="admin@example.com",
                    role_id=None,  # 需要先创建角色后关联
                    is_active=True,
                    is_deleted=False,
                    remark="默认管理员账户",
                )
                
                session.add(admin_user)
                await session.commit()
                
                logger.info("默认管理员账户创建成功！")
                logger.info("用户名: admin")
                logger.info("密码: admin123")
                logger.warning("请尽快修改默认密码！")
                
            except Exception as e:
                logger.error(f"创建默认管理员账户失败: {e}")
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
    主函数：执行数据库表创建
    """
    logger.info("=" * 60)
    logger.info("开始创建 admin_users 表...")
    logger.info("=" * 60)
    
    # 创建表
    await create_admin_user_table()
    
    # 询问是否创建默认管理员账户
    logger.info("=" * 60)
    logger.info("是否创建默认管理员账户？")
    logger.info("如需创建，请取消注释下面的代码行：")
    logger.info("# await create_default_admin_user()")
    logger.info("=" * 60)
    
    # 取消注释下面这行来创建默认管理员账户
    # await create_default_admin_user()


if __name__ == "__main__":
    asyncio.run(main())



