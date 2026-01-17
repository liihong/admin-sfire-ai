-- 创建算力冻结记录表（幂等性保证）
-- 用于实现原子化扣减和幂等性控制

CREATE TABLE IF NOT EXISTS `compute_freeze_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `request_id` VARCHAR(128) NOT NULL COMMENT '请求ID（全局唯一，用于幂等性控制）',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `amount` DECIMAL(10,4) NOT NULL COMMENT '冻结金额',
  `status` VARCHAR(20) NOT NULL DEFAULT 'frozen' COMMENT '状态：frozen-已冻结, settled-已结算, refunded-已退还, failed-失败',
  `model_id` BIGINT NULL COMMENT '关联的模型ID',
  `conversation_id` BIGINT NULL COMMENT '关联的会话ID',
  `estimated_cost` DECIMAL(10,4) NULL COMMENT '预估消耗',
  `actual_cost` DECIMAL(10,4) NULL COMMENT '实际消耗（结算时填写）',
  `input_tokens` BIGINT NULL COMMENT '输入Token数（结算时填写）',
  `output_tokens` BIGINT NULL COMMENT '输出Token数（结算时填写）',
  `frozen_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '冻结时间',
  `settled_at` DATETIME NULL COMMENT '结算时间',
  `refunded_at` DATETIME NULL COMMENT '退款时间',
  `remark` VARCHAR(512) NULL COMMENT '备注说明',
  `extra_data` VARCHAR(1024) NULL COMMENT '扩展数据（JSON格式）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_compute_freeze_logs_request_id` (`request_id`) COMMENT '幂等性唯一索引',
  KEY `ix_compute_freeze_logs_user_id` (`user_id`),
  KEY `ix_compute_freeze_logs_status` (`status`),
  KEY `ix_compute_freeze_logs_created_at` (`created_at`),
  CONSTRAINT `fk_compute_freeze_logs_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_compute_freeze_logs_model_id` FOREIGN KEY (`model_id`) REFERENCES `llm_models` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_compute_freeze_logs_conversation_id` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='算力冻结记录表（幂等性保证）';
