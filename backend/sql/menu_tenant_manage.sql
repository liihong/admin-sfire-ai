-- =============================================================================
-- 菜单：租户管理（挂载在「系统管理」system 下）
-- MySQL 8 / utf8mb4
-- 执行前请确认 menus 表中存在 name = 'system' 的父级菜单
-- =============================================================================

SET @system_parent_id := (SELECT `id` FROM `menus` WHERE `name` = 'system' LIMIT 1);

INSERT INTO `menus` (
  `parent_id`, `name`, `path`, `component`, `redirect`,
  `sort_order`, `icon`, `title`, `is_link`,
  `is_hide`, `is_full`, `is_affix`, `is_keep_alive`,
  `active_menu`, `perms`, `required_level`, `required_compute_power`, `consume_compute_power`,
  `is_enabled`, `created_at`, `updated_at`
)
SELECT
  @system_parent_id,
  'tenantManage',
  '/system/tenantManage',
  '/system/tenantManage/index',
  NULL,
  11,
  'OfficeBuilding',
  '租户管理',
  '',
  0, 0, 0, 1,
  NULL, NULL, NULL, NULL, NULL,
  1,
  NOW(),
  NOW()
FROM DUAL
WHERE @system_parent_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `name` = 'tenantManage');
