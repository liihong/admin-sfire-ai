#!/bin/bash

# SFire Admin 更新部署脚本
# 使用方法: bash deploy/deploy.sh [backend|frontend|all]
# 功能：拉取最新代码、更新依赖、重新构建、重启服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"

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

# 加载配置文件
load_config() {
    if [ ! -f "${CONFIG_FILE}" ]; then
        log_error "配置文件不存在: ${CONFIG_FILE}"
        log_info "请先创建并配置 ${CONFIG_FILE}"
        exit 1
    fi
    
    log_info "加载配置文件: ${CONFIG_FILE}"
    source "${CONFIG_FILE}"
    
    # 设置变量
    PROJECT_DIR="${PROJECT_DIR:-/var/www/sfire-admin}"
    BACKEND_DIR="${BACKEND_DIR:-${PROJECT_DIR}/backend}"
    FRONTEND_DIR="${FRONTEND_DIR:-${PROJECT_DIR}/frontend}"
    FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-/var/www/html/sfire-admin}"
    SERVICE_NAME="sfire-admin-api"
    GIT_BRANCH="${GIT_BRANCH:-main}"
}

# 拉取最新代码
pull_code() {
    log_step "拉取最新代码"
    
    if [ ! -d "${PROJECT_DIR}" ]; then
        log_error "项目目录不存在: ${PROJECT_DIR}"
        exit 1
    fi
    
    cd "${PROJECT_DIR}"
    
    # 检查是否为 git 仓库
    if [ ! -d ".git" ]; then
        log_error "不是 Git 仓库，无法拉取代码"
        exit 1
    fi
    
    log_info "当前分支: $(git branch --show-current)"
    log_info "拉取最新代码..."
    
    # 保存当前更改（如果有）
    if ! git diff-index --quiet HEAD --; then
        log_warn "检测到未提交的更改，正在暂存..."
        git stash
    fi
    
    # 拉取最新代码
    git fetch origin
    git checkout "${GIT_BRANCH}"
    git pull origin "${GIT_BRANCH}" || {
        log_error "拉取代码失败"
        exit 1
    }
    
    log_info "代码更新完成"
}

# 部署后端
deploy_backend() {
    log_step "部署后端服务"
    
    cd "${BACKEND_DIR}"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_warn "虚拟环境不存在，正在创建..."
        python3.12 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    log_info "更新依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在，请先配置环境变量"
        exit 1
    fi
    
    # 重启服务
    log_info "重启服务..."
    systemctl daemon-reload
    systemctl restart "${SERVICE_NAME}"
    
    # 等待服务启动
    sleep 2
    
    # 检查服务状态
    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        log_info "后端服务启动成功"
    else
        log_error "后端服务启动失败"
        log_info "查看日志: journalctl -u ${SERVICE_NAME} -f"
        exit 1
    fi
}

# 部署前端
deploy_frontend() {
    log_step "部署前端服务"
    
    cd "${FRONTEND_DIR}"
    
    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        log_warn "node_modules 不存在，正在安装依赖..."
        pnpm install
    else
        log_info "更新依赖..."
        pnpm install
    fi
    
    # 检查 .env.production
    if [ ! -f ".env.production" ]; then
        log_error ".env.production 文件不存在，请先配置"
        exit 1
    fi
    
    # 构建项目
    log_info "构建前端项目..."
    if ! pnpm build:pro; then
        log_error "前端构建失败"
        exit 1
    fi
    
    # 复制到 Nginx 目录
    log_info "部署前端文件到 Nginx 目录..."
    mkdir -p "${FRONTEND_DIST_DIR}"
    cp -r dist/* "${FRONTEND_DIST_DIR}/"
    
    # 设置权限
    chown -R www-data:www-data "${FRONTEND_DIST_DIR}"
    
    # 重新加载 Nginx
    log_info "重新加载 Nginx..."
    if nginx -t; then
        systemctl reload nginx
        log_info "前端部署完成"
    else
        log_error "Nginx 配置有误，请检查"
        exit 1
    fi
}

# 主函数
main() {
    local target="${1:-all}"
    
    log_step "SFire Admin 更新部署"
    
    # 加载配置
    load_config
    
    # 拉取最新代码（除非指定不拉取）
    if [ "${2}" != "--no-pull" ]; then
        pull_code
    else
        log_info "跳过代码拉取（使用 --no-pull 参数）"
    fi
    
    # 根据参数部署
    case "${target}" in
        backend)
            deploy_backend
            ;;
        frontend)
            deploy_frontend
            ;;
        all)
            deploy_backend
            deploy_frontend
            ;;
        *)
            log_error "未知参数: ${target}"
            echo "使用方法: $0 [backend|frontend|all] [--no-pull]"
            echo ""
            echo "参数说明:"
            echo "  backend    - 仅部署后端"
            echo "  frontend   - 仅部署前端"
            echo "  all        - 部署前后端（默认）"
            echo "  --no-pull  - 不拉取最新代码"
            exit 1
            ;;
    esac
    
    log_step "部署完成"
    echo ""
    log_info "服务状态:"
    echo "  后端服务: systemctl status ${SERVICE_NAME}"
    echo "  Nginx: systemctl status nginx"
    echo ""
    log_info "查看日志:"
    echo "  后端日志: journalctl -u ${SERVICE_NAME} -f"
    echo "  Nginx 日志: tail -f /var/log/nginx/sfire-admin-error.log"
    echo ""
}

# 运行主函数
main "$@"
