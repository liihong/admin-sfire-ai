-- 子租户用户迁移后，将仍留在主租户(DEFAULT=1)的项目同步为所属用户的 tenant_id
-- 场景：用户在 dingma(tenant_id=2) 注册/迁移，但 IP 项目在 tenant_id=1 下创建

UPDATE `projects` p
INNER JOIN `users` u ON p.user_id = u.id
SET p.tenant_id = u.tenant_id
WHERE p.is_deleted = 0
  AND p.tenant_id != u.tenant_id;
