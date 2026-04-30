-- 租户独立微信小程序换票密钥（可与 wechat_app_id 成对使用）
-- MySQL 8+

ALTER TABLE `tenants`
  ADD COLUMN `wechat_app_secret` VARCHAR(128) NULL
  COMMENT '微信小程序 AppSecret（与 wechat_app_id 成对；为空且 AppID 与 .env WECHAT_APP_ID 一致时使用全局 Secret）'
  AFTER `wechat_app_id`;
