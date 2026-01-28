-- 灵感表迁移SQL
-- 执行前请备份数据库
-- 用于存储用户灵感记录，支持标签、项目关联、生成内容等功能

-- ============================================
-- 第一步：创建灵感表
-- ============================================
CREATE TABLE IF NOT EXISTS inspirations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    project_id BIGINT NULL COMMENT '项目ID（可选，关联到具体项目）',
    content TEXT NOT NULL COMMENT '灵感内容（限制500字符）',
    tags JSON NULL COMMENT '标签数组（如 ["#视频脚本", "#文案想法"]）',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态：active-活跃, archived-归档, deleted-已删除',
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否置顶',
    generated_content TEXT NULL COMMENT '已生成的口播文案（可选）',
    generated_at DATETIME NULL COMMENT '生成时间（可选）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE COMMENT '关联用户表',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL COMMENT '关联项目表',
    
    -- 索引
    INDEX ix_inspirations_user_status (user_id, status) COMMENT '用户ID和状态联合索引',
    INDEX ix_inspirations_project_id (project_id) COMMENT '项目ID索引',
    INDEX ix_inspirations_created_at (created_at) COMMENT '创建时间索引（排序优化）',
    INDEX ix_inspirations_pinned_created (is_pinned, created_at) COMMENT '置顶和时间联合索引',
    
    -- 全文索引（用于搜索）
    FULLTEXT INDEX ft_inspirations_content (content) COMMENT '内容全文索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='灵感表';

-- ============================================
-- 第二步：添加内容长度检查约束（MySQL 5.7+ 支持 CHECK 约束）
-- ============================================
-- 注意：MySQL 5.7 之前版本不支持 CHECK 约束，需要在应用层验证
-- ALTER TABLE inspirations ADD CONSTRAINT chk_content_length CHECK (CHAR_LENGTH(content) <= 500);

-- ============================================
-- 第三步：创建索引优化查询性能
-- ============================================
-- 索引已在表创建时定义，这里仅作说明：
-- 1. ix_inspirations_user_status: 用于查询用户的活跃/归档灵感
-- 2. ix_inspirations_project_id: 用于按项目筛选灵感
-- 3. ix_inspirations_created_at: 用于按时间排序
-- 4. ix_inspirations_pinned_created: 用于置顶优先排序
-- 5. ft_inspirations_content: 用于全文搜索

-- ============================================
-- 第四步：数据迁移说明（如果需要）
-- ============================================
-- 如果已有灵感数据需要迁移，可以在这里添加迁移脚本
-- 例如：从其他表导入数据、转换格式等



