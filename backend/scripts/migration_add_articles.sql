-- 文章表创建SQL
-- 执行前请备份数据库
-- 说明：创建文章表，用于管理小程序首页的文章内容（创始人故事、运营干货、客户案例）

-- ============================================
-- 创建文章表
-- ============================================
CREATE TABLE IF NOT EXISTS `articles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `category` ENUM('founder_story', 'operation_article', 'customer_case', 'announcement') NOT NULL COMMENT '文章类型: founder_story-创始人故事, operation_article-运营干货, customer_case-客户案例, announcement-公告',
    `title` VARCHAR(256) NOT NULL COMMENT '文章标题',
    `content` TEXT NOT NULL COMMENT '文章内容（富文本）',
    `summary` VARCHAR(500) DEFAULT NULL COMMENT '文章摘要/简介',
    `cover_image` VARCHAR(512) DEFAULT NULL COMMENT '封面图URL',
    `tags` JSON DEFAULT NULL COMMENT '标签数组（JSON格式，如 ["标签1", "标签2"]）',
    `sort_order` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '排序顺序（数字越小越靠前）',
    `publish_time` DATETIME DEFAULT NULL COMMENT '发布时间',
    `view_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览量',
    `is_published` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已发布',
    `is_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `ix_articles_category` (`category`),
    INDEX `ix_articles_is_published` (`is_published`),
    INDEX `ix_articles_is_enabled` (`is_enabled`),
    INDEX `ix_articles_sort_order` (`sort_order`),
    INDEX `ix_articles_publish_time` (`publish_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章表';

-- ============================================
-- 插入初始化数据（示例）
-- ============================================

-- 插入创始人故事示例
INSERT INTO `articles` (
    `category`,
    `title`,
    `content`,
    `summary`,
    `cover_image`,
    `tags`,
    `sort_order`,
    `publish_time`,
    `is_published`,
    `is_enabled`
) VALUES (
    'founder_story',
    '武峥:火源AI创始人',
    '<p>10年北京代码生涯,回乡做AI,只想帮你每天多省出一杯茶的时间。</p>',
    '10年北京代码生涯,回乡做AI,只想帮你每天多省出一杯茶的时间。',
    NULL,
    JSON_ARRAY('创始人', '创业故事'),
    0,
    NOW(),
    1,
    1
);

-- 插入运营干货示例
INSERT INTO `articles` (
    `category`,
    `title`,
    `content`,
    `summary`,
    `cover_image`,
    `tags`,
    `sort_order`,
    `publish_time`,
    `is_published`,
    `is_enabled`
) VALUES (
    'operation_article',
    '如何让AI写出"人味十足"的笔记',
    '<p>本文将介绍如何通过AI工具创作出更加自然、有温度的内容...</p>',
    '本文将介绍如何通过AI工具创作出更加自然、有温度的内容',
    NULL,
    JSON_ARRAY('01. 爆款逻辑', 'AI写作'),
    0,
    NOW(),
    1,
    1
),
(
    'operation_article',
    '县城商家起号最易犯的3个错误',
    '<p>在县城做短视频运营，很多商家容易犯这些错误...</p>',
    '在县城做短视频运营，很多商家容易犯这些错误',
    NULL,
    JSON_ARRAY('02. 避坑指南', '运营技巧'),
    1,
    NOW(),
    1,
    1
);

-- ============================================
-- 验证表创建结果
-- ============================================
-- 查询表结构
DESCRIBE `articles`;

-- 查询插入的数据
SELECT 
    id,
    category,
    title,
    summary,
    tags,
    is_published,
    is_enabled,
    created_at
FROM `articles`
ORDER BY category, sort_order;

-- ============================================
-- 执行完成
-- ============================================
-- 文章表已成功创建，并插入了示例数据
-- 可以通过管理后台继续添加更多文章内容

