-- 文章类型：sys_dict article_category（item_value 01-04），articles 表增加 author
-- 执行前请备份。适用于 MySQL 8+ / MariaDB 10.5+

-- ========== 1. 字典类型 ==========
INSERT IGNORE INTO sys_dict (dict_code, dict_name, description, is_enabled, sort_order, created_at, updated_at)
VALUES ('article_category', '文章类型', '小程序/后台文章分类（articles.category 存 item_value）', 1, 0, NOW(), NOW());

-- ========== 2. 字典项（幂等：同 dict + value 已存在则跳过）==========
INSERT INTO sys_dict_item (dict_id, item_value, item_label, description, is_enabled, sort_order, created_at, updated_at)
SELECT d.id, '01', '商业底牌', NULL, 1, 1, NOW(), NOW()
FROM sys_dict d
WHERE d.dict_code = 'article_category'
  AND NOT EXISTS (SELECT 1 FROM sys_dict_item i WHERE i.dict_id = d.id AND i.item_value = '01');

INSERT INTO sys_dict_item (dict_id, item_value, item_label, description, is_enabled, sort_order, created_at, updated_at)
SELECT d.id, '02', '流量心法', NULL, 1, 2, NOW(), NOW()
FROM sys_dict d
WHERE d.dict_code = 'article_category'
  AND NOT EXISTS (SELECT 1 FROM sys_dict_item i WHERE i.dict_id = d.id AND i.item_value = '02');

INSERT INTO sys_dict_item (dict_id, item_value, item_label, description, is_enabled, sort_order, created_at, updated_at)
SELECT d.id, '03', '实操手册', NULL, 1, 3, NOW(), NOW()
FROM sys_dict d
WHERE d.dict_code = 'article_category'
  AND NOT EXISTS (SELECT 1 FROM sys_dict_item i WHERE i.dict_id = d.id AND i.item_value = '03');

INSERT INTO sys_dict_item (dict_id, item_value, item_label, description, is_enabled, sort_order, created_at, updated_at)
SELECT d.id, '04', '创始人说', NULL, 1, 4, NOW(), NOW()
FROM sys_dict d
WHERE d.dict_code = 'article_category'
  AND NOT EXISTS (SELECT 1 FROM sys_dict_item i WHERE i.dict_id = d.id AND i.item_value = '04');

-- ========== 3. articles：category 改为字典值，并增加 author ==========
ALTER TABLE articles MODIFY COLUMN category VARCHAR(8) NOT NULL
  COMMENT '文章类型（sys_dict article_category 的 item_value：01-04）';

UPDATE articles SET category = CASE category
  WHEN 'founder_story' THEN '04'
  WHEN 'operation_article' THEN '02'
  WHEN 'customer_case' THEN '03'
  WHEN 'announcement' THEN '01'
  WHEN '01' THEN '01'
  WHEN '02' THEN '02'
  WHEN '03' THEN '03'
  WHEN '04' THEN '04'
  ELSE '04'
END;

ALTER TABLE articles ADD COLUMN author VARCHAR(128) NOT NULL DEFAULT 'Source Fire' COMMENT '作者' AFTER category;
