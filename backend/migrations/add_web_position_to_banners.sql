-- 为 banners 表的 position 字段添加 web 位置选项
-- 执行方式: mysql -u用户名 -p 数据库名 < add_web_position_to_banners.sql
-- 或在 MySQL 客户端中执行以下 SQL

ALTER TABLE banners MODIFY COLUMN position ENUM('home_top', 'home_middle', 'home_bottom', 'web') NOT NULL DEFAULT 'home_top' COMMENT 'Banner位置: home_top-首页顶部, home_middle-首页中部, home_bottom-首页底部, web-web端';
