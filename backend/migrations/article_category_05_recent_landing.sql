-- 文章类型 article_category 增加 05「最近落地」（幂等）
-- 执行前请备份。适用于 MySQL 8+ / MariaDB 10.5+

INSERT INTO sys_dict_item (dict_id, item_value, item_label, description, is_enabled, sort_order, created_at, updated_at)
SELECT d.id, '05', '最近落地', NULL, 1, 5, NOW(), NOW()
FROM sys_dict d
WHERE d.dict_code = 'article_category'
  AND NOT EXISTS (SELECT 1 FROM sys_dict_item i WHERE i.dict_id = d.id AND i.item_value = '05');
