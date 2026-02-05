-- 创建管理员操作日志表
-- 执行前请备份数据库

-- 创建管理员操作日志表
CREATE TABLE admin_operation_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    admin_user_id BIGINT NOT NULL COMMENT '操作管理员ID',
    user_id BIGINT NOT NULL COMMENT '目标用户ID',
    operation_type VARCHAR(32) NOT NULL COMMENT '操作类型: recharge-充值, deduct-扣费, change_level-修改等级, change_status-修改状态, reset_password-重置密码',
    operation_detail TEXT NULL COMMENT '操作详情（JSON格式）',
    remark TEXT NULL COMMENT '备注说明',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX ix_admin_operation_logs_admin_user_id (admin_user_id),
    INDEX ix_admin_operation_logs_user_id (user_id),
    INDEX ix_admin_operation_logs_operation_type (operation_type),
    INDEX ix_admin_operation_logs_created_at (created_at),
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员操作日志表';



