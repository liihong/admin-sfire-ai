-- 为 roles 表增加菜单权限字段（与 models.role.Role.menu_ids 对应）
-- 若库已由新 ORM 建表且含 menu_ids，可跳过
-- 执行: mysql -h主机 -u用户 -p 数据库名 < add_roles_menu_ids.sql

ALTER TABLE `roles`
ADD COLUMN `menu_ids` JSON NULL COMMENT '可访问的菜单ID列表（JSON数组）' AFTER `sort_order`;
