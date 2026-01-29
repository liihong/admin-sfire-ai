# Nginx 配置说明

## 配置概述

本项目的 Nginx 配置将后台管理系统部署在 `/sfire-admin` 路径下，根路径 `/` 保留给未来的官网使用。

## 访问地址

- **后台管理系统**: `https://your-domain.com/sfire-admin` 或 `http://your-ip/sfire-admin`
- **API 接口**: `https://your-domain.com/api` 或 `http://your-ip/api`
- **根路径**: `https://your-domain.com/` （保留给未来官网）

## 前端配置要求

**重要：** 在部署前端之前，必须确保 `.env.production` 文件中设置了正确的 `VITE_PUBLIC_PATH`：

```bash
# .env.production
VITE_PUBLIC_PATH=/sfire-admin
VITE_API_URL=/api
```

如果不设置 `VITE_PUBLIC_PATH=/sfire-admin`，前端构建后的资源路径会不正确，导致页面无法正常加载。

## 配置结构

### 1. 后台管理系统路径 (`/sfire-admin`)

```nginx
location /sfire-admin {
    alias /var/www/html/sfire-admin;
    index index.html;
    try_files $uri $uri/ /sfire-admin/index.html;
}
```

- 使用 `alias` 而不是 `root`，因为路径不是直接在 root 下
- `try_files` 确保 Vue Router 的 history 模式正常工作
- 静态资源缓存设置为 1 年

### 2. 根路径 (`/`)

```nginx
location / {
    try_files $uri $uri/ =404;
}
```

- 暂时返回 404，等官网部署后可以配置
- 或者可以指向一个默认页面

### 3. API 代理 (`/api`)

```nginx
location /api {
    proxy_pass http://127.0.0.1:8000;
    # ... 其他代理配置
}
```

- 所有 `/api` 开头的请求会被代理到后端服务
- 支持 WebSocket 连接

## 部署步骤

1. **配置前端环境变量**

   编辑 `frontend/.env.production`：
   ```bash
   VITE_PUBLIC_PATH=/sfire-admin
   VITE_API_URL=/api
   ```

2. **构建前端**

   ```bash
   cd frontend
   pnpm build:pro
   ```

3. **部署到服务器**

   ```bash
   sudo mkdir -p /var/www/html/sfire-admin
   sudo cp -r dist/* /var/www/html/sfire-admin/
   sudo chown -R www-data:www-data /var/www/html/sfire-admin
   ```

4. **配置 Nginx**

   ```bash
   sudo cp deploy/nginx.conf /etc/nginx/sites-available/sfire-admin
   sudo ln -s /etc/nginx/sites-available/sfire-admin /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## 常见问题

### 1. 页面空白或 404

**原因**: `VITE_PUBLIC_PATH` 未正确设置

**解决**: 确保 `.env.production` 中 `VITE_PUBLIC_PATH=/sfire-admin`

### 2. 静态资源 404

**原因**: 资源路径不正确

**解决**: 
- 检查 `VITE_PUBLIC_PATH` 配置
- 检查 Nginx `alias` 配置是否正确
- 查看浏览器控制台的资源请求路径

### 3. API 请求失败

**原因**: 代理配置不正确

**解决**:
- 检查后端服务是否运行: `systemctl status sfire-admin-api`
- 检查 `proxy_pass` 地址是否正确
- 查看 Nginx 错误日志: `tail -f /var/log/nginx/sfire-admin-error.log`

## 未来扩展

当需要部署官网时：

1. 在 `/var/www/html/` 下部署官网文件
2. 修改 Nginx 配置中的 `location /` 块：

```nginx
location / {
    root /var/www/html;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

这样：
- 官网访问: `https://your-domain.com/`
- 后台管理: `https://your-domain.com/sfire-admin`
- API 接口: `https://your-domain.com/api`

三个路径互不干扰。

































