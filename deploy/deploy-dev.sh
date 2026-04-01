#!/bin/bash

# SFire Admin 开发环境更新部署脚本
# 与生产 deploy.sh 类似，但使用独立目录、端口与 systemd 服务，便于在服务器上调试。
#
# 使用方法:
#   sudo bash deploy/deploy-dev.sh [backend|frontend|frontend-static|all] [--no-pull]
#
# 首次部署前请:
#   1. 将仓库 clone 到 PROJECT_DIR_DEV（默认 /var/www/sfire-admin-dev）
#   2. cp deploy/config.dev.sh.example deploy/config.dev.sh 并修改路径/分支/端口
#   3. 配置 backend/.env（建议 DEBUG=true，PORT 与 BACKEND_PORT_DEV 一致，如 8001）
#   4. 配置 frontend/.env.development（VITE_PROXY 指向本机 dev API，如 http://127.0.0.1:8001）
#   5. 安装 systemd 单元（路径需与单元文件一致，或先编辑单元内路径）:
#        sudo cp deploy/sfire-admin-api-dev.service /etc/systemd/system/
#        sudo cp deploy/sfire-admin-frontend-dev.service /etc/systemd/system/
#        sudo systemctl daemon-reload
#        sudo systemctl enable --now sfire-admin-api-dev
#        sudo systemctl enable --now sfire-admin-frontend-dev   # 若使用 frontend 模式
#   6. 为 www-data 配置可用的 node/pnpm（或把单元中 User 改为你的部署用户）

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DEV_FILE="${SCRIPT_DIR}/config.dev.sh"

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

load_config_dev() {
    if [ ! -f "${CONFIG_DEV_FILE}" ]; then
        log_error "开发环境配置不存在: ${CONFIG_DEV_FILE}"
        log_info "请执行: cp ${SCRIPT_DIR}/config.dev.sh.example ${CONFIG_DEV_FILE} 并编辑"
        exit 1
    fi

    log_info "加载配置: ${CONFIG_DEV_FILE}"
    # shellcheck source=/dev/null
    source "${CONFIG_DEV_FILE}"

    PROJECT_DIR_DEV="${PROJECT_DIR_DEV:-/var/www/sfire-admin-dev}"
    BACKEND_DIR_DEV="${BACKEND_DIR_DEV:-${PROJECT_DIR_DEV}/backend}"
    FRONTEND_DIR_DEV="${FRONTEND_DIR_DEV:-${PROJECT_DIR_DEV}/frontend}"
    FRONTEND_DIST_DIR_DEV="${FRONTEND_DIST_DIR_DEV:-/var/www/html/sfire-admin-dev}"
    GIT_BRANCH_DEV="${GIT_BRANCH_DEV:-develop}"
    SERVICE_NAME_BACKEND_DEV="${SERVICE_NAME_BACKEND_DEV:-sfire-admin-api-dev}"
    SERVICE_NAME_FRONTEND_DEV="${SERVICE_NAME_FRONTEND_DEV:-sfire-admin-frontend-dev}"
    BACKEND_PORT_DEV="${BACKEND_PORT_DEV:-8001}"
}

require_systemd_unit() {
    local unit="$1"
    if [ ! -f "/etc/systemd/system/${unit}.service" ] && [ ! -f "/lib/systemd/system/${unit}.service" ]; then
        log_warn "未找到 ${unit}.service，请先复制到 /etc/systemd/system/ 并执行 systemctl daemon-reload"
    fi
}

pull_code_dev() {
    log_step "拉取最新代码（开发分支）"

    if [ ! -d "${PROJECT_DIR_DEV}" ]; then
        log_error "项目目录不存在: ${PROJECT_DIR_DEV}"
        exit 1
    fi

    cd "${PROJECT_DIR_DEV}"

    if [ ! -d ".git" ]; then
        log_error "不是 Git 仓库，无法拉取代码"
        exit 1
    fi

    log_info "目标分支: ${GIT_BRANCH_DEV}"
    log_info "当前分支: $(git branch --show-current)"

    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_warn "检测到未提交的更改，正在暂存..."
        git stash push -m "deploy-dev-stash-$(date +%s)" || true
    fi

    git fetch origin
    git checkout "${GIT_BRANCH_DEV}"
    git pull origin "${GIT_BRANCH_DEV}" || {
        log_error "拉取代码失败"
        exit 1
    }

    log_info "代码更新完成"
}

