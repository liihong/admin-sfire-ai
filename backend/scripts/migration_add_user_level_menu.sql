-- 用户等级管理菜单注册SQL
-- 执行前请备份数据库
-- 说明：将用户等级管理页面注册到菜单系统中

-- ============================================
-- 第一步：查询或创建"系统管理"父菜单
-- ============================================
-- 如果不存在"系统管理"父菜单，则创建
INSERT INTO menus (
    parent_id,
    name,
    path,
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
    NULL as parent_id,
    'system' as name,
    '/system' as path,
    '系统管理' as title,
    'Setting' as icon,
    10 as sort_order,
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
    SELECT 1 FROM menus WHERE name = 'system'
);

-- ============================================
-- 第二步：创建"用户等级管理"子菜单
-- ============================================
-- 获取"系统管理"父菜单的ID
SET @system_menu_id = (SELECT id FROM menus WHERE name = 'system' LIMIT 1);

-- 插入用户等级管理菜单（如果不存在）
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
    @system_menu_id as parent_id,
    'userLevelManage' as name,
    '/system/user-level-manage' as path,
    '/system/userLevelManage/index' as component,
    '用户等级管理' as title,
    'UserFilled' as icon,
    1 as sort_order,
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
    SELECT 1 FROM menus WHERE name = 'userLevelManage'
);

-- ============================================
-- 第三步：验证菜单创建结果
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
WHERE name IN ('system', 'userLevelManage')
ORDER BY parent_id IS NULL DESC, sort_order;

-- ============================================
-- 执行完成
-- ============================================
-- 菜单已成功注册，刷新前端页面即可看到"系统管理" -> "用户等级管理"菜单项







