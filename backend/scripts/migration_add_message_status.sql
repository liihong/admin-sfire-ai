-- 消息状态字段和Agent备用模型字段迁移SQL
-- 执行前请备份数据库

-- 1. 添加ConversationMessage状态字段
ALTER TABLE conversation_messages 
ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'pending',
ADD COLUMN error_message TEXT NULL;

-- 2. 添加索引
CREATE INDEX idx_conversation_messages_status ON conversation_messages(status);
CREATE INDEX idx_conversation_messages_role_status ON conversation_messages(role, status);

-- 3. 更新现有消息的状态（将现有消息标记为success）
UPDATE conversation_messages 
SET status = 'success' 
WHERE status = 'pending' AND role = 'assistant';

-- 4. 添加Agent备用模型和超时字段
ALTER TABLE agents 
ADD COLUMN fallback_model_id BIGINT NULL,
ADD COLUMN timeout_seconds INT NOT NULL DEFAULT 120;

-- 5. 添加外键约束
ALTER TABLE agents 
ADD CONSTRAINT fk_agents_fallback_model 
FOREIGN KEY (fallback_model_id) REFERENCES llm_models(id);

-- 6. 创建AdminDebugLog表
CREATE TABLE admin_debug_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    admin_user_id BIGINT NOT NULL,
    agent_id BIGINT NULL,
    model_id BIGINT NULL,
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    estimated_cost DECIMAL(10, 4) NOT NULL DEFAULT 0,
    debug_type VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_admin_user_id (admin_user_id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Admin调试日志表';















