# -*- coding: utf-8 -*-
"""
创建小程序管理相关数据表
包括 banners 和 home_configs 表
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, close_db


async def create_banners_table(session: AsyncSession) -> None:
    """创建 banners 表"""
    logger.info("Creating banners table...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS banners (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(128) NOT NULL COMMENT 'Banner标题',
        image_url VARCHAR(512) NOT NULL COMMENT '图片URL',
        link_url VARCHAR(512) COMMENT '跳转链接',
        link_type VARCHAR(16) NOT NULL DEFAULT 'none' COMMENT '链接类型: none-无链接, internal-内部链接, external-外部链接',
        sort_order BIGINT NOT NULL DEFAULT 0 COMMENT '排序顺序（数字越小越靠前）',
        position VARCHAR(32) NOT NULL DEFAULT 'home_top' COMMENT 'Banner位置: home_top-首页顶部, home_middle-首页中部, home_bottom-首页底部',
        start_time DATETIME COMMENT '开始时间（可选）',
        end_time DATETIME COMMENT '结束时间（可选）',
        is_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX ix_banners_position (position),
        INDEX ix_banners_sort_order (sort_order),
        INDEX ix_banners_is_enabled (is_enabled)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Banner表';
    """
    
    await session.execute(text(create_table_sql))
    await session.commit()
    logger.info("Banners table created successfully")


async def create_home_configs_table(session: AsyncSession) -> None:
    """创建 home_configs 表"""
    logger.info("Creating home_configs table...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS home_configs (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        config_key VARCHAR(64) NOT NULL UNIQUE COMMENT '配置键（唯一标识）',
        config_value TEXT COMMENT '配置值（JSON格式字符串）',
        config_type VARCHAR(16) NOT NULL DEFAULT 'string' COMMENT '配置类型: string-字符串, json-JSON对象, array-数组',
        description VARCHAR(256) COMMENT '配置说明',
        is_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX ix_home_configs_config_key (config_key),
        INDEX ix_home_configs_is_enabled (is_enabled)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='首页配置表';
    """
    
    await session.execute(text(create_table_sql))
    await session.commit()
    logger.info("Home configs table created successfully")


async def init_default_configs(session: AsyncSession) -> None:
    """初始化默认配置项"""
    logger.info("Initializing default home configs...")
    
    default_configs = [
        {
            "config_key": "home_title",
            "config_value": "欢迎使用",
            "config_type": "string",
            "description": "首页标题",
        },
        {
            "config_key": "home_subtitle",
            "config_value": "让AI为您服务",
            "config_type": "string",
            "description": "首页副标题",
        },
        {
            "config_key": "home_background",
            "config_value": "",
            "config_type": "string",
            "description": "首页背景图URL",
        },
        {
            "config_key": "featured_modules",
            "config_value": "[]",
            "config_type": "array",
            "description": "推荐模块列表",
        },
        {
            "config_key": "quick_links",
            "config_value": "[]",
            "config_type": "array",
            "description": "快捷链接列表",
        },
    ]
    
    insert_sql = """
    INSERT INTO home_configs (config_key, config_value, config_type, description, is_enabled)
    VALUES (:config_key, :config_value, :config_type, :description, TRUE)
    ON DUPLICATE KEY UPDATE
        config_value = VALUES(config_value),
        config_type = VALUES(config_type),
        description = VALUES(description)
    """
    
    for config in default_configs:
        await session.execute(text(insert_sql), config)
    
    await session.commit()
    logger.info(f"Initialized {len(default_configs)} default configs")


async def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("Creating miniprogram management tables...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        await init_db()
        logger.info("Database connection initialized")
        
        # 重新导入 async_session_maker（在 init_db() 之后）
        from app.db.session import async_session_maker
        if async_session_maker is None:
            raise RuntimeError("async_session_maker 未初始化")
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 创建表
                await create_banners_table(session)
                await create_home_configs_table(session)
                
                # 初始化默认配置
                await init_default_configs(session)
                
                logger.info("=" * 60)
                logger.info("All tables created successfully!")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"Error creating tables: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # 关闭数据库连接
        await close_db()
        logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())

