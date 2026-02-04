-- 算力充值系统迁移SQL
-- 执行前请备份数据库
-- 用于支持套餐管理和支付充值功能

-- ============================================
-- 第一步：创建套餐表（recharge_packages）
-- ============================================
CREATE TABLE IF NOT EXISTS recharge_packages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    name VARCHAR(128) NOT NULL COMMENT '套餐名称（如"新人尝鲜包"）',
    price DECIMAL(10, 2) NOT NULL COMMENT '销售价格（元）',
    power_amount DECIMAL(16, 0) NOT NULL COMMENT '获得算力（火源币）',
    unit_price VARCHAR(32) NULL COMMENT '实际单价（1:121格式，计算字段）',
    tag JSON NULL COMMENT '标签（如["最划算", "限购一次"]，JSON格式）',
    description TEXT NULL COMMENT '运营建议/描述',
    article_count INT NULL COMMENT '约可生成文案数量（计算字段）',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序（数字越小越靠前）',
    status INT NOT NULL DEFAULT 1 COMMENT '状态：0-禁用, 1-启用',
    is_popular BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否主推款',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX ix_recharge_packages_status (status) COMMENT '状态索引',
    INDEX ix_recharge_packages_sort_order (sort_order) COMMENT '排序索引',
    INDEX ix_recharge_packages_is_popular (is_popular) COMMENT '主推款索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='充值套餐表';

-- ============================================
-- 第二步：扩展 compute_logs 表添加支付字段
-- ============================================
ALTER TABLE compute_logs 
ADD COLUMN payment_amount DECIMAL(10, 2) NULL COMMENT '支付金额（元）' AFTER order_id,
ADD COLUMN payment_status VARCHAR(32) NULL DEFAULT 'pending' COMMENT '支付状态：pending-待支付, paid-已支付, failed-支付失败, cancelled-已取消' AFTER payment_amount,
ADD COLUMN payment_time DATETIME NULL COMMENT '支付时间' AFTER payment_status,
ADD COLUMN wechat_transaction_id VARCHAR(64) NULL COMMENT '微信交易号' AFTER payment_time,
ADD COLUMN package_id BIGINT NULL COMMENT '关联套餐ID' AFTER wechat_transaction_id;

-- 添加外键约束
ALTER TABLE compute_logs 
ADD CONSTRAINT fk_compute_logs_package_id 
FOREIGN KEY (package_id) REFERENCES recharge_packages(id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX ix_compute_logs_payment_status ON compute_logs(payment_status);
CREATE INDEX ix_compute_logs_package_id ON compute_logs(package_id);
CREATE INDEX ix_compute_logs_order_id_payment_status ON compute_logs(order_id, payment_status);

-- ============================================
-- 第三步：插入初始套餐数据
-- ============================================
INSERT INTO recharge_packages (name, price, power_amount, unit_price, tag, description, article_count, sort_order, status, is_popular) VALUES
('新人尝鲜包', 9.90, 1200, '1:121', '["限购一次"]', '限购一次。降低门槛，让用户不纠结。', 40, 1, 1, FALSE),
('新手创作者', 39.00, 5000, '1:128', '[]', '适合刚起号，一周更新 3-5 篇的用户。', 166, 2, 1, FALSE),
('爆款合伙人', 99.00, 15000, '1:151', '["最划算", "80%用户选择"]', '主推款。价格在百元内，性价比最高。', 500, 3, 1, TRUE),
('专业工作室', 199.00, 35000, '1:175', '[]', '针对有 6 人以上小团队的同行。', 1166, 4, 1, FALSE);









