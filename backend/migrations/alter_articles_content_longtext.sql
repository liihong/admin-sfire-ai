-- articles.content 由 TEXT(约 64KB) 扩为 LONGTEXT，支持富文本/大段 HTML 保存
-- 执行前请确认表名与线上一致

ALTER TABLE articles
  MODIFY COLUMN content LONGTEXT NOT NULL
  COMMENT '文章内容（富文本）';