deploy_backend_dev() {
    log_step "部署后端（开发）"

    require_systemd_unit "${SERVICE_NAME_BACKEND_DEV}"

    cd "${BACKEND_DIR_DEV}"

    if [ ! -d "venv" ]; then
        log_warn "虚拟环境不存在，正在创建..."
        python3.12 -m venv venv
    fi

    log_info "更新依赖..."
    # shellcheck source=/dev/null
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    if [ ! -f ".env" ]; then
        log_error ".env 不存在，请先配置（建议 DEBUG=true，PORT=${BACKEND_PORT_DEV}）"
        exit 1
    fi

    log_info "重启后端开发服务..."
    systemctl daemon-reload
    systemctl restart "${SERVICE_NAME_BACKEND_DEV}"

    sleep 2

    if systemctl is-active --quiet "${SERVICE_NAME_BACKEND_DEV}"; then
        log_info "后端开发服务运行中（${SERVICE_NAME_BACKEND_DEV}）"
    else
        log_error "后端开发服务启动失败"
        log_info "查看日志: journalctl -u ${SERVICE_NAME_BACKEND_DEV} -f"
        exit 1
    fi
}

deploy_frontend_vite_dev() {
    log_step "部署前端（Vite 开发服务）"

    require_systemd_unit "${SERVICE_NAME_FRONTEND_DEV}"

    cd "${FRONTEND_DIR_DEV}"

    if [ ! -d "node_modules" ]; then
        log_warn "node_modules 不存在，正在安装依赖..."
        pnpm install
    else
        log_info "更新依赖..."
        pnpm install
    fi

    if [ ! -f ".env.development" ]; then
        log_error ".env.development 不存在，请先配置（含 VITE_PROXY 指向 127.0.0.1:${BACKEND_PORT_DEV}）"
        exit 1
    fi

    log_info "重启 Vite 开发服务..."
    systemctl daemon-reload
    systemctl restart "${SERVICE_NAME_FRONTEND_DEV}"

    sleep 2

    if systemctl is-active --quiet "${SERVICE_NAME_FRONTEND_DEV}"; then
        log_info "前端开发服务运行中（${SERVICE_NAME_FRONTEND_DEV}）"
    else
        log_error "前端开发服务启动失败"
        log_info "查看日志: journalctl -u ${SERVICE_NAME_FRONTEND_DEV} -f"
        exit 1
    fi
}

deploy_frontend_static_dev() {
    log_step "部署前端（development 构建 + 静态目录）"

    cd "${FRONTEND_DIR_DEV}"

    if [ ! -d "node_modules" ]; then
        pnpm install
    else
        pnpm install
    fi

    if [ ! -f ".env.development" ]; then
        log_error ".env.development 不存在，请先配置"
        exit 1
    fi

    log_info "构建（development）..."
    if ! pnpm build:dev; then
        log_error "前端构建失败"
        exit 1
    fi

    log_info "同步到 ${FRONTEND_DIST_DIR_DEV} ..."
    mkdir -p "${FRONTEND_DIST_DIR_DEV}"
    cp -r dist/* "${FRONTEND_DIST_DIR_DEV}/"
    chown -R www-data:www-data "${FRONTEND_DIST_DIR_DEV}"

    log_info "重新加载 Nginx..."
    if nginx -t; then
        systemctl reload nginx
        log_info "静态开发构建部署完成"
    else
        log_error "Nginx 配置有误"
        exit 1
    fi
}

main() {
    local target="all"
    local do_pull=1

    while [ $# -gt 0 ]; do
        case "$1" in
            --no-pull)
                do_pull=0
                shift
                ;;
            backend|frontend|frontend-static|all)
                target="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                echo "用法: $0 [backend|frontend|frontend-static|all] [--no-pull]"
                exit 1
                ;;
        esac
    done

    log_step "SFire Admin 开发环境部署"

    load_config_dev

    if [ "${do_pull}" -eq 1 ]; then
        pull_code_dev
    else
        log_info "跳过代码拉取（--no-pull）"
    fi

    case "${target}" in
        backend)
            deploy_backend_dev
            ;;
        frontend)
            deploy_frontend_vite_dev
            ;;
        frontend-static)
            deploy_frontend_static_dev
            ;;
        all)
            deploy_backend_dev
            deploy_frontend_vite_dev
            ;;
        *)
            log_error "未知部署目标: ${target}"
            echo "用法: $0 [backend|frontend|frontend-static|all] [--no-pull]"
            echo ""
            echo "  backend           仅后端（reload systemd）"
            echo "  frontend          Vite 开发服务（systemd）"
            echo "  frontend-static   pnpm build:dev 输出到 FRONTEND_DIST_DIR_DEV"
            echo "  all               后端 + Vite（默认）"
            echo "  --no-pull         不执行 git pull"
            exit 1
            ;;
    esac

    log_step "开发环境部署完成"
    echo ""
    log_info "常用命令:"
    echo "  journalctl -u ${SERVICE_NAME_BACKEND_DEV} -f"
    echo "  journalctl -u ${SERVICE_NAME_FRONTEND_DEV} -f"
    echo ""
}

main "$@"
