-- 优化对话表的索引,减少锁冲突
-- 执行前请备份数据库

-- 1. 检查现有索引
SHOW INDEX FROM conversation_messages;
SHOW INDEX FROM conversations;

-- 2. 添加复合索引以优化查询性能
-- 这个索引可以加速 save_conversation_async 中的 sequence 查询
CREATE INDEX IF NOT EXISTS idx_conv_msg_conv_seq
ON conversation_messages(conversation_id, sequence DESC);

-- 3. 添加覆盖索引以减少回表查询
CREATE INDEX IF NOT EXISTS idx_conv_messages_covering
ON conversation_messages(conversation_id, sequence, role, content(100));

-- 4. 优化 conversations 表的锁竞争
-- 为经常更新的字段添加单独索引
CREATE INDEX IF NOT EXISTS idx_conv_tokens_count
ON conversations(total_tokens, message_count);

-- 5. 验证索引是否创建成功
SHOW INDEX FROM conversation_messages;
SHOW INDEX FROM conversations;
