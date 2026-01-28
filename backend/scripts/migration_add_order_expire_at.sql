-- 添加订单过期时间字段
-- 用于标记待支付订单的过期时间，超过此时间的订单自动失效

ALTER TABLE `compute_logs` 
ADD COLUMN `order_expire_at` DATETIME NULL COMMENT '订单过期时间（待支付订单超过此时间后自动失效）' AFTER `wechat_transaction_id`;

-- 为订单过期时间添加索引（便于查询过期订单）
CREATE INDEX `ix_compute_logs_order_expire_at` ON `compute_logs` (`order_expire_at`);

-- 为充值订单的order_id添加唯一索引（防止订单号重复）
-- 注意：仅对充值订单（type='recharge'）且order_id不为NULL的记录应用唯一约束
-- MySQL/MariaDB不支持条件唯一索引，需要在应用层处理唯一性
-- 但可以添加普通唯一索引，应用层需要确保order_id在充值订单中不为NULL
CREATE UNIQUE INDEX `uk_compute_logs_order_id_recharge` ON `compute_logs` (`order_id`) 
WHERE `type` = 'recharge' AND `order_id` IS NOT NULL;

-- 如果上面的条件唯一索引不支持，使用以下方式：
-- 先添加唯一索引（注意：这要求所有充值订单的order_id都不为NULL）
-- ALTER TABLE `compute_logs` ADD UNIQUE INDEX `uk_compute_logs_order_id` (`order_id`);

-- 注意：如果数据库不支持条件唯一索引，需要在应用层通过查询检查唯一性
-- 代码中已经实现了订单号重复检查和重试机制

