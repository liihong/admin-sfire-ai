-- agents 表改为 utf8mb4，避免 system_prompt / welcome_message / description 等写入 emoji（4 字节 UTF-8）时出现 MySQL 1366。
-- 连接串虽已使用 charset=utf8mb4，若表或列为旧 utf8（utf8mb3），仍会报错。
-- 执行: mysql -u用户 -p 数据库名 < alter_agents_utf8mb4.sql

ALTER TABLE agents
  CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
