#!/bin/bash
# SFire Admin 首次部署脚本
# 功能：一键完成从零到生产环境的完整部署
# 注意：此脚本仅用于首次部署，日常更新请使用 deploy/deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.sh"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

log_debug() {
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        log_error "此脚本需要 root 权限运行"
        log_info "请使用: sudo bash $0"
        exit 1
    fi
}

# 加载配置文件
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        log_info "请先创建并配置 $CONFIG_FILE"
        exit 1
    fi
    
    log_info "加载配置文件: $CONFIG_FILE"
    source "$CONFIG_FILE"
    
    # 验证必要配置
    if [ -z "$GIT_REPO_URL" ]; then
        log_error "请配置 GIT_REPO_URL"
        exit 1
    fi
    
    if [ -z "$DOMAIN" ] && [ "$AUTO_SSL" = "true" ]; then
        log_error "启用 SSL 需要配置 DOMAIN"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    log_step "检测操作系统"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(lsb_release -sr)
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi
    
    log_info "操作系统: $OS $OS_VERSION"
    
    case $OS in
        ubuntu|debian)
            OS_TYPE="debian"
            PKG_MANAGER="apt"
            ;;
        centos|rhel|fedora)
            OS_TYPE="rhel"
            PKG_MANAGER="yum"
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
}

# 更新系统包
update_system() {
    log_step "更新系统包"
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt update && apt upgrade -y
    else
        yum update -y
    fi
}

# 安装基础工具
install_basic_tools() {
    log_step "安装基础工具"
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt install -y git curl wget vim build-essential software-properties-common
    else
        yum install -y git curl wget vim gcc gcc-c++ make
    fi
}

# 安装 Python
install_python() {
    log_step "安装 Python 3.12+"
    
    if command -v python3.12 &> /dev/null; then
        log_info "Python 3.12 已安装"
        return
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        # Ubuntu/Debian
        add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
        apt update
        apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
    else
        # CentOS/RHEL
        yum install -y python312 python312-pip python312-devel
    fi
    
    # 创建 python3.12 的软链接（如果不存在）
    if [ ! -f /usr/bin/python3.12 ]; then
        log_warn "Python 3.12 可能未正确安装，请手动检查"
    fi
}

# 安装 Node.js
install_nodejs() {
    log_step "安装 Node.js 18+"
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            log_info "Node.js 已安装: $(node -v)"
            return
        fi
    fi
    
    # 使用 NodeSource 安装
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt install -y nodejs
    else
        yum install -y nodejs
    fi
    
    # 安装 pnpm
    if ! command -v pnpm &> /dev/null; then
        log_info "安装 pnpm"
        npm install -g pnpm
    fi
}

# 安装 Redis
install_redis() {
    log_step "安装 Redis"
    
    if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet redis-server 2>/dev/null; then
        log_info "Redis 已安装并运行"
        return
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt install -y redis-server
        systemctl start redis-server
        systemctl enable redis-server
    else
        yum install -y redis
        systemctl start redis
        systemctl enable redis
    fi
    
    # 配置 Redis 密码
    if [ -n "$REDIS_PASSWORD" ]; then
        log_info "配置 Redis 密码"
        REDIS_CONF="/etc/redis/redis.conf"
        if [ -f "$REDIS_CONF" ]; then
            # 检查是否已有密码配置
            if grep -q "^requirepass" "$REDIS_CONF"; then
                sed -i "s/^requirepass.*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
            else
                # 如果使用注释的密码行，取消注释并修改
                if grep -q "^# requirepass" "$REDIS_CONF"; then
                    sed -i "s/^# requirepass.*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
                else
                    # 添加新的密码配置
                    echo "requirepass $REDIS_PASSWORD" >> "$REDIS_CONF"
                fi
            fi
            systemctl restart redis-server 2>/dev/null || systemctl restart redis
        else
            log_warn "Redis 配置文件不存在: $REDIS_CONF"
        fi
    fi
}

# 安装 Nginx
install_nginx() {
    log_step "安装 Nginx"
    
    if systemctl is-active --quiet nginx 2>/dev/null; then
        log_info "Nginx 已安装并运行"
        return
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt install -y nginx
    else
        yum install -y nginx
    fi
    
    systemctl start nginx
    systemctl enable nginx
}

