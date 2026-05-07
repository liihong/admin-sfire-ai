-- C 端 quick-entries 列表：tenant_id + type + status + ORDER BY priority
-- tenants：按 wechat_app_id 解析租户（每个带 appid 的请求会先查）

ALTER TABLE `quick_entries`
  ADD INDEX `ix_quick_entries_tenant_type_status_priority` (`tenant_id`, `type`, `status`, `priority`);

ALTER TABLE `tenants`
  ADD INDEX `ix_tenants_wechat_app_id` (`wechat_app_id`);
