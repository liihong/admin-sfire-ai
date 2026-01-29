# OSS 对象存储服务配置说明

## 概述

系统支持多种 OSS（对象存储服务）提供商，用于处理图片等文件的上传和存储。

## 支持的服务商

- **local**: 本地存储（默认，用于开发环境）
- **aliyun**: 阿里云 OSS
- **tencent**: 腾讯云 COS
- **qiniu**: 七牛云

## 配置字段说明

### 通用配置字段

所有 OSS 服务商都需要以下基础配置：

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `OSS_PROVIDER` | string | 是 | OSS 服务提供商，可选值：`local`、`aliyun`、`tencent`、`qiniu` | `aliyun` |
| `OSS_ACCESS_KEY_ID` | string | 条件必填 | OSS Access Key ID（本地存储不需要） | `LTAI5t...` |
| `OSS_ACCESS_KEY_SECRET` | string | 条件必填 | OSS Access Key Secret（本地存储不需要） | `xxx...` |
| `OSS_BUCKET_NAME` | string | 条件必填 | OSS 存储桶名称（本地存储不需要） | `my-bucket` |
| `OSS_DOMAIN` | string | 否 | OSS 自定义域名，用于文件访问 URL（可选，不配置时会自动生成） | `https://cdn.example.com` |

### 阿里云 OSS 专用配置

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `OSS_ENDPOINT` | string | 是 | 阿里云 OSS 服务端点 | `oss-cn-hangzhou.aliyuncs.com` |

**阿里云 OSS 端点列表：**
- 华东1（杭州）：`oss-cn-hangzhou.aliyuncs.com`
- 华东2（上海）：`oss-cn-shanghai.aliyuncs.com`
- 华北1（青岛）：`oss-cn-qingdao.aliyuncs.com`
- 华北2（北京）：`oss-cn-beijing.aliyuncs.com`
- 华北3（张家口）：`oss-cn-zhangjiakou.aliyuncs.com`
- 华北5（呼和浩特）：`oss-cn-huhehaote.aliyuncs.com`
- 华南1（深圳）：`oss-cn-shenzhen.aliyuncs.com`
- 华南2（河源）：`oss-cn-heyuan.aliyuncs.com`
- 西南1（成都）：`oss-cn-chengdu.aliyuncs.com`
- 中国（香港）：`oss-cn-hongkong.aliyuncs.com`
- 美国（硅谷）：`oss-us-west-1.aliyuncs.com`
- 美国（弗吉尼亚）：`oss-us-east-1.aliyuncs.com`
- 新加坡：`oss-ap-southeast-1.aliyuncs.com`
- 澳大利亚（悉尼）：`oss-ap-southeast-2.aliyuncs.com`
- 马来西亚（吉隆坡）：`oss-ap-southeast-3.aliyuncs.com`
- 印度尼西亚（雅加达）：`oss-ap-southeast-5.aliyuncs.com`
- 日本（东京）：`oss-ap-northeast-1.aliyuncs.com`
- 韩国（首尔）：`oss-ap-northeast-2.aliyuncs.com`
- 印度（孟买）：`oss-ap-south-1.aliyuncs.com`
- 英国（伦敦）：`oss-eu-west-1.aliyuncs.com`
- 德国（法兰克福）：`oss-eu-central-1.aliyuncs.com`
- 阿联酋（迪拜）：`oss-me-east-1.aliyuncs.com`

### 腾讯云 COS 专用配置

| 字段名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `OSS_REGION` | string | 是 | 腾讯云 COS 区域 | `ap-guangzhou` |

**腾讯云 COS 区域列表：**
- 北京一区：`ap-beijing-1`
- 北京：`ap-beijing`
- 上海：`ap-shanghai`
- 广州：`ap-guangzhou`
- 成都：`ap-chengdu`
- 重庆：`ap-chongqing`
- 新加坡：`ap-singapore`
- 香港：`ap-hongkong`
- 多伦多：`na-toronto`
- 硅谷：`na-siliconvalley`
- 弗吉尼亚：`na-ashburn`
- 法兰克福：`eu-frankfurt`
- 首尔：`ap-seoul`
- 孟买：`ap-mumbai`
- 东京：`ap-tokyo`

### 七牛云专用配置

