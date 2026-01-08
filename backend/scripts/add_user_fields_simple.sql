-- 添加用户表新字段的SQL脚本
-- 添加 partner_balance 和 vip_expire_date 字段
-- 
-- 使用方法：
-- 1. 如果字段不存在，直接执行下面的SQL
-- 2. 如果字段已存在，执行时会报错，可以忽略（字段已存在错误不影响）
-- 3. 或者在执行前先检查字段是否存在

-- 添加 partner_balance 字段
ALTER TABLE users 
ADD COLUMN partner_balance DECIMAL(16,4) NOT NULL DEFAULT 0.0000 
COMMENT '合伙人资产余额' 
AFTER frozen_balance;

-- 添加 vip_expire_date 字段
ALTER TABLE users 
ADD COLUMN vip_expire_date DATETIME NULL 
COMMENT '会员到期时间' 
AFTER partner_balance;









