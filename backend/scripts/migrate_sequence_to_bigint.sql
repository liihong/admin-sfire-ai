-- 迁移脚本：将conversation_messages表的sequence字段从INT改为BIGINT
-- 原因：支持基于时间戳的序列号生成方式，避免并发插入时的锁冲突

-- 检查当前字段类型
-- SELECT COLUMN_TYPE FROM information_schema.COLUMNS 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME = 'conversation_messages' 
-- AND COLUMN_NAME = 'sequence';

-- 修改字段类型为BIGINT
ALTER TABLE `conversation_messages` 
MODIFY COLUMN `sequence` BIGINT NOT NULL COMMENT '消息序号（用于排序，基于时间戳生成）';

-- 验证修改结果
-- SELECT COLUMN_TYPE FROM information_schema.COLUMNS 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME = 'conversation_messages' 
-- AND COLUMN_NAME = 'sequence';
-- 应该返回: bigint(20)