七牛云使用通用配置字段即可，无需额外配置。

## 环境变量配置示例

### 本地存储（开发环境）

```bash
# .env 文件
OSS_PROVIDER=local
OSS_DOMAIN=http://localhost:8000
```

### 阿里云 OSS

```bash
# .env 文件
OSS_PROVIDER=aliyun
OSS_ACCESS_KEY_ID=LTAI5txxxxxxxxxxxxx
OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_BUCKET_NAME=my-bucket-name
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_DOMAIN=https://cdn.example.com  # 可选，配置自定义域名
```

### 腾讯云 COS

```bash
# .env 文件
OSS_PROVIDER=tencent
OSS_ACCESS_KEY_ID=AKIDxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_BUCKET_NAME=my-bucket-name-1234567890
OSS_REGION=ap-guangzhou
OSS_DOMAIN=https://cdn.example.com  # 可选，配置自定义域名
```

### 七牛云

```bash
# .env 文件
OSS_PROVIDER=qiniu
OSS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_BUCKET_NAME=my-bucket-name
OSS_DOMAIN=https://cdn.example.com  # 必填，七牛云需要配置域名
```

## 依赖安装

根据选择的服务商，需要安装对应的 Python SDK：

### 阿里云 OSS

```bash
pip install oss2
```

### 腾讯云 COS

```bash
pip install cos-python-sdk-v5
```

### 七牛云

```bash
pip install qiniu
```

## 使用方法

### 在代码中使用

```python
from utils.oss_service import oss_service

# 上传文件
result = await oss_service.upload_file(
    file_content=file_bytes,
    filename="image.jpg",
    folder="images",  # 可选，指定存储文件夹
    content_type="image/jpeg"  # 可选，自动检测
)

# 返回结果示例：
# {
#     "url": "https://cdn.example.com/uploads/20240101/abc123.jpg",
#     "path": "uploads/20240101/abc123.jpg",
#     "filename": "abc123.jpg",
#     "size": 102400
# }

# 删除文件
success = await oss_service.delete_file("uploads/20240101/abc123.jpg")

# 获取文件 URL（不实际上传）
url = oss_service.get_file_url("uploads/20240101/abc123.jpg")
```

### 在路由中使用示例

```python
from fastapi import APIRouter, UploadFile, File
from utils.oss_service import oss_service
from utils.response import success

router = APIRouter()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # 读取文件内容
    content = await file.read()
    
    # 上传到 OSS
    result = await oss_service.upload_file(
        file_content=content,
        filename=file.filename or "image.jpg",
        folder="images"
    )
    
    return success(data=result, msg="上传成功")
```

## 注意事项

1. **配置优先级**：如果配置不完整，系统会自动降级到本地存储模式
2. **文件路径**：文件会自动按日期组织目录（格式：`YYYYMMDD`）
3. **文件名**：系统会自动生成唯一文件名（UUID），避免文件名冲突
4. **自定义域名**：建议配置 `OSS_DOMAIN`，使用 CDN 加速访问
5. **权限设置**：确保 OSS 存储桶的访问权限配置正确（公共读或私有读）
6. **本地存储**：本地存储模式下，文件保存在 `static/uploads/` 目录下

## 故障排查

### 问题：上传失败，自动降级到本地存储

**原因**：
- OSS SDK 未安装
- 配置信息不完整
- 网络连接问题
- 凭证无效

**解决方案**：
1. 检查是否安装了对应的 SDK
2. 检查 `.env` 文件中的配置是否完整
3. 检查网络连接和 OSS 服务状态
4. 验证 Access Key 和 Secret 是否正确

### 问题：文件上传成功但无法访问

**原因**：
- 存储桶权限配置不正确
- 自定义域名未配置或配置错误
- CORS 配置问题

**解决方案**：
1. 检查存储桶的访问权限（建议设置为公共读）
2. 检查 `OSS_DOMAIN` 配置是否正确
3. 检查 OSS 控制台的 CORS 配置

## 安全建议

1. **不要将 Access Key 和 Secret 提交到代码仓库**
2. **使用环境变量或密钥管理服务存储敏感信息**
3. **定期轮换 Access Key**
4. **使用最小权限原则配置 OSS 权限**
5. **启用 OSS 访问日志和监控**

