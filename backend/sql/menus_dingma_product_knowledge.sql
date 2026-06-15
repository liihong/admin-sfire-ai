-- =============================================================================
-- 顶妈产品配方：挂到已有「技能组装」父菜单（name=skill-assembly, 通常 id=17）
-- 可重复执行
-- =============================================================================

SET @skill_parent_id := (
  SELECT `id` FROM `menus` WHERE `name` IN ('skill-assembly', 'skillAssembly') ORDER BY `id` LIMIT 1
);

INSERT INTO `menus` (
  `parent_id`, `name`, `path`, `component`, `redirect`,
  `sort_order`, `icon`, `title`, `is_link`,
  `is_hide`, `is_full`, `is_affix`, `is_keep_alive`,
  `is_enabled`, `created_at`, `updated_at`
)
SELECT
  @skill_parent_id,
  'dingmaProductKnowledge',
  '/skill-assembly/product-knowledge',
  '/dingma/productKnowledge/index',
  NULL,
  3,
  'Notebook',
  '产品配方',
  '',
  0, 0, 0, 1,
  1,
  NOW(),
  NOW()
FROM DUAL
WHERE @skill_parent_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `name` = 'dingmaProductKnowledge');

UPDATE `menus`
SET
  `parent_id` = @skill_parent_id,
  `path` = '/skill-assembly/product-knowledge',
  `component` = '/dingma/productKnowledge/index',
  `sort_order` = 3,
  `icon` = 'Notebook',
  `title` = '产品配方',
  `is_hide` = 0,
  `is_enabled` = 1,
  `updated_at` = NOW()
WHERE `name` = 'dingmaProductKnowledge'
  AND @skill_parent_id IS NOT NULL;
