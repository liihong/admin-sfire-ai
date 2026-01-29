-- 快捷入口配置菜单注册SQL
-- 执行前请备份数据库
-- 说明：将快捷入口配置管理页面注册到菜单系统中，作为"小程序装修"的子菜单

-- ============================================
-- 创建"快捷入口配置"子菜单
-- ============================================
-- parent_id = 6 对应"小程序装修"父菜单
-- 如果父菜单ID不是6，请先查询确认正确的parent_id

-- 插入快捷入口配置菜单（如果不存在）
INSERT INTO menus (
    parent_id,
    name,
    path,
    component,
    title,
    icon,
    sort_order,
    is_link,
    is_hide,
    is_full,
    is_affix,
    is_keep_alive,
    is_enabled,
    created_at,
    updated_at
)
SELECT 
    6 as parent_id,
    'quickEntryManage' as name,
    '/miniprogram/quick-entry' as path,
    '/miniprogram/quickEntry/index' as component,
    '快捷入口配置' as title,
    'Grid' as icon,
    2 as sort_order,
    '' as is_link,
    0 as is_hide,
    0 as is_full,
    0 as is_affix,
    1 as is_keep_alive,
    1 as is_enabled,
    NOW() as created_at,
    NOW() as updated_at
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM menus WHERE name = 'quickEntryManage'
);

-- ============================================
-- 验证菜单创建结果
-- ============================================
-- 查询创建的菜单
SELECT 
    id,
    parent_id,
    name,
    path,
    component,
    title,
    icon,
    sort_order,
    is_enabled
FROM menus 
WHERE name = 'quickEntryManage';

-- ============================================
-- 执行完成
-- ============================================
-- 菜单已成功注册，刷新前端页面即可看到"小程序装修" -> "快捷入口配置"菜单项
-- 注意：如果parent_id=6不是"小程序装修"菜单，请先查询正确的parent_id：
-- SELECT id, name, title FROM menus WHERE name = 'app' OR title LIKE '%小程序%';





