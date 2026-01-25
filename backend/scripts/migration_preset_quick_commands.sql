-- 预设快捷指令库 SQL
-- 用于快速初始化快捷指令库的预设数据
-- 执行前请先确保已创建 quick_entries 表，并且 agents 表中有可用的 Agent

-- ============================================
-- 第一步：查询可用的 Agent ID（参考用）
-- ============================================
-- 执行以下SQL查询可用的 Agent，获取对应的 ID：
-- SELECT id, name, description, status FROM agents WHERE status = 1 AND is_system = 0 ORDER BY sort_order;

-- ============================================
-- 第二步：插入预设快捷指令
-- ============================================
-- 注意：下面的 action_value 字段使用了占位符 '1'，需要根据实际的 agent_id 进行替换
-- 建议先查询 agents 表，然后将对应的 agent_id 替换到 action_value 字段中

INSERT INTO quick_entries (unique_key, type, title, subtitle, icon_class, bg_color, action_type, action_value, tag, priority, status) VALUES
-- 文案创作类（优先级 1-3）
('copywriting_assistant', 'command', '文案助手', '专业的文案创作助手，帮你写出吸引人的内容', 'ri-edit-box-line', '#397FF6', 'agent', '1', 'hot', 1, 1),
('title_generator', 'command', '标题生成器', '快速生成吸引眼球的标题', 'ri-heading', '#F69C0E', 'agent', '1', 'none', 2, 1),
('content_rewriter', 'command', '内容改写', '帮你改写和优化现有内容', 'ri-refresh-line', '#00B781', 'agent', '1', 'none', 3, 1),

-- 创意灵感类（优先级 4-5）
('creative_inspiration', 'command', '创意灵感', '激发你的创作灵感', 'ri-lightbulb-flash-line', '#9C27B0', 'agent', '1', 'new', 4, 1),
('brainstorming', 'command', '头脑风暴', '多角度思考，拓展思路', 'ri-brain-line', '#E91E63', 'agent', '1', 'none', 5, 1),

-- 热点分析类（优先级 6-7）
('hotspot_analyzer', 'command', '热点分析', '分析当前热点，抓住流量密码', 'ri-fire-line', '#F53C5E', 'agent', '1', 'hot', 6, 1),
('trend_tracker', 'command', '趋势追踪', '追踪行业趋势，把握先机', 'ri-line-chart-line', '#FF9800', 'agent', '1', 'none', 7, 1),

-- 内容优化类（优先级 8-9）
('seo_optimizer', 'command', 'SEO优化', '优化内容，提升搜索排名', 'ri-search-line', '#2196F3', 'agent', '1', 'none', 8, 1),
('content_polish', 'command', '内容润色', '让内容更加流畅自然', 'ri-magic-line', '#4CAF50', 'agent', '1', 'none', 9, 1),

-- 专业领域类（优先级 10-12）
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
-- 1. 执行此SQL前，请先确保：
--    - quick_entries 表已创建（执行 migration_add_quick_entries.sql）
--    - agents 表中有可用的 Agent（status=1, is_system=0）
--
-- 2. 查询可用的 Agent ID：
--    SELECT id, name, description FROM agents WHERE status = 1 AND is_system = 0 ORDER BY sort_order;
--
-- 3. 替换 action_value：
--    - 将上面 INSERT 语句中的 action_value 字段（当前为 '1'）替换为实际的 agent_id
--    - 或者使用 UPDATE 语句批量更新：
--      UPDATE quick_entries SET action_value = '实际的agent_id' WHERE unique_key = 'copywriting_assistant';
--
-- 4. 如果某个快捷指令暂时没有对应的 Agent：
--    - 可以将 status 设置为 0（禁用）
--    - 或设置为 2（即将上线）
--
-- 5. 自定义快捷指令：
--    - 可以在管理后台（/admin/quick-entries）手动添加或修改
--    - 也可以通过 API 接口动态管理

-- ============================================
-- 批量更新 Agent ID 示例（需要根据实际情况修改）
-- ============================================
-- 假设你已经知道各个快捷指令对应的 agent_id，可以使用以下方式批量更新：
--
-- UPDATE quick_entries SET action_value = '2' WHERE unique_key = 'copywriting_assistant';
-- UPDATE quick_entries SET action_value = '3' WHERE unique_key = 'title_generator';
-- UPDATE quick_entries SET action_value = '4' WHERE unique_key = 'content_rewriter';
-- ... 以此类推

