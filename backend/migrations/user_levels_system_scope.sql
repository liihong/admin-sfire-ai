-- 用户等级改为全租户共用系统配置（存储于 tenant_id = 1）
-- 执行前请备份数据库；若外键名不同，先用 SHOW CREATE TABLE users 确认

-- 1. 删除 users 上 (tenant_id, level_code) 联合外键（允许各租户用户引用系统等级 code）
SET @fk_name := (
  SELECT CONSTRAINT_NAME
  FROM information_schema.KEY_COLUMN_USAGE
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'users'
    AND REFERENCED_TABLE_NAME = 'user_levels'
  LIMIT 1
);
SET @drop_fk := IF(
  @fk_name IS NOT NULL,
  CONCAT('ALTER TABLE `users` DROP FOREIGN KEY `', @fk_name, '`'),
  'SELECT 1'
);
PREPARE stmt FROM @drop_fk;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.（可选）清理历史按租户复制的等级配置，仅保留系统级
-- DELETE FROM `user_levels` WHERE `tenant_id` <> 1;
