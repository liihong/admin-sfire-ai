-- 项目对标抖音账号表
-- 执行前请备份数据库。适用于 MySQL 8+ / MariaDB 10.5+

CREATE TABLE IF NOT EXISTS project_benchmark_accounts (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '所属用户ID',
    project_id BIGINT NOT NULL COMMENT '项目ID',
    sec_uid VARCHAR(128) NOT NULL COMMENT '抖音 sec_uid',
    profile_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '用户填写的主页或分享链接',
    nickname VARCHAR(200) NOT NULL DEFAULT '' COMMENT '昵称（解析或同步缓存）',
    avatar_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '头像 URL（缓存）',
    signature VARCHAR(1000) NOT NULL DEFAULT '' COMMENT '简介（缓存）',
    follower_count INT NOT NULL DEFAULT 0 COMMENT '粉丝数（缓存）',
    following_count INT NOT NULL DEFAULT 0 COMMENT '关注数（缓存）',
    total_favorited INT NOT NULL DEFAULT 0 COMMENT '获赞总数（缓存）',
    aweme_count INT NOT NULL DEFAULT 0 COMMENT '作品数（缓存）',
    remark TEXT NULL COMMENT '备注',
    is_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uq_project_benchmark_sec_uid (project_id, sec_uid),
    KEY ix_pba_project_id (project_id),
    KEY ix_pba_user_id (user_id),
    CONSTRAINT fk_pba_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_pba_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目对标抖音账号';
