-- 创建对话会话表
CREATE TABLE IF NOT EXISTS `conversations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `agent_id` BIGINT NULL COMMENT '智能体ID（可选）',
  `project_id` BIGINT NULL COMMENT '项目ID（可选）',
  `title` VARCHAR(256) NOT NULL DEFAULT '新对话' COMMENT '会话标题（自动生成，首条用户消息摘要）',
  `model_type` VARCHAR(64) NOT NULL DEFAULT 'deepseek' COMMENT '使用的模型类型',
  `total_tokens` INT NOT NULL DEFAULT 0 COMMENT '总token数（用于统计）',
  `message_count` INT NOT NULL DEFAULT 0 COMMENT '消息数量',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态：active-活跃, archived-归档',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `ix_conversations_user_id` (`user_id`),
  INDEX `ix_conversations_agent_id` (`agent_id`),
  INDEX `ix_conversations_project_id` (`project_id`),
  INDEX `ix_conversations_status` (`status`),
  INDEX `ix_conversations_created_at` (`created_at`),
  CONSTRAINT `fk_conversations_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conversations_agent_id` FOREIGN KEY (`agent_id`) REFERENCES `agents` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_conversations_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表';

-- 创建对话消息表
CREATE TABLE IF NOT EXISTS `conversation_messages` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `conversation_id` BIGINT NOT NULL COMMENT '会话ID',
  `role` VARCHAR(20) NOT NULL COMMENT '角色：user-用户, assistant-AI助手, system-系统',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `tokens` INT NOT NULL DEFAULT 0 COMMENT '该消息的token数（用于统计）',
  `sequence` BIGINT NOT NULL COMMENT '消息序号（用于排序，基于时间戳生成）',
  `embedding_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '向量化状态：pending-待处理, processing-处理中, completed-已完成, failed-失败',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `ix_conversation_messages_conversation_id` (`conversation_id`),
  INDEX `ix_conversation_messages_sequence` (`conversation_id`, `sequence`),
  INDEX `ix_conversation_messages_embedding_status` (`embedding_status`),
  CONSTRAINT `fk_conversation_messages_conversation_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表';

-- 创建对话片段表
CREATE TABLE IF NOT EXISTS `conversation_chunks` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `conversation_id` BIGINT NOT NULL COMMENT '会话ID',
  `user_message_id` BIGINT NOT NULL COMMENT '用户消息ID',
  `assistant_message_id` BIGINT NOT NULL COMMENT 'AI回复消息ID',
  `chunk_text` TEXT NOT NULL COMMENT '片段文本（User消息 + AI回复的组合）',
  `vector_id` VARCHAR(128) NULL COMMENT '向量数据库中的ID（用于关联）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `ix_conversation_chunks_conversation_id` (`conversation_id`),
  INDEX `ix_conversation_chunks_vector_id` (`vector_id`),
  CONSTRAINT `fk_conversation_chunks_conversation_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conversation_chunks_user_message_id` FOREIGN KEY (`user_message_id`) REFERENCES `conversation_messages` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conversation_chunks_assistant_message_id` FOREIGN KEY (`assistant_message_id`) REFERENCES `conversation_messages` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话片段表';

