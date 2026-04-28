-- =============================================================================
-- 多租户改造：一次性执行前请先备份全库（mysqldump / 快照）
-- 适用：MySQL 8.x，InnoDB，utf8mb4
-- 说明：主租户固定 id=1；存量数据全部 tenant_id=1
-- 若某步报「外键/索引名不存在」，用下方「附录」查询实际名称后改语句再执行
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- 1. 租户主表
-- =============================================================================
CREATE TABLE IF NOT EXISTS `tenants` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(64) NOT NULL COMMENT '租户代码',
  `name` VARCHAR(128) NOT NULL COMMENT '租户名称',
  `is_default` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否主租户',
  `remark` TEXT NULL COMMENT '备注',
  `wechat_app_id` VARCHAR(64) NULL COMMENT '绑定的微信小程序 AppID',
  `created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_tenants_code` (`code`),
  KEY `ix_tenants_is_default` (`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户表';

INSERT INTO `tenants` (`id`, `code`, `name`, `is_default`, `remark`, `wechat_app_id`, `created_at`, `updated_at`)
VALUES (1, 'default', '主租户', 1, '迁移默认主租户', NULL, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `is_default` = VALUES(`is_default`),
  `updated_at` = NOW();

-- =============================================================================
-- 2. users 表上原指向 user_levels.code 的外键必须先删除（名称因库而异，用动态 SQL）
-- =============================================================================
SET @fk_users_level := (
  SELECT `CONSTRAINT_NAME` FROM `information_schema`.`KEY_COLUMN_USAGE`
  WHERE `TABLE_SCHEMA` = DATABASE()
    AND `TABLE_NAME` = 'users'
    AND `REFERENCED_TABLE_NAME` = 'user_levels'
    AND `COLUMN_NAME` = 'level_code'
  LIMIT 1
);
SET @sql_drop_ul := IF(
  @fk_users_level IS NOT NULL,
  CONCAT('ALTER TABLE `users` DROP FOREIGN KEY `', @fk_users_level, '`'),
  'SELECT 1 AS `skip_users_fk_ul`'
);
PREPARE `stmt_ul` FROM @sql_drop_ul;
EXECUTE `stmt_ul`;
DEALLOCATE PREPARE `stmt_ul`;

-- =============================================================================
-- 3. user_levels：增加 tenant_id，唯一约束由 code 改为 (tenant_id, code)
-- =============================================================================

-- 3.1 删除 user_levels 上仅在 code 列的唯一索引（常见名 ix_user_levels_code 或 code）
SET @uq_ul_code := (
  SELECT `INDEX_NAME` FROM `information_schema`.`STATISTICS`
  WHERE `TABLE_SCHEMA` = DATABASE()
    AND `TABLE_NAME` = 'user_levels'
    AND `COLUMN_NAME` = 'code'
    AND `NON_UNIQUE` = 0
    AND `SEQ_IN_INDEX` = 1
  ORDER BY CARDINALITY
  LIMIT 1
);

SET @sql_drop_uq_ul := IF(
  @uq_ul_code IS NOT NULL AND @uq_ul_code != 'PRIMARY',
  CONCAT('ALTER TABLE `user_levels` DROP INDEX `', @uq_ul_code, '`'),
  'SELECT 1 AS `skip_drop_ul_unique`'
);
PREPARE s_uq FROM @sql_drop_uq_ul;
EXECUTE s_uq;
DEALLOCATE PREPARE s_uq;

-- 3.2 增加 tenant_id（若列已存在会报错——说明已迁移过一节，请注释本段）
ALTER TABLE `user_levels`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `user_levels` SET `tenant_id` = 1;

ALTER TABLE `user_levels`
  ADD UNIQUE KEY `ix_user_levels_tenant_code` (`tenant_id`, `code`),
  ADD KEY `ix_user_levels_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_user_levels_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- =============================================================================
-- 4. users：增加 tenant_id + 外键 + 与 user_levels 的联合外键
-- =============================================================================
ALTER TABLE `users`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `users` SET `tenant_id` = 1;

ALTER TABLE `users`
  ADD KEY `ix_users_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_users_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT,
  ADD CONSTRAINT `fk_users_tenant_level_code` FOREIGN KEY (`tenant_id`, `level_code`)
    REFERENCES `user_levels` (`tenant_id`, `code`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- =============================================================================
-- 5. admin_users：tenant_id 允许 NULL（平台超级管理员）
-- =============================================================================
ALTER TABLE `admin_users`
  ADD COLUMN `tenant_id` BIGINT NULL COMMENT '租户ID；NULL 表示平台超级管理员' AFTER `id`;

UPDATE `admin_users` SET `tenant_id` = 1;

-- 平台超级管理员需 tenant_id 为 NULL；请按实际账号改条件后执行，例如：
-- UPDATE `admin_users` SET `tenant_id` = NULL WHERE `username` = '你的超管账号';

ALTER TABLE `admin_users`
  ADD KEY `ix_admin_users_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_admin_users_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- =============================================================================
-- 6. 需调整唯一约束的表（去掉单列唯一 → 租户+字段联合唯一）
-- =============================================================================

-- 6.1 home_configs：原 UNIQUE(config_key)
ALTER TABLE `home_configs` DROP INDEX `ix_home_configs_config_key`;

ALTER TABLE `home_configs`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `home_configs` SET `tenant_id` = 1;

ALTER TABLE `home_configs`
  ADD UNIQUE KEY `ix_home_configs_tenant_config` (`tenant_id`, `config_key`),
  ADD KEY `ix_home_configs_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_home_configs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- 6.2 quick_entries：原 UNIQUE(unique_key)
ALTER TABLE `quick_entries` DROP INDEX `ix_quick_entries_unique_key`;

ALTER TABLE `quick_entries`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `quick_entries` SET `tenant_id` = 1;

ALTER TABLE `quick_entries`
  ADD UNIQUE KEY `ix_quick_entries_tenant_unique_key` (`tenant_id`, `unique_key`),
  ADD KEY `ix_quick_entries_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_quick_entries_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- 6.3 tool_packages：原 UNIQUE(code)，与 backend/sql/tool_packages.sql 中 uk_tool_packages_code 一致
ALTER TABLE `tool_packages` DROP INDEX `uk_tool_packages_code`;

ALTER TABLE `tool_packages`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `tool_packages` SET `tenant_id` = 1;

ALTER TABLE `tool_packages`
  ADD UNIQUE KEY `uq_tool_packages_tenant_code` (`tenant_id`, `code`),
  ADD KEY `ix_tool_packages_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_tool_packages_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- 6.4 sys_dict：原 UNIQUE(dict_code)
ALTER TABLE `sys_dict` DROP INDEX `ix_sys_dict_code`;

ALTER TABLE `sys_dict`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `sys_dict` SET `tenant_id` = 1;

ALTER TABLE `sys_dict`
  ADD UNIQUE KEY `ix_sys_dict_tenant_code` (`tenant_id`, `dict_code`),
  ADD KEY `ix_sys_dict_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_sys_dict_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- =============================================================================
-- 7. user_voice_speakers：唯一约束改为 (tenant_id, owner_type, owner_id)
-- =============================================================================
ALTER TABLE `user_voice_speakers` DROP INDEX `uq_user_voice_speaker_owner`;

ALTER TABLE `user_voice_speakers`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;

UPDATE `user_voice_speakers` SET `tenant_id` = 1;

ALTER TABLE `user_voice_speakers`
  ADD UNIQUE KEY `uq_user_voice_speaker_tenant_owner` (`tenant_id`, `owner_type`, `owner_id`),
  ADD KEY `ix_user_voice_speakers_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_user_voice_speakers_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- =============================================================================
-- 8. 其余业务表：仅增加 tenant_id + 索引 + FK（无单列唯一改写）
-- 若列已存在会报错，请先检查 SHOW COLUMNS FROM `表名`;
-- =============================================================================

-- agents
ALTER TABLE `agents`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `agents` SET `tenant_id` = 1;
ALTER TABLE `agents`
  ADD KEY `ix_agents_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_agents_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- projects
ALTER TABLE `projects`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `projects` SET `tenant_id` = 1;
ALTER TABLE `projects`
  ADD KEY `ix_projects_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_projects_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- conversations
ALTER TABLE `conversations`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `conversations` SET `tenant_id` = 1;
ALTER TABLE `conversations`
  ADD KEY `ix_conversations_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_conversations_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- compute_logs
ALTER TABLE `compute_logs`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `compute_logs` SET `tenant_id` = 1;
ALTER TABLE `compute_logs`
  ADD KEY `ix_compute_logs_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_compute_logs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- articles
ALTER TABLE `articles`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `articles` SET `tenant_id` = 1;
ALTER TABLE `articles`
  ADD KEY `ix_articles_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_articles_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- banners
ALTER TABLE `banners`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `banners` SET `tenant_id` = 1;
ALTER TABLE `banners`
  ADD KEY `ix_banners_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_banners_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- inspirations
ALTER TABLE `inspirations`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `inspirations` SET `tenant_id` = 1;
ALTER TABLE `inspirations`
  ADD KEY `ix_inspirations_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_inspirations_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- recharge_packages
ALTER TABLE `recharge_packages`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `recharge_packages` SET `tenant_id` = 1;
ALTER TABLE `recharge_packages`
  ADD KEY `ix_recharge_packages_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_recharge_packages_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- tickets
ALTER TABLE `tickets`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `tickets` SET `tenant_id` = 1;
ALTER TABLE `tickets`
  ADD KEY `ix_tickets_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_tickets_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- copywriting_library_entries
ALTER TABLE `copywriting_library_entries`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `copywriting_library_entries` SET `tenant_id` = 1;
ALTER TABLE `copywriting_library_entries`
  ADD KEY `ix_cle_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_cle_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- llm_models
ALTER TABLE `llm_models`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `llm_models` SET `tenant_id` = 1;
ALTER TABLE `llm_models`
  ADD KEY `ix_llm_models_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_llm_models_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- skill_library
ALTER TABLE `skill_library`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `skill_library` SET `tenant_id` = 1;
ALTER TABLE `skill_library`
  ADD KEY `ix_skill_library_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_skill_library_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- project_benchmark_accounts
ALTER TABLE `project_benchmark_accounts`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `project_benchmark_accounts` SET `tenant_id` = 1;
ALTER TABLE `project_benchmark_accounts`
  ADD KEY `ix_pba_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_pba_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- project_benchmark_videos
ALTER TABLE `project_benchmark_videos`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `project_benchmark_videos` SET `tenant_id` = 1;
ALTER TABLE `project_benchmark_videos`
  ADD KEY `ix_pbv_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_pbv_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- compute_freeze_logs
ALTER TABLE `compute_freeze_logs`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `compute_freeze_logs` SET `tenant_id` = 1;
ALTER TABLE `compute_freeze_logs`
  ADD KEY `ix_compute_freeze_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_compute_freeze_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- admin_operation_logs
ALTER TABLE `admin_operation_logs`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `admin_operation_logs` SET `tenant_id` = 1;
ALTER TABLE `admin_operation_logs`
  ADD KEY `ix_admin_operation_logs_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_admin_operation_logs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

-- admin_debug_logs
ALTER TABLE `admin_debug_logs`
  ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID' AFTER `id`;
UPDATE `admin_debug_logs` SET `tenant_id` = 1;
ALTER TABLE `admin_debug_logs`
  ADD KEY `ix_admin_debug_logs_tenant_id` (`tenant_id`),
  ADD CONSTRAINT `fk_admin_debug_logs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE RESTRICT;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 附录：若某索引名与线上一致，可自检
-- =============================================================================
-- SHOW CREATE TABLE `users`\G
-- SHOW CREATE TABLE `user_levels`\G
-- SELECT * FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='users';
-- SHOW INDEX FROM `tool_packages`;
