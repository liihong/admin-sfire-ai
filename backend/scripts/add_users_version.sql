-- 给 users 表添加 version 字段（乐观锁）
-- 执行: mysql -u root -p your_database < scripts/add_users_version.sql

ALTER TABLE users
ADD COLUMN version INT NOT NULL DEFAULT 0 COMMENT '版本号（乐观锁）' AFTER frozen_balance;

-- 创建索引以优化查询
CREATE INDEX idx_users_id_version ON users(id, version);

-- 验证
SELECT id, balance, frozen_balance, version FROM users LIMIT 5;
