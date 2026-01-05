# 部署文件说明

本目录包含 SFire Admin 系统部署所需的所有配置文件。

## 📁 文件说明

### 配置文件

- **nginx.conf** - Nginx 反向代理配置文件
  - 配置前端静态文件服务
  - 配置后端 API 反向代理
  - 包含 HTTPS/SSL 配置示例

- **sfire-admin-api.service** - Systemd 服务文件
  - 用于管理后端 API 服务
  - 支持自动重启和日志管理

- **supervisor.conf** - Supervisor 配置文件（备选方案）
  - 如果不想使用 systemd，可以使用 Supervisor
  - 需要单独安装 Supervisor: `sudo apt install supervisor`

### 部署脚本

- **auto-deploy.sh** - 首次部署脚本（仅首次使用）
  - 一键完成从零到生产环境的完整部署
  - 自动安装所有环境依赖
  - 自动配置所有服务
  - 支持 SSL 证书自动申请
  - **注意：仅用于首次部署，日常更新请使用 deploy.sh**
  - 使用方法: `bash deploy/auto-deploy.sh`
  - 详细说明: [AUTO_DEPLOY_README.md](AUTO_DEPLOY_README.md)
  - 快速开始: [QUICK_START.md](QUICK_START.md)

- **deploy.sh** - 更新部署脚本（日常使用）⭐
  - 自动拉取最新代码
  - 支持单独部署后端或前端
  - 适用于日常更新部署
  - 使用方法: `sudo bash deploy/deploy.sh [backend|frontend|all]`
  - 详细说明: [DEPLOY_UPDATE.md](DEPLOY_UPDATE.md)

- **quick-deploy.sh** - 快速部署脚本（交互式）
  - 适用于首次部署
  - 交互式配置，引导完成部署
  - 使用方法: `bash deploy/quick-deploy.sh`

## 🚀 快速开始

### 方式一：使用全自动部署脚本（最推荐）⭐

```bash
# 1. 编辑配置文件
vim deploy/config.sh

# 2. 运行全自动部署脚本
bash deploy/auto-deploy.sh
```

**优势：**
- 完全自动化，无需手动干预
- 自动安装所有环境依赖
- 自动配置所有服务
- 支持 SSL 证书自动申请

详细说明请参考：[AUTO_DEPLOY_README.md](AUTO_DEPLOY_README.md)

### 方式二：使用快速部署脚本（交互式）

```bash
# 1. 上传项目到服务器
# 2. 进入项目目录
cd /var/www/sfire-admin

# 3. 运行快速部署脚本
bash deploy/quick-deploy.sh
```

脚本会引导你完成：
- 系统环境检查
- 后端配置和部署
- 前端配置和构建
- Nginx 配置

### 方式三：手动部署

#### 1. 部署后端

```bash
# 进入后端目录
cd /var/www/sfire-admin/backend

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
vim .env  # 编辑配置

# 初始化数据库
python scripts/init_db.py

# 配置 systemd 服务
sudo cp deploy/sfire-admin-api.service /etc/systemd/system/
sudo vim /etc/systemd/system/sfire-admin-api.service  # 修改路径
sudo systemctl daemon-reload
sudo systemctl enable sfire-admin-api
sudo systemctl start sfire-admin-api
```

#### 2. 部署前端

```bash
# 进入前端目录
cd /var/www/sfire-admin/frontend

# 安装依赖
pnpm install

# 配置生产环境变量
cp .env.production.example .env.production
vim .env.production  # 编辑配置

# 构建项目
pnpm build:pro

# 部署到 Nginx
sudo mkdir -p /var/www/html/sfire-admin
sudo cp -r dist/* /var/www/html/sfire-admin/
sudo chown -R www-data:www-data /var/www/html/sfire-admin
```

#### 3. 配置 Nginx

