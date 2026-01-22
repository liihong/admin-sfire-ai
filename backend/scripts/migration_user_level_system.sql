-- 用户等级权限系统迁移SQL
-- 执行前请备份数据库
-- 执行顺序：按顺序执行，不要跳过任何步骤

-- ============================================
-- 第一步：创建用户等级配置表
-- ============================================
CREATE TABLE IF NOT EXISTS user_levels (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(32) NOT NULL COMMENT '等级代码：normal-观望者, vip-个人创作者, svip-小工作室, max-矩阵大佬',
    name VARCHAR(64) NOT NULL COMMENT '等级名称（中文显示）',
    max_ip_count INT NULL COMMENT '最大IP数量（NULL表示不限制）',
    ip_type VARCHAR(16) NOT NULL DEFAULT 'permanent' COMMENT 'IP类型：temporary-临时, permanent-永久',
    daily_tokens_limit INT NULL COMMENT '每日AI能量限制（NULL表示无限制，normal用户限制3次）',
    can_use_advanced_agent TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可使用高级智能体',
    unlimited_conversations TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否无限制对话',
    is_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用该等级',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序顺序（数字越小越靠前）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_user_levels_code (code),
    INDEX ix_user_levels_code (code),
    INDEX ix_user_levels_is_enabled (is_enabled),
    INDEX ix_user_levels_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户等级配置表';

-- ============================================
-- 第二步：初始化等级数据
-- ============================================
INSERT INTO user_levels (code, name, max_ip_count, ip_type, daily_tokens_limit, can_use_advanced_agent, unlimited_conversations, is_enabled, sort_order) VALUES
('normal', '观望者', 1, 'temporary', 3, 0, 0, 1, 1),
('vip', '个人创作者', 1, 'permanent', NULL, 1, 1, 1, 2),
('svip', '小工作室', 5, 'permanent', NULL, 1, 1, 1, 3),
('max', '矩阵大佬/B端', NULL, 'permanent', NULL, 1, 1, 1, 4)
ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    max_ip_count = VALUES(max_ip_count),
    ip_type = VALUES(ip_type),
    daily_tokens_limit = VALUES(daily_tokens_limit),
    can_use_advanced_agent = VALUES(can_use_advanced_agent),
    unlimited_conversations = VALUES(unlimited_conversations),
    is_enabled = VALUES(is_enabled),
    sort_order = VALUES(sort_order);

-- ============================================
-- 第三步：为users表添加level_code字段
-- ============================================
ALTER TABLE users 
ADD COLUMN level_code VARCHAR(32) NULL COMMENT '用户等级代码（外键关联user_levels表）：normal/vip/svip/max' AFTER level;

-- 添加外键约束
ALTER TABLE users 
ADD CONSTRAINT fk_users_level_code 
FOREIGN KEY (level_code) REFERENCES user_levels(code) ON DELETE RESTRICT;

-- 添加索引
CREATE INDEX ix_users_level_code ON users(level_code);

-- ============================================
-- 第四步：迁移现有数据（member→vip, partner→svip）
-- ============================================
-- 将member等级映射为vip
UPDATE users 
SET level_code = 'vip' 
WHERE level = 'member' AND level_code IS NULL;

-- 将partner等级映射为svip
UPDATE users 
SET level_code = 'svip' 
WHERE level = 'partner' AND level_code IS NULL;

-- 将normal等级映射为normal
UPDATE users 
SET level_code = 'normal' 
WHERE level = 'normal' AND level_code IS NULL;

-- ============================================
-- 第五步：为projects表添加status字段
-- ============================================
ALTER TABLE projects 
ADD COLUMN status INT NOT NULL DEFAULT 1 COMMENT '状态：1-正常, 2-已冻结' AFTER is_deleted;

-- 添加索引
CREATE INDEX ix_projects_status ON projects(status);

-- 更新现有数据，确保所有项目状态为1（正常）
UPDATE projects SET status = 1 WHERE status IS NULL OR status = 0;

-- ============================================
-- 迁移完成
-- ============================================
-- 注意：
-- 1. 旧的level字段保留用于兼容，新系统使用level_code
-- 2. 如果后续需要完全移除level字段，可以执行：
--    ALTER TABLE users DROP COLUMN level;
--    ALTER TABLE users DROP INDEX ix_users_level;
-- 3. 建议在确认新系统稳定运行后再移除旧字段

