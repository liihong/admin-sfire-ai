"""
数据库迁移：创建 dingma_product_knowledge 表

执行方式：
    cd backend && python -m db.migrations.add_dingma_product_knowledge
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from loguru import logger

from db.session import init_db, close_db


async def upgrade():
    """创建 dingma_product_knowledge 表"""
    from db.session import engine

    if engine is None:
        raise RuntimeError("Database not initialized")

    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'dingma_product_knowledge'
            """)
        )
        if result.scalar() > 0:
            logger.info("dingma_product_knowledge 表已存在，跳过迁移")
            return

        logger.info("正在创建 dingma_product_knowledge 表...")
        await conn.execute(
            text("""
                CREATE TABLE dingma_product_knowledge (
                    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                    tenant_id BIGINT NOT NULL COMMENT '租户ID（dingma）',
                    category_code VARCHAR(32) NOT NULL COMMENT '品类编码',
                    category_name VARCHAR(64) NOT NULL COMMENT '品类名称',
                    product_code VARCHAR(64) NOT NULL COMMENT '产品稳定编码',
                    product_name VARCHAR(128) NOT NULL COMMENT '产品名称',
                    aliases JSON NULL COMMENT '别名列表',
                    pack_formula TEXT NULL COMMENT '出货配比',
                    recipe_detail JSON NULL COMMENT '制作详情',
                    copywriting_facts TEXT NULL COMMENT '文案事实',
                    source_version VARCHAR(32) NULL COMMENT '课件版本',
                    status INT NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
                    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_dpk_tenant_product_code (tenant_id, product_code),
                    KEY ix_dpk_tenant_id (tenant_id),
                    KEY ix_dpk_category_code (category_code),
                    KEY ix_dpk_status (status),
                    CONSTRAINT fk_dpk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='顶妈产品知识库'
            """)
        )
        logger.info("迁移完成：dingma_product_knowledge 表已创建")


async def main():
    await init_db()
    try:
        await upgrade()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
