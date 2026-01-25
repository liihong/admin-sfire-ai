-- 快捷入口配置表迁移SQL
-- 执行前请备份数据库
-- 用于统一管理"今天拍点啥"和"快捷指令库"的配置

-- ============================================
-- 第一步：创建快捷入口配置表
-- ============================================
CREATE TABLE IF NOT EXISTS quick_entries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    unique_key VARCHAR(64) NOT NULL COMMENT '唯一标识（如：story, opinion, agent_001）',
    type VARCHAR(16) NOT NULL COMMENT '入口类型: category-今天拍点啥, command-快捷指令库',
    title VARCHAR(128) NOT NULL COMMENT '标题（主标题）',
    subtitle VARCHAR(256) NULL COMMENT '副标题（描述信息）',
    icon_class VARCHAR(64) NOT NULL COMMENT '图标类名（RemixIcon 类名，如：ri-book-line）',
    bg_color VARCHAR(16) NULL COMMENT '背景色（十六进制颜色，如：#F69C0E）',
    action_type VARCHAR(16) NOT NULL COMMENT '动作类型: agent-调用Agent, skill-调用Skill, prompt-硬编码Prompt',
    action_value TEXT NOT NULL COMMENT '动作值（根据action_type：agent_id/skill_id/prompt文本）',
    tag VARCHAR(16) NOT NULL DEFAULT 'none' COMMENT '标签: none-无标签, new-新上线, hot-最热门',
    priority INT NOT NULL DEFAULT 0 COMMENT '排序权重（数字越小越靠前）',
    status INT NOT NULL DEFAULT 1 COMMENT '状态：0-禁用, 1-启用, 2-即将上线',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_quick_entries_unique_key (unique_key),
    INDEX ix_quick_entries_type (type),
    INDEX ix_quick_entries_status (status),
    INDEX ix_quick_entries_priority (priority),
    INDEX ix_quick_entries_tag (tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='快捷入口配置表';

-- ============================================
-- 第二步：初始化示例数据（可选）
-- ============================================

-- "今天拍点啥"的5个分类
INSERT INTO quick_entries (unique_key, type, title, subtitle, icon_class, bg_color, action_type, action_value, tag, priority, status) VALUES
('story', 'category', '讲故事', NULL, 'ri-book-line', '#F69C0E', 'agent', '1', 'none', 1, 1),
('opinion', 'category', '聊观点', NULL, 'ri-chat-3-line', '#397FF6', 'agent', '1', 'none', 2, 1),
('process', 'category', '晒过程', NULL, 'ri-time-line', '#397FF6', 'agent', '1', 'none', 3, 1),
('knowledge', 'category', '教知识', NULL, 'ri-graduation-cap-line', '#00B781', 'agent', '1', 'none', 4, 1),
('hotspot', 'category', '蹭热点', NULL, 'ri-fire-line', '#F53C5E', 'agent', '1', 'hot', 5, 1)
ON DUPLICATE KEY UPDATE 
    title = VALUES(title),
    icon_class = VALUES(icon_class),
    bg_color = VALUES(bg_color),
    priority = VALUES(priority);

-- 注意：示例数据中的 action_value 设置为 '1'（agent_id），实际使用时需要根据实际情况修改
-- 如果还没有对应的 Agent，可以先设置为一个占位值，后续在管理后台修改

-- ============================================
-- 第三步：预设快捷指令库（command类型）
-- ============================================

-- 预设快捷指令库数据
-- 注意：action_value 中的 agent_id 需要根据实际的 agents 表中的 ID 进行修改
-- 可以先查询 agents 表获取可用的 agent_id，然后替换下面的占位符

-- 查询可用 Agent 的 SQL（用于获取 agent_id）：
-- SELECT id, name FROM agents WHERE status = 1 AND is_system = 0 ORDER BY sort_order LIMIT 10;

INSERT INTO quick_entries (unique_key, type, title, subtitle, icon_class, bg_color, action_type, action_value, tag, priority, status) VALUES
-- 文案创作类
('copywriting_assistant', 'command', '文案助手', '专业的文案创作助手，帮你写出吸引人的内容', 'ri-edit-box-line', '#397FF6', 'agent', '1', 'hot', 1, 1),
('title_generator', 'command', '标题生成器', '快速生成吸引眼球的标题', 'ri-heading', '#F69C0E', 'agent', '1', 'none', 2, 1),
('content_rewriter', 'command', '内容改写', '帮你改写和优化现有内容', 'ri-refresh-line', '#00B781', 'agent', '1', 'none', 3, 1),

-- 创意灵感类
('creative_inspiration', 'command', '创意灵感', '激发你的创作灵感', 'ri-lightbulb-flash-line', '#9C27B0', 'agent', '1', 'new', 4, 1),
('brainstorming', 'command', '头脑风暴', '多角度思考，拓展思路', 'ri-brain-line', '#E91E63', 'agent', '1', 'none', 5, 1),

-- 热点分析类
('hotspot_analyzer', 'command', '热点分析', '分析当前热点，抓住流量密码', 'ri-fire-line', '#F53C5E', 'agent', '1', 'hot', 6, 1),
('trend_tracker', 'command', '趋势追踪', '追踪行业趋势，把握先机', 'ri-line-chart-line', '#FF9800', 'agent', '1', 'none', 7, 1),

-- 内容优化类
('seo_optimizer', 'command', 'SEO优化', '优化内容，提升搜索排名', 'ri-search-line', '#2196F3', 'agent', '1', 'none', 8, 1),
('content_polish', 'command', '内容润色', '让内容更加流畅自然', 'ri-magic-line', '#4CAF50', 'agent', '1', 'none', 9, 1),

-- 专业领域类
('marketing_copy', 'command', '营销文案', '专业的营销文案创作', 'ri-megaphone-line', '#FF5722', 'agent', '1', 'none', 10, 1),
('product_description', 'command', '产品描述', '撰写吸引人的产品描述', 'ri-shopping-bag-line', '#607D8B', 'agent', '1', 'none', 11, 1),
('social_media_post', 'command', '社交媒体', '创作适合社交媒体的内容', 'ri-share-line', '#00BCD4', 'agent', '1', 'none', 12, 1)
ON DUPLICATE KEY UPDATE 
    title = VALUES(title),
    subtitle = VALUES(subtitle),
    icon_class = VALUES(icon_class),
    bg_color = VALUES(bg_color),
    action_type = VALUES(action_type),
    action_value = VALUES(action_value),
    tag = VALUES(tag),
    priority = VALUES(priority),
    status = VALUES(status);

-- ============================================
-- 使用说明：
-- ============================================
-- 1. 执行此SQL前，请先确保 agents 表中已有可用的 Agent
-- 2. 执行以下SQL查询可用的 Agent ID：
--    SELECT id, name, status FROM agents WHERE status = 1 AND is_system = 0 ORDER BY sort_order;
-- 3. 根据查询结果，将上面 INSERT 语句中的 action_value 字段（当前为 '1'）替换为实际的 agent_id
-- 4. 或者，可以先插入占位数据，后续在管理后台（/admin/quick-entries）手动修改 action_value
-- 5. 如果某个快捷指令暂时没有对应的 Agent，可以将 status 设置为 0（禁用）或 2（即将上线）

