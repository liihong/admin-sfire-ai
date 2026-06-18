"""
数据库迁移：重建顶妈知识库 v2（3 表结构）

- 删除旧表 dingma_product_knowledge
- 创建 dingma_knowledge_component / dingma_knowledge_sku / dingma_sku_component_link

执行方式：
    cd backend && python -m db.migrations.rebuild_dingma_knowledge_v2
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from loguru import logger

from db.session import init_db, close_db


async def upgrade():
    """重建知识库表结构"""
    from db.session import engine

    if engine is None:
        raise RuntimeError("Database not initialized")

    async with engine.begin() as conn:
        logger.info("删除旧表 dingma_product_knowledge（若存在）...")
        await conn.execute(text("DROP TABLE IF EXISTS dingma_product_knowledge"))

        logger.info("删除 v2 表（若存在，便于重复执行）...")
        await conn.execute(text("DROP TABLE IF EXISTS dingma_sku_component_link"))
        await conn.execute(text("DROP TABLE IF EXISTS dingma_knowledge_sku"))
        await conn.execute(text("DROP TABLE IF EXISTS dingma_knowledge_component"))

        logger.info("创建 dingma_knowledge_component ...")
        await conn.execute(
            text("""
                CREATE TABLE dingma_knowledge_component (
                    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                    tenant_id BIGINT NOT NULL COMMENT '租户ID',
                    component_code VARCHAR(64) NOT NULL COMMENT '组件编码',
                    component_name VARCHAR(128) NOT NULL COMMENT '组件名称',
                    component_type VARCHAR(32) NOT NULL DEFAULT 'sauce' COMMENT '组件类型',
                    aliases JSON NULL COMMENT '别名',
                    pack_formula TEXT NULL COMMENT '出货/用法说明',
                    recipe_detail JSON NULL COMMENT '全量配方',
                    guardrail JSON NULL COMMENT '文案护栏',
                    process_copywriting JSON NULL COMMENT '过程文案',
                    source_version VARCHAR(32) NULL COMMENT '课件版本',
                    status INT NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
                    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_dkc_tenant_code (tenant_id, component_code),
                    KEY ix_dkc_tenant_id (tenant_id),
                    KEY ix_dkc_component_type (component_type),
                    KEY ix_dkc_status (status),
                    CONSTRAINT fk_dkc_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='顶妈知识库-组件'
            """)
        )

        logger.info("创建 dingma_knowledge_sku ...")
        await conn.execute(
            text("""
                CREATE TABLE dingma_knowledge_sku (
                    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                    tenant_id BIGINT NOT NULL COMMENT '租户ID',
                    sku_code VARCHAR(64) NOT NULL COMMENT 'SKU编码',
                    sku_name VARCHAR(128) NOT NULL COMMENT 'SKU名称',
                    category_code VARCHAR(32) NOT NULL COMMENT '品类编码',
                    category_name VARCHAR(64) NOT NULL COMMENT '品类名称',
                    aliases JSON NULL COMMENT '别名',
                    pack_formula TEXT NULL COMMENT '出货配比',
                    guardrail JSON NULL COMMENT '文案护栏',
                    process_copywriting JSON NULL COMMENT 'SKU级过程文案',
                    source_version VARCHAR(32) NULL COMMENT '课件版本',
                    status INT NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
                    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_dks_tenant_code (tenant_id, sku_code),
                    KEY ix_dks_tenant_id (tenant_id),
                    KEY ix_dks_category_code (category_code),
                    KEY ix_dks_status (status),
                    CONSTRAINT fk_dks_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='顶妈知识库-成品SKU'
            """)
        )

        logger.info("创建 dingma_sku_component_link ...")
        await conn.execute(
            text("""
                CREATE TABLE dingma_sku_component_link (
                    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                    sku_id BIGINT NOT NULL COMMENT 'SKU ID',
                    component_id BIGINT NOT NULL COMMENT '组件 ID',
                    role VARCHAR(32) NOT NULL DEFAULT 'other' COMMENT '关联角色',
                    process_focus TINYINT(1) NOT NULL DEFAULT 0 COMMENT '过程场景焦点',
                    display_label VARCHAR(64) NULL COMMENT '展示名',
                    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_dscl_sku_component (sku_id, component_id),
                    KEY ix_dscl_sku_id (sku_id),
                    KEY ix_dscl_component_id (component_id),
                    CONSTRAINT fk_dscl_sku FOREIGN KEY (sku_id) REFERENCES dingma_knowledge_sku(id) ON DELETE CASCADE,
                    CONSTRAINT fk_dscl_component FOREIGN KEY (component_id) REFERENCES dingma_knowledge_component(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='顶妈知识库-SKU组件关联'
            """)
        )

        logger.info("迁移完成：顶妈知识库 v2 三表已就绪")


async def main():
    await init_db()
    try:
        await upgrade()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
