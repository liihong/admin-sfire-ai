-- 文案库：创建 copywriting_library_entries 表
-- 说明：按 user_id + project_id（IP）隔离，支持 tags、状态流转、发布后数据补录
-- 注意：请在测试库先验证；生产环境建议使用标准迁移流程执行

CREATE TABLE IF NOT EXISTS `copywriting_library_entries` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `project_id` BIGINT NOT NULL COMMENT '项目/IP ID',

  `content` LONGTEXT NOT NULL COMMENT '文案正文',
  `tags` JSON NULL COMMENT '标签数组（JSON格式，如 ["种草","开场"]）',
  `status` VARCHAR(20) NOT NULL DEFAULT 'todo' COMMENT '状态：draft/todo/published/archived',

  `views` INT NULL COMMENT '播放/曝光量（可选）',
  `likes` INT NULL COMMENT '点赞数（可选）',
  `comments` INT NULL COMMENT '评论数（可选）',
  `shares` INT NULL COMMENT '转发/分享数（可选）',
  `published_at` DATETIME NULL COMMENT '发布时间（可选）',

  PRIMARY KEY (`id`),
  KEY `ix_cle_user_id` (`user_id`),
  KEY `ix_cle_project_id` (`project_id`),
  KEY `ix_cle_user_project` (`user_id`, `project_id`),
  KEY `ix_cle_status` (`status`),
  KEY `ix_cle_created_at` (`created_at`),
  CONSTRAINT `fk_cle_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cle_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文案库条目表（按用户+项目隔离）';

