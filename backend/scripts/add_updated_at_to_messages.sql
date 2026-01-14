-- 为 conversation_messages 表添加 updated_at 字段
ALTER TABLE `conversation_messages` 
ADD COLUMN `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' 
AFTER `created_at`;

-- 为 conversation_chunks 表添加 updated_at 字段
ALTER TABLE `conversation_chunks` 
ADD COLUMN `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' 
AFTER `created_at`;














