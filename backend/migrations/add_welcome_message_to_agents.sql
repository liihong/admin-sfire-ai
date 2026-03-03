-- 为 agents 表添加 welcome_message 字段
-- 执行方式: mysql -u用户名 -p 数据库名 < add_welcome_message_to_agents.sql
-- 或在 MySQL 客户端中执行以下 SQL

ALTER TABLE agents ADD COLUMN welcome_message TEXT NULL COMMENT '欢迎语（用户进入对话时展示）' AFTER description;
