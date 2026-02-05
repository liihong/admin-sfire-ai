-- 修复 agents 表 UTF8MB4 编码支持
-- 解决 emoji 等 4 字节 UTF-8 字符无法存储的问题
-- 执行前请备份数据库

-- 1. 确保 agents 表使用 utf8mb4 字符集
ALTER TABLE agents CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 确保 system_prompt 列使用 utf8mb4（显式转换，确保支持 emoji）
ALTER TABLE agents 
MODIFY COLUMN system_prompt TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '系统提示词';

-- 3. 同时修复其他可能包含 emoji 的 TEXT 字段
ALTER TABLE agents 
MODIFY COLUMN description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '描述信息';

ALTER TABLE agents 
MODIFY COLUMN routing_description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '路由特征描述';

-- 4. 验证字符集（可选，用于检查）
-- SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME 
-- FROM information_schema.COLUMNS 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME = 'agents' 
-- AND COLUMN_NAME IN ('system_prompt', 'description', 'routing_description');






