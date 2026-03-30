-- MySQL 8+: 将 projects.persona_settings 旧 JSON 迁移为新结构（13 字符串键 + keywords 数组）
-- 执行前请备份: mysqldump -u... -p... DB_NAME projects > backup_projects.sql
--
-- 说明：
-- - introduction -> ip_experience
-- - tone -> style_tones, catchphrase -> style_mantra，并合并 taboos/benchmark_accounts/content_style 到 style_mantra
-- - target_audience -> cl_targetPopulation, target_pains -> cl_painPoints
-- - industry_understanding -> cl_advantages, unique_views -> cl_feedback
-- - ip_name/ip_industry 取自列 name/industry
-- - keywords 保留为 JSON 数组

UPDATE projects p
SET persona_settings = JSON_MERGE_PATCH(
  COALESCE(
    CASE WHEN JSON_VALID(p.persona_settings) THEN CAST(p.persona_settings AS JSON) END,
    JSON_OBJECT()
  ),
  JSON_OBJECT(
    'ip_name', COALESCE(p.name, ''),
    'ip_age', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.ip_age')), ''),
    'ip_city', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.ip_city')), ''),
    'ip_industry', COALESCE(p.industry, '通用'),
    'ip_identityTag', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.ip_identityTag')), ''),
    'ip_experience', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.ip_experience')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.introduction')), '')
    ),
    'cl_mainProducts', COALESCE(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.cl_mainProducts')), ''),
    'cl_targetPopulation', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.cl_targetPopulation')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.target_audience')), '')
    ),
    'cl_painPoints', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.cl_painPoints')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.target_pains')), '')
    ),
    'cl_advantages', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.cl_advantages')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.industry_understanding')), '')
    ),
    'cl_feedback', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.cl_feedback')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.unique_views')), '')
    ),
    'style_tones', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.style_tones')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.tone')), '专业亲和')
    ),
    'style_mantra', COALESCE(
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.style_mantra')), ''),
      NULLIF(JSON_UNQUOTE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.catchphrase')), '')
    ),
    'keywords', COALESCE(JSON_EXTRACT(CAST(p.persona_settings AS JSON), '$.keywords'), JSON_ARRAY())
  )
)
WHERE JSON_VALID(p.persona_settings);

-- 注意：若需把 taboos/benchmark_accounts/content_style 拼进 style_mantra，建议在应用层用 normalize_persona_settings_dict 再写回，
-- 或在此处用存储过程处理数组字段；上线前请在测试库验证。
