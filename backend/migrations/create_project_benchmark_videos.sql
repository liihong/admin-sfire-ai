-- 对标账号视频缓存表
-- MySQL 8+ / MariaDB 10.5+

CREATE TABLE IF NOT EXISTS project_benchmark_videos (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '所属用户ID',
    project_id BIGINT NOT NULL COMMENT '项目ID',
    account_id BIGINT NOT NULL COMMENT '对标账号ID',
    aweme_id VARCHAR(64) NOT NULL COMMENT '抖音作品ID',
    is_top TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶：1-置顶，0-普通',
    `desc` VARCHAR(2000) NOT NULL DEFAULT '' COMMENT '文案',
    create_time INT NOT NULL DEFAULT 0 COMMENT '发布时间戳',
    cover_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '封面图',
    digg_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    comment_count INT NOT NULL DEFAULT 0 COMMENT '评论数',
    share_count INT NOT NULL DEFAULT 0 COMMENT '分享数',
    collect_count INT NOT NULL DEFAULT 0 COMMENT '收藏数',
    play_count INT NOT NULL DEFAULT 0 COMMENT '播放数',
    duration INT NOT NULL DEFAULT 0 COMMENT '时长秒',
    author_nickname VARCHAR(200) NOT NULL DEFAULT '' COMMENT '作者昵称',
    author_avatar_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '作者头像',
    video_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '视频直链',
    share_url VARCHAR(1024) NOT NULL DEFAULT '' COMMENT '分享链接',
    created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uq_pbv_account_aweme (account_id, aweme_id),
    KEY ix_pbv_project_account (project_id, account_id),
    KEY ix_pbv_account_top_create (account_id, is_top, create_time),
    CONSTRAINT fk_pbv_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_pbv_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_pbv_account FOREIGN KEY (account_id) REFERENCES project_benchmark_accounts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目对标账号视频缓存';

