-- 更新用户密码哈希
-- 说明：由于前端使用 MD5 加密密码后传输，数据库需要存储 MD5 密码的 bcrypt 哈希
-- 密码: 123456
-- MD5: e10adc3949ba59abbe56e057f20f883e
-- Bcrypt of MD5: $2b$12$tPHxSPInbC.9b12AdJmJPuIXzQ0oPkk21PIuatK1M3/CtskwIHL2O

UPDATE users
SET password_hash = '$2b$12$tPHxSPInbC.9b12AdJmJPuIXzQ0oPkk21PIuatK1M3/CtskwIHL2O',
    updated_at = NOW()
WHERE phone = '13261276633';

-- 验证更新结果
SELECT
    id,
    username,
    phone,
    nickname,
    password_hash,
    is_active,
    level,
    vip_expire_date,
    created_at,
    updated_at
FROM users
WHERE phone = '13261276633';