# 安装 Certbot
install_certbot() {
    log_step "安装 Certbot"
    
    if command -v certbot &> /dev/null; then
        log_info "Certbot 已安装"
        return
    fi
    
    if [ "$OS_TYPE" = "debian" ]; then
        apt install -y certbot python3-certbot-nginx
    else
        yum install -y certbot python3-certbot-nginx
    fi
}

# 配置防火墙
configure_firewall() {
    if [ "$AUTO_FIREWALL" != "true" ]; then
        return
    fi
    
    log_step "配置防火墙"
    
    if [ "$OS_TYPE" = "debian" ]; then
        # UFW
        if command -v ufw &> /dev/null; then
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            echo "y" | ufw enable 2>/dev/null || true
            log_info "UFW 防火墙已配置"
        fi
    else
        # firewalld
        if systemctl is-active --quiet firewalld 2>/dev/null; then
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --reload
            log_info "firewalld 防火墙已配置"
        fi
    fi
    
    log_warn "请确保阿里云安全组已开放 22, 80, 443 端口"
}

# 克隆项目
clone_project() {
    log_step "克隆项目代码"
    
    if [ -d "$PROJECT_DIR" ]; then
        log_warn "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除并重新克隆? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            log_info "跳过克隆，使用现有项目"
            return
        fi
    fi
    
    mkdir -p "$(dirname $PROJECT_DIR)"
    
    log_info "克隆仓库: $GIT_REPO_URL (分支: $GIT_BRANCH)"
    git clone -b "$GIT_BRANCH" "$GIT_REPO_URL" "$PROJECT_DIR" || {
        log_error "克隆失败，请检查 Git 仓库地址和权限"
        exit 1
    }
    
    log_info "项目克隆完成"
}

# 配置后端
setup_backend() {
    log_step "配置后端服务"
    
    cd "$BACKEND_DIR"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建 Python 虚拟环境"
        python3.12 -m venv venv
    fi
    
    # 安装依赖
    log_info "安装 Python 依赖"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 配置环境变量
    if [ ! -f ".env" ]; then
        log_info "配置环境变量"
        cp env.example .env
        
        # 生成随机密钥（如果未配置）
        if [ -z "$JWT_SECRET_KEY" ]; then
            JWT_SECRET_KEY=$(openssl rand -hex 32)
        fi
        if [ -z "$APP_SECRET_KEY" ]; then
            APP_SECRET_KEY=$(openssl rand -hex 32)
        fi
        
        # 更新 .env 文件
        sed -i "s|APP_ENV=development|APP_ENV=production|" .env
        sed -i "s|DEBUG=true|DEBUG=false|" .env
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$APP_SECRET_KEY|" .env
        sed -i "s|HOST=.*|HOST=127.0.0.1|" .env
        sed -i "s|PORT=.*|PORT=$BACKEND_PORT|" .env
        
        if [ -n "$MYSQL_PASSWORD" ]; then
            sed -i "s|MYSQL_HOST=.*|MYSQL_HOST=localhost|" .env
            sed -i "s|MYSQL_PORT=.*|MYSQL_PORT=3306|" .env
            sed -i "s|MYSQL_USER=.*|MYSQL_USER=$MYSQL_USER|" .env
            sed -i "s|MYSQL_PASSWORD=.*|MYSQL_PASSWORD=$MYSQL_PASSWORD|" .env
            sed -i "s|MYSQL_DATABASE=.*|MYSQL_DATABASE=$MYSQL_DATABASE|" .env
        fi
        
        if [ -n "$REDIS_PASSWORD" ]; then
            sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|" .env
        fi
        
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET_KEY|" .env
        
        # 配置 CORS
        if [ -n "$DOMAIN" ]; then
            CORS_ORIGINS="[\"https://$DOMAIN\""
            if [ "$INCLUDE_WWW" = "true" ]; then
                CORS_ORIGINS="$CORS_ORIGINS,\"https://www.$DOMAIN\""
            fi
            CORS_ORIGINS="$CORS_ORIGINS]"
            sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=$CORS_ORIGINS|" .env
        fi
        
        log_info "环境变量已配置，请检查 .env 文件"
    else
        log_warn ".env 文件已存在，检查并更新 MySQL 配置"
        
        # 即使 .env 文件存在，也更新 MySQL 配置以确保正确
        if [ -n "$MYSQL_PASSWORD" ]; then
            # 如果配置项不存在，添加它们
            if ! grep -q "^MYSQL_HOST=" .env; then
                echo "MYSQL_HOST=localhost" >> .env
            else
                sed -i "s|^MYSQL_HOST=.*|MYSQL_HOST=localhost|" .env
            fi
            
            if ! grep -q "^MYSQL_PORT=" .env; then
                echo "MYSQL_PORT=3306" >> .env
            else
                sed -i "s|^MYSQL_PORT=.*|MYSQL_PORT=3306|" .env
            fi
            
            if ! grep -q "^MYSQL_USER=" .env; then
                echo "MYSQL_USER=$MYSQL_USER" >> .env
            else
                sed -i "s|^MYSQL_USER=.*|MYSQL_USER=$MYSQL_USER|" .env
            fi
            
            if ! grep -q "^MYSQL_PASSWORD=" .env; then
                echo "MYSQL_PASSWORD=$MYSQL_PASSWORD" >> .env
            else
                sed -i "s|^MYSQL_PASSWORD=.*|MYSQL_PASSWORD=$MYSQL_PASSWORD|" .env
            fi
            
            if ! grep -q "^MYSQL_DATABASE=" .env; then
                echo "MYSQL_DATABASE=$MYSQL_DATABASE" >> .env
            else
                sed -i "s|^MYSQL_DATABASE=.*|MYSQL_DATABASE=$MYSQL_DATABASE|" .env
            fi
            
            log_info "已更新 .env 文件中的 MySQL 配置"
        fi
    fi
}

