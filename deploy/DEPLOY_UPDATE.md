# 更新部署指南

## 概述

`deploy.sh` 是用于日常更新部署的脚本，适用于已经完成首次部署的环境。

## 功能

- ✅ 自动拉取最新代码
- ✅ 更新后端依赖
- ✅ 重新构建前端
- ✅ 重启服务
- ✅ 支持单独部署前端或后端

## 使用方法

### 基本用法

```bash
# 部署前后端（默认）
sudo bash deploy/deploy.sh

# 或明确指定 all
sudo bash deploy/deploy.sh all
```

### 单独部署

```bash
# 仅部署后端
sudo bash deploy/deploy.sh backend

# 仅部署前端
sudo bash deploy/deploy.sh frontend
```

### 不拉取代码

如果代码已经是最新的，可以跳过拉取步骤：

```bash
# 不拉取代码，直接部署
sudo bash deploy/deploy.sh all --no-pull
```

## 配置要求

脚本会自动读取 `deploy/config.sh` 配置文件，确保以下配置正确：

- `PROJECT_DIR` - 项目目录路径
- `BACKEND_DIR` - 后端目录路径
- `FRONTEND_DIR` - 前端目录路径
- `FRONTEND_DIST_DIR` - 前端部署目录
- `GIT_BRANCH` - Git 分支（默认 main）

## 部署流程

1. **拉取最新代码** - 从 Git 仓库拉取指定分支的最新代码
2. **部署后端**
   - 更新 Python 依赖
   - 重启 systemd 服务
3. **部署前端**
   - 更新 Node.js 依赖
   - 重新构建前端项目
   - 复制文件到 Nginx 目录
   - 重新加载 Nginx

## 注意事项

1. 需要 root 权限运行（使用 sudo）
2. 确保 `.env` 和 `.env.production` 文件已正确配置
3. 如果拉取代码时有冲突，脚本会自动暂存本地更改
4. 部署失败时会显示详细的错误信息

## 故障排查

### 后端服务启动失败

```bash
# 查看服务状态
systemctl status sfire-admin-api

# 查看日志
journalctl -u sfire-admin-api -f
```

### 前端构建失败

```bash
# 进入前端目录手动构建
cd /var/www/sfire-admin/frontend
pnpm build:pro
```

### Nginx 配置错误

```bash
# 测试配置
nginx -t

# 查看错误日志
tail -f /var/log/nginx/sfire-admin-error.log
```

## 与首次部署脚本的区别

- `auto-deploy.sh` - 首次部署脚本，包含环境安装、系统配置等
- `deploy.sh` - 更新部署脚本，仅用于代码更新和服务重启

首次部署完成后，日常更新请使用 `deploy.sh`。



























