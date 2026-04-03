-- 允许 compute_logs.extra_data 存完整 Unicode（含 emoji），避免 MySQL utf8(3字节) 下 1366 错误。
-- 在目标库执行前请确认表名/列名与线上一致。
-- 若线上该列类型为 JSON 而非 LONGTEXT，请改用对应 JSON + utf8mb4 的 ALTER，或咨询 DBA。

ALTER TABLE compute_logs
  MODIFY COLUMN extra_data LONGTEXT
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL
  COMMENT '扩展数据（JSON格式，存储额外信息）';
