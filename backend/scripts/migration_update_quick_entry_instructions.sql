-- 更新快捷指令库的 instructions 字段
-- 根据快捷指令的功能特点，生成默认的指令内容
-- 执行前请备份数据库

-- ============================================
-- 更新 command 类型的快捷指令的 instructions 字段
-- ============================================

-- 1. 文案助手 - 需要改写
UPDATE quick_entries 
SET instructions = '请帮我改写以下文案，让它更加吸引人、更有感染力。要求：1. 保持原意不变；2. 语言更加生动有趣；3. 符合目标受众的阅读习惯。'
WHERE unique_key = 'copywriting_assistant' AND type = 'command';

-- 2. 标题生成器 - 需要重构
UPDATE quick_entries 
SET instructions = '请帮我生成一个吸引眼球的标题。要求：1. 简洁有力，不超过20字；2. 能够激发读者的好奇心；3. 符合平台调性和目标受众喜好。'
WHERE unique_key = 'title_generator' AND type = 'command';

-- 3. 内容改写 - 需要扩展
UPDATE quick_entries 
SET instructions = '请帮我扩展以下内容，让它更加丰富完整。要求：1. 保持核心观点不变；2. 增加细节描述和案例支撑；3. 逻辑清晰，层次分明。'
WHERE unique_key = 'content_rewriter' AND type = 'command';

-- 4. 创意灵感 - 需要人设故事
UPDATE quick_entries 
SET instructions = '请帮我创作一个人设故事，用于账号定位和内容规划。要求：1. 符合我的行业和定位；2. 有鲜明的个人特色；3. 能够持续产出内容。'
WHERE unique_key = 'creative_inspiration' AND type = 'command';

-- 5. 头脑风暴 - 需要同城文案
UPDATE quick_entries 
SET instructions = '请帮我创作一条同城相关的文案。要求：1. 突出本地特色和地域优势；2. 能够吸引本地用户关注；3. 适合在同城社交平台发布。'
WHERE unique_key = 'brainstorming' AND type = 'command';

-- 6. 热点分析 - 需要选题
UPDATE quick_entries 
SET instructions = '请帮我分析当前热点，并推荐适合的选题方向。要求：1. 结合我的账号定位；2. 分析热点的传播价值和时效性；3. 提供具体的创作建议。'
WHERE unique_key = 'hotspot_analyzer' AND type = 'command';

-- ============================================
-- 批量更新（如果上面的单独更新没有匹配到记录，可以使用批量更新）
-- ============================================

-- 方式一：根据 unique_key 批量更新（推荐）
UPDATE quick_entries 
SET instructions = CASE unique_key
    WHEN 'copywriting_assistant' THEN '请帮我改写以下文案，让它更加吸引人、更有感染力。要求：1. 保持原意不变；2. 语言更加生动有趣；3. 符合目标受众的阅读习惯。'
    WHEN 'title_generator' THEN '请帮我生成一个吸引眼球的标题。要求：1. 简洁有力，不超过20字；2. 能够激发读者的好奇心；3. 符合平台调性和目标受众喜好。'
    WHEN 'content_rewriter' THEN '请帮我扩展以下内容，让它更加丰富完整。要求：1. 保持核心观点不变；2. 增加细节描述和案例支撑；3. 逻辑清晰，层次分明。'
    WHEN 'creative_inspiration' THEN '请帮我创作一个人设故事，用于账号定位和内容规划。要求：1. 符合我的行业和定位；2. 有鲜明的个人特色；3. 能够持续产出内容。'
    WHEN 'brainstorming' THEN '请帮我创作一条同城相关的文案。要求：1. 突出本地特色和地域优势；2. 能够吸引本地用户关注；3. 适合在同城社交平台发布。'
    WHEN 'hotspot_analyzer' THEN '请帮我分析当前热点，并推荐适合的选题方向。要求：1. 结合我的账号定位；2. 分析热点的传播价值和时效性；3. 提供具体的创作建议。'
    ELSE instructions
END
WHERE type = 'command' AND unique_key IN (
    'copywriting_assistant',
    'title_generator',
    'content_rewriter',
    'creative_inspiration',
    'brainstorming',
    'hotspot_analyzer'
);

-- ============================================
-- 验证更新结果
-- ============================================
-- 执行以下 SQL 查看更新结果：
-- SELECT unique_key, title, instructions FROM quick_entries WHERE type = 'command' ORDER BY priority;

-- ============================================
-- 说明
-- ============================================
-- 1. 这些 instructions 是默认模板，用户可以在使用前进行编辑
-- 2. category 类型的快捷指令不需要 instructions（保持 NULL 即可）
-- 3. 如果某个快捷指令的 unique_key 不存在，对应的 UPDATE 语句不会影响任何记录
-- 4. 建议先执行验证 SQL，确认需要更新的记录存在后再执行 UPDATE

