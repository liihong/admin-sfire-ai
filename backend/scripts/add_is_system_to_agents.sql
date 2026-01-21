-- 为 agents 表添加 is_system 字段
-- 用于标识是否为系统自用智能体
-- 0-否（默认），1-是
-- 系统自用智能体不会在前端用户界面显示，但会在 admin 后台显示

ALTER TABLE agents 
ADD COLUMN is_system INT NOT NULL DEFAULT 0 
COMMENT '是否为系统自用智能体：0-否，1-是';

-- 为现有数据设置默认值（可选，因为已经有 DEFAULT 0）
-- UPDATE agents SET is_system = 0 WHERE is_system IS NULL;