```bash
# 复制 Nginx 配置
sudo cp deploy/nginx.conf /etc/nginx/sites-available/sfire-admin

# 编辑配置（修改域名）
sudo vim /etc/nginx/sites-available/sfire-admin

# 启用配置
sudo ln -s /etc/nginx/sites-available/sfire-admin /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

#### 4. 配置 SSL（可选但推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 🔧 配置说明

### Systemd 服务配置

编辑 `/etc/systemd/system/sfire-admin-api.service`，确保以下路径正确：

- `WorkingDirectory`: 后端项目路径
- `ExecStart`: Python 虚拟环境路径
- `User/Group`: 运行服务的用户（推荐使用 www-data）

### Nginx 配置

编辑 `/etc/nginx/sites-available/sfire-admin`，修改：

- `server_name`: 你的域名
- `root`: 前端静态文件路径
- `ssl_certificate`: SSL 证书路径（如果使用 HTTPS）
- `proxy_pass`: 后端服务地址（默认 http://127.0.0.1:8000）

### 环境变量配置

#### 后端 (.env)

- `MYSQL_*`: MySQL 数据库配置
- `REDIS_*`: Redis 配置
- `JWT_SECRET_KEY`: JWT 密钥（必须修改）
- `SECRET_KEY`: 应用密钥（必须修改）
- `CORS_ORIGINS`: 允许的跨域域名

#### 前端 (.env.production)

- `VITE_API_URL`: API 地址（如果使用 Nginx 代理，设置为 `/api`）
- `VITE_PUBLIC_PATH`: 公共基础路径（设置为 `/sfire-admin`，因为后台管理系统部署在 `/sfire-admin` 路径下）

## 📝 常用命令

### 服务管理

```bash
# 后端服务
sudo systemctl start sfire-admin-api
sudo systemctl stop sfire-admin-api
sudo systemctl restart sfire-admin-api
sudo systemctl status sfire-admin-api
sudo journalctl -u sfire-admin-api -f

# Nginx
sudo systemctl start nginx
sudo systemctl reload nginx
sudo nginx -t
```

### 查看日志

```bash
# 后端日志
sudo journalctl -u sfire-admin-api -f
sudo journalctl -u sfire-admin-api -n 100

# Nginx 日志
sudo tail -f /var/log/nginx/sfire-admin-access.log
sudo tail -f /var/log/nginx/sfire-admin-error.log
```

### 更新部署（推荐使用脚本）

```bash
# 使用更新部署脚本（推荐）⭐
sudo bash deploy/deploy.sh

# 或单独部署
sudo bash deploy/deploy.sh backend   # 仅更新后端
sudo bash deploy/deploy.sh frontend  # 仅更新前端

# 不拉取代码，直接部署
sudo bash deploy/deploy.sh all --no-pull
```

**手动更新（不推荐）:**

```bash
# 更新后端
cd /var/www/sfire-admin/backend
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sfire-admin-api

# 更新前端
cd /var/www/sfire-admin/frontend
git pull
pnpm install
pnpm build:pro
sudo cp -r dist/* /var/www/html/sfire-admin/
sudo systemctl reload nginx
```

## ❓ 常见问题

### 1. 服务无法启动

检查：
- 环境变量配置是否正确
- 数据库和 Redis 是否正常运行
- 端口是否被占用
- 文件权限是否正确

### 2. 502 Bad Gateway

检查：
- 后端服务是否运行: `sudo systemctl status sfire-admin-api`
- 后端服务日志: `sudo journalctl -u sfire-admin-api -f`
- Nginx 配置中的 proxy_pass 地址是否正确

### 3. 前端页面空白

检查：
- 前端文件是否正确部署到 `/var/www/html/sfire-admin`
- Nginx 配置中的 root 路径是否正确
- 浏览器控制台是否有错误
- API 地址配置是否正确

## 🔐 安全建议

1. **修改默认密码**: 确保所有默认密码都已修改
2. **使用强密码**: 数据库、Redis、JWT 密钥等
3. **启用 HTTPS**: 使用 SSL 证书加密传输
4. **配置防火墙**: 只开放必要的端口（80, 443, 22）
5. **定期更新**: 保持系统和软件包更新
6. **备份数据**: 定期备份数据库和重要文件

## 📚 更多信息

详细部署文档请参考: [DEPLOYMENT.md](../DEPLOYMENT.md)

