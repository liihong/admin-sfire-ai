#!/bin/bash
# SFire Admin 自动化部署配置文件
# 请根据实际情况修改以下配置

# ==================== 服务器信息 ====================
# 服务器 IP 地址
SERVER_IP="172.26.215.41"
# 服务器用户名
SERVER_USER="root"
# 服务器密码（如果使用密码登录，建议使用 SSH 密钥更安全）
SERVER_PASSWORD="Sfire@2026"

# ==================== Git 仓库配置 ====================
# Git 仓库地址（支持 HTTPS 或 SSH）
GIT_REPO_URL="https://github.com/liihong/admin-sfire-ai.git"
# Git 分支（默认为 main 或 master）
GIT_BRANCH="main"
# 如果仓库是私有的，需要配置访问凭证
# 方式1: 使用 SSH 密钥（推荐）
# 方式2: 在 URL 中包含用户名和密码（不推荐，不安全）
# 方式3: 使用 GitHub/GitLab Personal Access Token

# ==================== 域名配置 ====================
# 主域名（例如: example.com）
DOMAIN="sourcefire.cn"
# 是否包含 www 子域名
INCLUDE_WWW=true

# ==================== 项目路径配置 ====================
# 项目部署路径
PROJECT_DIR="/var/www/sfire-admin"
# 后端目录
BACKEND_DIR="$PROJECT_DIR/backend"
# 前端目录
FRONTEND_DIR="$PROJECT_DIR/frontend"

# ==================== 数据库配置 ====================
# MySQL root 密码（首次安装 MySQL 时设置）
MYSQL_ROOT_PASSWORD="Sfire@2026"
# 数据库名称
MYSQL_DATABASE="sfire_admin"
# 数据库用户名（如果使用独立用户）
MYSQL_USER="sfire_admin"
# 数据库用户密码
MYSQL_PASSWORD="Sfire@2026"

# ==================== Redis 配置 ====================
# Redis 密码（留空表示不使用密码，不推荐）
REDIS_PASSWORD=""

# ==================== 后端配置 ====================
# 后端服务端口
BACKEND_PORT=8000
# 后端服务用户（推荐使用 www-data）
BACKEND_USER="www-data"
# JWT 密钥（留空将自动生成，建议手动设置强密码）
JWT_SECRET_KEY=""
# 应用密钥（留空将自动生成，建议手动设置强密码）
APP_SECRET_KEY=""

# ==================== 前端配置 ====================
# 前端构建输出目录
FRONTEND_DIST_DIR="/var/www/html/sfire-admin"

# ==================== SSL 证书配置 ====================
# 是否自动申请 SSL 证书（需要域名已解析）
AUTO_SSL=true
# SSL 证书邮箱（Let's Encrypt 需要）
SSL_EMAIL=""

# ==================== 防火墙配置 ====================
# 是否自动配置防火墙
AUTO_FIREWALL=true

# ==================== 其他配置 ====================
# 是否跳过环境安装（如果环境已安装，可以设置为 true）
SKIP_ENV_INSTALL=true
# 是否跳过数据库初始化（如果数据库已初始化，可以设置为 true）
SKIP_DB_INIT=true
# 日志级别（INFO, DEBUG, WARN, ERROR）
LOG_LEVEL="INFO"
