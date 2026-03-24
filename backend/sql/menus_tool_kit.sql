-- =============================================================================
-- 便捷工具包：菜单初始化（MySQL / utf8mb4）
-- 依赖表：menus（字段与 models/menu.py 一致）
-- 可重复执行：已存在同名 name 时不会重复插入
-- =============================================================================

-- 若「系统管理」仍为 sort_order=6，建议与 init_db 一致改为 7（可选，避免与便捷工具包同级排序冲突）
-- UPDATE `menus` SET `sort_order` = 7 WHERE `name` = 'system' AND `sort_order` = 6;

-- 1) 父级：便捷工具包
INSERT INTO `menus` (
  `parent_id`, `name`, `path`, `component`, `redirect`,
  `sort_order`, `icon`, `title`, `is_link`,
  `is_hide`, `is_full`, `is_affix`, `is_keep_alive`,
  `active_menu`, `perms`, `required_level`, `required_compute_power`, `consume_compute_power`,
  `is_enabled`, `created_at`, `updated_at`
)
SELECT
  NULL,
  'toolKit',
  '/tool-kit',
  NULL,
  '/tool-kit/list',
  6,
  'Box',
  '便捷工具包',
  '',
  0, 0, 0, 1,
  NULL, NULL, NULL, NULL, NULL,
  1,
  NOW(),
  NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `menus` WHERE `name` = 'toolKit');

-- 2) 子菜单（依赖父级 id）
SET @tool_kit_parent_id := (SELECT `id` FROM `menus` WHERE `name` = 'toolKit' LIMIT 1);

INSERT INTO `menus` (
  `parent_id`, `name`, `path`, `component`, `redirect`,
  `sort_order`, `icon`, `title`, `is_link`,
  `is_hide`, `is_full`, `is_affix`, `is_keep_alive`,
  `active_menu`, `perms`, `required_level`, `required_compute_power`, `consume_compute_power`,
  `is_enabled`, `created_at`, `updated_at`
)
SELECT @tool_kit_parent_id, 'toolKitList', '/tool-kit/list', '/tool-kit/list/index', NULL,
  1, 'Grid', '工具包列表', '',
  0, 0, 0, 1,
  NULL, NULL, NULL, NULL, NULL,
  1, NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `menus` WHERE `name` = 'toolKitList');

INSERT INTO `menus` (
  `parent_id`, `name`, `path`, `component`, `redirect`,
  `sort_order`, `icon`, `title`, `is_link`,
  `is_hide`, `is_full`, `is_affix`, `is_keep_alive`,
  `active_menu`, `perms`, `required_level`, `required_compute_power`, `consume_compute_power`,
  `is_enabled`, `created_at`, `updated_at`
)
SELECT @tool_kit_parent_id, 'toolKitManage', '/tool-kit/manage', '/tool-kit/manage/index', NULL,
  2, 'Setting', '工具包管理', '',
  0, 0, 0, 1,
  NULL, NULL, NULL, NULL, NULL,
  1, NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `menus` WHERE `name` = 'toolKitManage');

INSERT INTO `menus` (
  `parent_id`, `name`, `path`, `component`, `redirect`,
  `sort_order`, `icon`, `title`, `is_link`,
  `is_hide`, `is_full`, `is_affix`, `is_keep_alive`,
  `active_menu`, `perms`, `required_level`, `required_compute_power`, `consume_compute_power`,
  `is_enabled`, `created_at`, `updated_at`
)
SELECT @tool_kit_parent_id, 'toolKitRun', '/tool-kit/tool/:code', '/tool-kit/run/index', NULL,
  99, 'Menu', '使用工具', '',
  1, 0, 0, 1,
  '/tool-kit/list', NULL, NULL, NULL, NULL,
  1, NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `menus` WHERE `name` = 'toolKitRun');
