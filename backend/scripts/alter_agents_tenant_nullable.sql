-- MySQL：允许 agents.tenant_id 为 NULL，表示全租户可用的公用智能体
-- 执行前请备份。与 models.agent.Agent.tenant_id nullable 一致。
ALTER TABLE agents MODIFY COLUMN tenant_id BIGINT NULL COMMENT '租户ID，NULL 表示全租户可用';
