-- 便捷工具包表（MySQL 8+ / utf8mb4）
-- 执行前请确认库名，或去掉 USE 语句

CREATE TABLE IF NOT EXISTS `tool_packages` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code` VARCHAR(64) NOT NULL COMMENT '唯一标识（路由片段，如 voice-clone）',
  `name` VARCHAR(128) NOT NULL COMMENT '展示名称',
  `description` TEXT NULL COMMENT '描述',
  `icon` VARCHAR(64) NOT NULL DEFAULT 'Box' COMMENT 'Element Plus 图标名',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序（越小越靠前）',
  `status` SMALLINT NOT NULL DEFAULT 1 COMMENT '0-禁用 1-启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tool_packages_code` (`code`),
  KEY `ix_tool_packages_status_sort` (`status`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='便捷工具包配置表';

-- 基础数据：声音复刻（若已存在则跳过）
INSERT INTO `tool_packages` (`code`, `name`, `description`, `icon`, `sort_order`, `status`)
SELECT 'voice-clone', '声音复刻', '上传音频训练专属音色，支持文本转语音', 'Microphone', 0, 1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `tool_packages` WHERE `code` = 'voice-clone');

INSERT INTO `tool_packages` (`code`, `name`, `description`, `icon`, `sort_order`, `status`)
SELECT 'douyin-caption', '抖音文案提取', '粘贴抖音链接，提取视频口播文案（TikHub 解析 + 火山语音识别）', 'Document', 1, 1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `tool_packages` WHERE `code` = 'douyin-caption');
