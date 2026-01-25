-- 添加项目头像字段迁移SQL
-- 执行前请备份数据库
-- 为 projects 表添加 avatar_letter 和 avatar_color 字段

-- 检查并添加 avatar_letter 字段（如果不存在）
-- 注意：MySQL 不支持 IF NOT EXISTS，需要手动检查或使用存储过程
-- 如果字段已存在，执行会报错，可以忽略

-- 1. 添加 avatar_letter 字段（项目首字母/头像显示字符）
ALTER TABLE projects 
ADD COLUMN avatar_letter VARCHAR(10) NOT NULL DEFAULT '' COMMENT '项目首字母/头像显示字符';

-- 2. 添加 avatar_color 字段（头像背景色）
ALTER TABLE projects 
ADD COLUMN avatar_color VARCHAR(20) NOT NULL DEFAULT '#3B82F6' COMMENT '头像背景色';

-- 3. 更新现有项目的 avatar_letter（根据项目名称首字母生成）
UPDATE projects 
SET avatar_letter = UPPER(LEFT(name, 1))
WHERE avatar_letter = '' AND name IS NOT NULL AND name != '';

-- 4. 如果项目名称为空，设置默认值
UPDATE projects 
SET avatar_letter = 'P'
WHERE avatar_letter = '' OR avatar_letter IS NULL;

-- 5. 确保所有项目的 avatar_color 都有默认值
UPDATE projects 
SET avatar_color = '#3B82F6'
WHERE avatar_color = '' OR avatar_color IS NULL;

