-- 已有库升级：在 roles 表增加菜单权限字段（新库由 ORM 建表时已包含，可跳过）
-- MySQL 5.7+

ALTER TABLE `roles`
ADD COLUMN `menu_ids` JSON NULL COMMENT '可访问的菜单ID列表（JSON数组）' AFTER `sort_order`;
