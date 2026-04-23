-- 为已存在的 project_benchmark_accounts 表补充账号资料缓存字段
-- MySQL 8+ / MariaDB 10.5+

ALTER TABLE project_benchmark_accounts
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '头像 URL（缓存）' AFTER nickname,
    ADD COLUMN IF NOT EXISTS signature VARCHAR(1000) NOT NULL DEFAULT '' COMMENT '简介（缓存）' AFTER avatar_url,
    ADD COLUMN IF NOT EXISTS follower_count INT NOT NULL DEFAULT 0 COMMENT '粉丝数（缓存）' AFTER signature,
    ADD COLUMN IF NOT EXISTS following_count INT NOT NULL DEFAULT 0 COMMENT '关注数（缓存）' AFTER follower_count,
    ADD COLUMN IF NOT EXISTS total_favorited INT NOT NULL DEFAULT 0 COMMENT '获赞总数（缓存）' AFTER following_count,
    ADD COLUMN IF NOT EXISTS aweme_count INT NOT NULL DEFAULT 0 COMMENT '作品数（缓存）' AFTER total_favorited;