# 配置前端
setup_frontend() {
    log_step "配置前端服务"
    
    cd "$FRONTEND_DIR"
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装 Node.js 依赖"
        pnpm install
    fi
    
    # 配置生产环境变量
    if [ ! -f ".env.production" ]; then
        log_info "配置生产环境变量"
        if [ -f ".env.production.example" ]; then
            cp .env.production.example .env.production
        else
            cat > .env.production <<EOF
VITE_PORT=5173
VITE_PUBLIC_PATH=/
VITE_API_URL=/api
VITE_PROXY=[["/api","http://127.0.0.1:$BACKEND_PORT"]]
VITE_DROP_CONSOLE=true
VITE_GLOB_APP_TITLE=SFire Admin
VITE_ROUTER_MODE=history
EOF
        fi
        
        # 更新 API 地址
        if [ -n "$DOMAIN" ]; then
            sed -i "s|VITE_API_URL=.*|VITE_API_URL=/api|" .env.production
        fi
    fi
    
    # 构建项目
    log_info "构建前端项目"
    pnpm build:pro
    
    # 部署到 Nginx 目录
    log_info "部署前端文件"
    mkdir -p "$FRONTEND_DIST_DIR"
    cp -r dist/* "$FRONTEND_DIST_DIR/"
    chown -R www-data:www-data "$FRONTEND_DIST_DIR"
}

# 配置 systemd 服务
setup_systemd_service() {
    log_step "配置 systemd 服务"
    
    SERVICE_FILE="/etc/systemd/system/sfire-admin-api.service"
    
    # 复制服务文件
    if [ -f "$SCRIPT_DIR/sfire-admin-api.service" ]; then
        cp "$SCRIPT_DIR/sfire-admin-api.service" "$SERVICE_FILE"
        
        # 替换路径
        sed -i "s|/var/www/sfire-admin/backend|$BACKEND_DIR|g" "$SERVICE_FILE"
        sed -i "s|User=.*|User=$BACKEND_USER|" "$SERVICE_FILE"
        sed -i "s|Group=.*|Group=$BACKEND_USER|" "$SERVICE_FILE"
        
        # 重新加载 systemd
        systemctl daemon-reload
        systemctl enable sfire-admin-api
        systemctl start sfire-admin-api
        
        # 检查服务状态
        sleep 2
        if systemctl is-active --quiet sfire-admin-api; then
            log_info "后端服务启动成功"
        else
            log_error "后端服务启动失败"
            log_info "查看日志: journalctl -u sfire-admin-api -f"
            exit 1
        fi
    else
        log_error "未找到 systemd 服务文件"
        exit 1
    fi
}

# 配置 Nginx
setup_nginx() {
    log_step "配置 Nginx"
    
    NGINX_CONF="/etc/nginx/sites-available/sfire-admin"
    
    if [ -f "$SCRIPT_DIR/nginx.conf" ]; then
        cp "$SCRIPT_DIR/nginx.conf" "$NGINX_CONF"
        
        # 替换配置
        if [ -n "$DOMAIN" ]; then
            sed -i "s/your-domain.com/$DOMAIN/g" "$NGINX_CONF"
            if [ "$INCLUDE_WWW" = "true" ]; then
                sed -i "s/www.your-domain.com/www.$DOMAIN/g" "$NGINX_CONF"
            else
                # 移除 www 配置
                sed -i "/www\.$DOMAIN/d" "$NGINX_CONF"
            fi
        else
            # 使用 IP 访问，简化配置
            sed -i "s/server_name.*/server_name $SERVER_IP;/" "$NGINX_CONF"
            # 注释掉 SSL 相关配置
            sed -i "s/^ssl_/### ssl_/" "$NGINX_CONF"
            sed -i "s/listen 443/listen 80/" "$NGINX_CONF"
        fi
        
        # 替换路径
        sed -i "s|/var/www/html/sfire-admin|$FRONTEND_DIST_DIR|g" "$NGINX_CONF"
        sed -i "s|127.0.0.1:8000|127.0.0.1:$BACKEND_PORT|g" "$NGINX_CONF"
        
        # 启用配置
        ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/sfire-admin
        
        # 测试配置
        if nginx -t; then
            systemctl reload nginx
            log_info "Nginx 配置完成"
        else
            log_error "Nginx 配置有误"
            exit 1
        fi
    else
        log_error "未找到 Nginx 配置文件"
        exit 1
    fi
}

