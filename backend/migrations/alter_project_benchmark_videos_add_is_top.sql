-- 为已存在的 project_benchmark_videos 表补充置顶排序字段与索引
-- MySQL 8+ / MariaDB 10.5+

ALTER TABLE project_benchmark_videos
    ADD COLUMN IF NOT EXISTS is_top TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶：1-置顶，0-普通' AFTER aweme_id;

-- 若旧索引存在则先删除，再建立新索引
DROP INDEX IF EXISTS ix_pbv_account_create_time ON project_benchmark_videos;
CREATE INDEX ix_pbv_account_top_create ON project_benchmark_videos(account_id, is_top, create_time);

