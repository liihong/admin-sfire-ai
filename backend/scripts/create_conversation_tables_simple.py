"""
创建对话相关的数据库表（简化版）
直接使用环境变量，避免复杂的导入
"""
import asyncio
import os
from pathlib import Path
import aiomysql

from loguru import logger

# SQL 语句
SQL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS `conversations` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `user_id` BIGINT NOT NULL COMMENT '用户ID',
      `agent_id` BIGINT NULL COMMENT '智能体ID（可选）',
      `project_id` BIGINT NULL COMMENT '项目ID（可选）',
      `title` VARCHAR(256) NOT NULL DEFAULT '新对话' COMMENT '会话标题',
      `model_type` VARCHAR(64) NOT NULL DEFAULT 'deepseek' COMMENT '使用的模型类型',
      `total_tokens` INT NOT NULL DEFAULT 0 COMMENT '总token数',
      `message_count` INT NOT NULL DEFAULT 0 COMMENT '消息数量',
      `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (`id`),
      INDEX `ix_conversations_user_id` (`user_id`),
      INDEX `ix_conversations_agent_id` (`agent_id`),
      INDEX `ix_conversations_project_id` (`project_id`),
      INDEX `ix_conversations_status` (`status`),
      INDEX `ix_conversations_created_at` (`created_at`),
      CONSTRAINT `fk_conversations_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
      CONSTRAINT `fk_conversations_agent_id` FOREIGN KEY (`agent_id`) REFERENCES `agents` (`id`) ON DELETE SET NULL,
      CONSTRAINT `fk_conversations_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表'
    """,
    """
    CREATE TABLE IF NOT EXISTS `conversation_messages` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `conversation_id` BIGINT NOT NULL COMMENT '会话ID',
      `role` VARCHAR(20) NOT NULL COMMENT '角色',
      `content` TEXT NOT NULL COMMENT '消息内容',
      `tokens` INT NOT NULL DEFAULT 0 COMMENT 'token数',
      `sequence` INT NOT NULL COMMENT '消息序号',
      `embedding_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '向量化状态',
      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      PRIMARY KEY (`id`),
      INDEX `ix_conversation_messages_conversation_id` (`conversation_id`),
      INDEX `ix_conversation_messages_sequence` (`conversation_id`, `sequence`),
      INDEX `ix_conversation_messages_embedding_status` (`embedding_status`),
      CONSTRAINT `fk_conversation_messages_conversation_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表'
    """,
    """
    CREATE TABLE IF NOT EXISTS `conversation_chunks` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `conversation_id` BIGINT NOT NULL COMMENT '会话ID',
      `user_message_id` BIGINT NOT NULL COMMENT '用户消息ID',
      `assistant_message_id` BIGINT NOT NULL COMMENT 'AI回复消息ID',
      `chunk_text` TEXT NOT NULL COMMENT '片段文本',
      `vector_id` VARCHAR(128) NULL COMMENT '向量数据库中的ID',
      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      PRIMARY KEY (`id`),
      INDEX `ix_conversation_chunks_conversation_id` (`conversation_id`),
      INDEX `ix_conversation_chunks_vector_id` (`vector_id`),
      CONSTRAINT `fk_conversation_chunks_conversation_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE,
      CONSTRAINT `fk_conversation_chunks_user_message_id` FOREIGN KEY (`user_message_id`) REFERENCES `conversation_messages` (`id`) ON DELETE CASCADE,
      CONSTRAINT `fk_conversation_chunks_assistant_message_id` FOREIGN KEY (`assistant_message_id`) REFERENCES `conversation_messages` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话片段表'
    """
]


async def main():
    """创建对话相关的数据库表"""
    # 从环境变量读取配置，如果没有则使用默认值
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "Sfire@2026")
    mysql_database = os.getenv("MYSQL_DATABASE", "sfire_admin")
    
    logger.info("=" * 60)
    logger.info("开始创建对话相关的数据库表...")
    logger.info(f"数据库: {mysql_host}:{mysql_port}/{mysql_database}")
    logger.info("=" * 60)
    
    try:
        # 连接到数据库
        conn = await aiomysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            db=mysql_database,
            charset="utf8mb4",
        )
        
        cursor = await conn.cursor()
        
        try:
            # 执行每个 SQL 语句
            for i, sql in enumerate(SQL_STATEMENTS, 1):
                logger.info(f"创建表 {i}/3...")
                await cursor.execute(sql)
                await conn.commit()
                logger.info(f"✓ 表 {i} 创建成功")
            
            logger.info("=" * 60)
            logger.info("所有数据库表创建完成！")
            logger.info("=" * 60)
            
        except Exception as e:
            await conn.rollback()
            logger.error(f"创建表失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())












