-- 多租户第一阶段：主租户 id=1，全表 tenant_id 回填为 1
-- 执行前请备份数据库；在 MySQL 8+ 测试。若外键/索引名与线上一致，请先核对 information_schema。

-- 1) 租户表
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
  UNIQUE KEY `uq_tenants_code` (`code`),
  KEY `ix_tenants_is_default` (`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户表';

INSERT INTO `tenants` (`id`,`code`,`name`,`is_default`,`remark`,`wechat_app_id`)
VALUES (1,'default','主租户',1,'迁移默认主租户（与主小程序数据一致）', NULL)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`), `is_default`=VALUES(`is_default`);

-- 2) 以下为各业务表增加 tenant_id 的模板（实际列顺序/是否已存在请按 show create table 调整后执行）：
-- ALTER TABLE `users` ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 AFTER `id`;
-- UPDATE `users` SET `tenant_id` = 1;
-- ALTER TABLE `users` ADD CONSTRAINT `fk_users_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`);

-- 3) user_levels：由单列 code 唯一改为 (tenant_id,code) 唯一 —— 需先处理 users 上引用 user_levels.code 的外键
-- 以 information_schema 查出 users 表上引用 level_code 的约束名后执行 DROP FOREIGN KEY `...`;
-- ALTER TABLE `user_levels` ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1;
-- UPDATE `user_levels` SET `tenant_id` = 1;
-- DROP INDEX `ix_user_levels_code` ON `user_levels`;  -- 名称以实际为准
-- ALTER TABLE `user_levels` ADD UNIQUE KEY `ix_user_levels_tenant_code` (`tenant_id`,`code`);
-- ALTER TABLE `user_levels` ADD CONSTRAINT `fk_ul_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`);

-- 4) users：增加 tenant_id；增加 (tenant_id,level_code) 联合外键到 user_levels —— 请先删原单列 FK
-- ALTER TABLE `users` DROP FOREIGN KEY `<fk_users_level_code>`;
-- ALTER TABLE `users` ADD COLUMN `tenant_id` BIGINT NOT NULL DEFAULT 1 AFTER `id`;
-- UPDATE `users` SET `tenant_id` = 1;
-- ALTER TABLE `users` ADD CONSTRAINT `fk_users_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`);
-- ALTER TABLE `users` ADD CONSTRAINT `fk_users_tenant_level_code` FOREIGN KEY (`tenant_id`,`level_code`)
--   REFERENCES `user_levels`(`tenant_id`,`code`);

-- 5) admin_users.tenant_id 允许 NULL（平台超级管理员）；迁移后请将业务管理员回填为 1：
-- ALTER TABLE `admin_users` ADD COLUMN `tenant_id` BIGINT NULL AFTER `id`;
-- UPDATE `admin_users` SET `tenant_id` = 1 WHERE `tenant_id` IS NULL AND id > 0;
-- ALTER TABLE `admin_users` ADD CONSTRAINT `fk_au_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`);

-- 6) sys_dict：dict_code 唯一改为 (tenant_id, dict_code)
-- 7) home_configs / quick_entries / tool_packages：同上类复合唯一索引调整

-- 请将上述 DDL 结合实际表结构与约束名在线下环境完整跑通后再上生产。

