# -*- coding: utf-8 -*-
"""
创建项目（Project）数据表
用于小程序项目管理功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from loguru import logger

from db import session as db_session
from models.project import Project


async def create_projects_table():
    """创建 projects 表"""
    try:
        logger.info("开始创建 projects 表...")
        
        # 初始化数据库连接
        await db_session.init_db()
        
        # 使用模块级别的 engine，而不是导入的引用
        engine = db_session.engine
        
        if engine is None:
            raise RuntimeError("数据库引擎未初始化")
        
        async with db_session.engine.begin() as conn:
            # 检查表是否已存在
            check_table_sql = text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'projects'
            """)
            
            result = await conn.execute(check_table_sql)
            table_exists = result.scalar() > 0
            
            if table_exists:
                logger.warning("projects 表已存在，跳过创建")
                return
            
            # 创建 projects 表
            # 注意：MySQL 的 JSON 列不能设置 DEFAULT 值，需要在应用层处理
            create_table_sql = text("""
                CREATE TABLE projects (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                    user_id BIGINT UNSIGNED NOT NULL COMMENT '关联用户ID',
                    name VARCHAR(100) NOT NULL COMMENT '项目名称',
                    industry VARCHAR(50) NOT NULL DEFAULT '通用' COMMENT '赛道',
                    avatar_letter VARCHAR(10) NOT NULL DEFAULT '' COMMENT '项目首字母',
                    avatar_color VARCHAR(20) NOT NULL DEFAULT '#3B82F6' COMMENT '头像背景色',
                    persona_settings JSON NOT NULL COMMENT 'IP人设配置（JSON格式）',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已删除（软删除）',
                    INDEX ix_projects_user_id (user_id),
                    INDEX ix_projects_updated_at (updated_at),
                    INDEX ix_projects_is_deleted (is_deleted),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目/IP表'
            """)
            
            await conn.execute(create_table_sql)
            logger.info("✅ projects 表创建成功")
            
    except Exception as e:
        logger.error(f"❌ 创建 projects 表失败: {e}")
        raise
    finally:
        if db_session.engine:
            await db_session.engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_projects_table())