# 申请 SSL 证书
setup_ssl() {
    if [ "$AUTO_SSL" != "true" ] || [ -z "$DOMAIN" ]; then
        return
    fi
    
    log_step "申请 SSL 证书"
    
    if [ -z "$SSL_EMAIL" ]; then
        log_warn "未配置 SSL_EMAIL，使用默认邮箱"
        SSL_EMAIL="admin@$DOMAIN"
    fi
    
    # 确保域名可以访问
    log_info "等待域名解析生效..."
    sleep 5
    
    # 申请证书
    CERTBOT_DOMAINS="-d $DOMAIN"
    if [ "$INCLUDE_WWW" = "true" ]; then
        CERTBOT_DOMAINS="$CERTBOT_DOMAINS -d www.$DOMAIN"
    fi
    
    certbot --nginx --non-interactive --agree-tos --email "$SSL_EMAIL" $CERTBOT_DOMAINS || {
        log_warn "SSL 证书申请失败，请稍后手动申请"
        log_info "手动申请命令: certbot --nginx -d $DOMAIN"
    }
}

# 主函数
main() {
    log_step "SFire Admin 自动化部署开始"
    
    # 检查 root 权限
    check_root
    
    # 加载配置
    load_config
    
    # 检测操作系统
    detect_os
    
    # 安装环境（如果未跳过）
    if [ "$SKIP_ENV_INSTALL" != "true" ]; then
        update_system
        install_basic_tools
        install_python
        install_nodejs
        install_redis
        install_nginx
        install_certbot
        configure_firewall
    else
        log_info "跳过环境安装"
    fi
    
    # 部署项目
    clone_project
    setup_backend
    setup_frontend
    
    # 配置服务
    setup_systemd_service
    setup_nginx
    
    # 申请 SSL
    setup_ssl
    
    # 完成
    log_step "部署完成"
    echo ""
    log_info "部署信息:"
    echo "  项目路径: $PROJECT_DIR"
    echo "  后端服务: http://127.0.0.1:$BACKEND_PORT"
    if [ -n "$DOMAIN" ]; then
        echo "  访问地址: https://$DOMAIN"
    else
        echo "  访问地址: http://$SERVER_IP"
    fi
    echo ""
    log_info "服务管理:"
    echo "  后端服务: systemctl status sfire-admin-api"
    echo "  Nginx: systemctl status nginx"
    echo ""
    log_info "查看日志:"
    echo "  后端日志: journalctl -u sfire-admin-api -f"
    echo "  Nginx 日志: tail -f /var/log/nginx/sfire-admin-error.log"
    echo ""
    log_warn "重要提醒:"
    echo "  1. 请检查后端 .env 文件，确保所有配置正确"
    echo "  2. 请检查前端 .env.production 文件"
    echo "  3. 确保阿里云安全组已开放 22, 80, 443 端口"
    echo "  4. 如果使用域名，确保 DNS 解析已生效"
    echo ""
}

# 运行主函数
main "$@"

