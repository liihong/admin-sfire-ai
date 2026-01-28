-- 添加公告类型到文章表
-- 如果文章表已创建，执行此脚本添加公告类型
-- 执行前请备份数据库

-- ============================================
-- 修改文章表，添加公告类型
-- ============================================
-- 注意：如果表已存在且有数据，需要先修改ENUM类型

-- 方法1：如果表还没有数据或可以接受短暂锁表
ALTER TABLE `articles` 
MODIFY COLUMN `category` ENUM('founder_story', 'operation_article', 'customer_case', 'announcement') 
NOT NULL 
COMMENT '文章类型: founder_story-创始人故事, operation_article-运营干货, customer_case-客户案例, announcement-公告';

-- ============================================
-- 验证修改结果
-- ============================================
-- 查询表结构
DESCRIBE `articles`;

-- 查询category字段的ENUM值
SHOW COLUMNS FROM `articles` WHERE Field = 'category';

-- ============================================
-- 执行完成
-- ============================================
-- 文章表已成功添加公告类型
-- 现在可以在管理后台创建公告类型的文章了

