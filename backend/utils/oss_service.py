"""
OSS 对象存储服务
支持阿里云 OSS、腾讯云 COS、七牛云等主流 OSS 服务商
"""
import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional
from pathlib import Path
from loguru import logger

from core.config import settings
from utils.exceptions import ServerErrorException, BadRequestException


class OSSService:
    """
    OSS 对象存储服务类
    
    支持多种 OSS 服务商：
    - 阿里云 OSS (aliyun)
    - 腾讯云 COS (tencent)
    - 七牛云 (qiniu)
    - 本地存储 (local) - 用于开发环境
    """
    
    def __init__(self):
        """初始化 OSS 服务"""
        self.provider = getattr(settings, "OSS_PROVIDER", "local").lower()
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """根据配置初始化对应的 OSS 客户端"""
        if self.provider == "local":
            # 本地存储，无需初始化客户端
            return
        
        elif self.provider == "aliyun":
            try:
                import oss2
                access_key_id = getattr(settings, "OSS_ACCESS_KEY_ID", "")
                access_key_secret = getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
                endpoint = getattr(settings, "OSS_ENDPOINT", "")
                bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
                
                if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
                    logger.warning("阿里云 OSS 配置不完整，将使用本地存储")
                    self.provider = "local"
                    return
                
                auth = oss2.Auth(access_key_id, access_key_secret)
                self._client = oss2.Bucket(auth, endpoint, bucket_name)
                logger.info("✅ 阿里云 OSS 客户端初始化成功")
            except ImportError:
                logger.warning("未安装 oss2 库，将使用本地存储。请运行: pip install oss2")
                self.provider = "local"
            except Exception as e:
                logger.error(f"阿里云 OSS 初始化失败: {e}，将使用本地存储")
                self.provider = "local"
        
        elif self.provider == "tencent":
            try:
                from qcloud_cos import CosConfig
                from qcloud_cos import CosS3Client
                
                secret_id = getattr(settings, "OSS_ACCESS_KEY_ID", "")
                secret_key = getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
                region = getattr(settings, "OSS_REGION", "")
                bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
                
                if not all([secret_id, secret_key, region, bucket_name]):
                    logger.warning("腾讯云 COS 配置不完整，将使用本地存储")
                    self.provider = "local"
                    return
                
                config = CosConfig(
                    Region=region,
                    SecretId=secret_id,
                    SecretKey=secret_key,
                    Scheme="https"
                )
                self._client = CosS3Client(config)
                self._bucket_name = bucket_name
                logger.info("✅ 腾讯云 COS 客户端初始化成功")
            except ImportError:
                logger.warning("未安装 qcloud_cos 库，将使用本地存储。请运行: pip install cos-python-sdk-v5")
                self.provider = "local"
            except Exception as e:
                logger.error(f"腾讯云 COS 初始化失败: {e}，将使用本地存储")
                self.provider = "local"
        
        elif self.provider == "qiniu":
            try:
                from qiniu import Auth, put_data
                
                access_key = getattr(settings, "OSS_ACCESS_KEY_ID", "")
                secret_key = getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
                bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
                domain = getattr(settings, "OSS_DOMAIN", "")
                
                if not all([access_key, secret_key, bucket_name]):
                    logger.warning("七牛云配置不完整，将使用本地存储")
                    self.provider = "local"
                    return
                
                self._auth = Auth(access_key, secret_key)
                self._bucket_name = bucket_name
                self._domain = domain
                logger.info("✅ 七牛云客户端初始化成功")
            except ImportError:
                logger.warning("未安装 qiniu 库，将使用本地存储。请运行: pip install qiniu")
                self.provider = "local"
            except Exception as e:
                logger.error(f"七牛云初始化失败: {e}，将使用本地存储")
                self.provider = "local"
        
        else:
            logger.warning(f"不支持的 OSS 服务商: {self.provider}，将使用本地存储")
            self.provider = "local"
    
    def _generate_file_path(
        self,
        filename: str,
        folder: Optional[str] = None
    ) -> str:
        """
        生成文件存储路径
        
        Args:
            filename: 原始文件名
            folder: 存储文件夹（可选）
        
        Returns:
            文件存储路径
        """
        # 获取文件扩展名
        ext = Path(filename).suffix or ".jpg"
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 按日期组织目录
        date_str = datetime.now().strftime("%Y%m%d")
        
        if folder:
            return f"{folder}/{date_str}/{unique_filename}"
        return f"uploads/{date_str}/{unique_filename}"
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> dict:
        """
        上传文件到 OSS
        
        Args:
            file_content: 文件内容（字节流）
            filename: 原始文件名
            folder: 存储文件夹（可选，如 "avatars", "images" 等）
            content_type: 文件 MIME 类型（可选，会自动检测）
        
        Returns:
            包含文件信息的字典：
            {
                "url": "文件访问URL",
                "path": "文件存储路径",
                "filename": "文件名",
                "size": 文件大小（字节）
            }
        
        Raises:
            ServerErrorException: 上传失败时抛出
        """
        if not file_content:
            raise BadRequestException(msg="文件内容不能为空")
        
        # 自动检测 MIME 类型
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"
        
        # 生成存储路径
        file_path = self._generate_file_path(filename, folder)
        file_size = len(file_content)
        
        try:
            if self.provider == "local":
                # 本地存储
                return await self._upload_to_local(file_content, file_path, filename, file_size)
            
            elif self.provider == "aliyun":
                # 阿里云 OSS
                if self._client is None:
                    logger.warning("阿里云 OSS 客户端未初始化，降级到本地存储")
                    return await self._upload_to_local(file_content, file_path, filename, file_size)
                return await self._upload_to_aliyun(file_content, file_path, content_type, filename, file_size)
            
            elif self.provider == "tencent":
                # 腾讯云 COS
                if self._client is None:
                    logger.warning("腾讯云 COS 客户端未初始化，降级到本地存储")
                    return await self._upload_to_local(file_content, file_path, filename, file_size)
                return await self._upload_to_tencent(file_content, file_path, content_type, filename, file_size)
            
            elif self.provider == "qiniu":
                # 七牛云
                if not hasattr(self, '_auth') or self._auth is None:
                    logger.warning("七牛云客户端未初始化，降级到本地存储")
                    return await self._upload_to_local(file_content, file_path, filename, file_size)
                return await self._upload_to_qiniu(file_content, file_path, content_type, filename, file_size)
            
            else:
                logger.warning(f"不支持的 OSS 服务商: {self.provider}，降级到本地存储")
                return await self._upload_to_local(file_content, file_path, filename, file_size)
        
        except BadRequestException:
            raise
        except ServerErrorException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {e}", exc_info=True)
            # 如果云存储失败，尝试降级到本地存储
            try:
                logger.warning(f"云存储上传失败，尝试降级到本地存储: {e}")
                return await self._upload_to_local(file_content, file_path, filename, file_size)
            except Exception as local_error:
                logger.error(f"本地存储也失败: {local_error}", exc_info=True)
                raise ServerErrorException(msg=f"文件上传失败: {str(e)}")
    
    async def _upload_to_local(
        self,
        file_content: bytes,
        file_path: str,
        filename: str,
        file_size: int
    ) -> dict:
        """上传文件到本地存储"""
        # 构建完整路径
        full_path = os.path.join("static", file_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 写入文件
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        # 生成访问 URL（本地存储时，不使用 OSS_DOMAIN，使用本地服务器地址）
        # 优先使用 CORS_ORIGINS 的第一个，如果没有则使用默认地址
        cors_origins = getattr(settings, "CORS_ORIGINS", [])
        if cors_origins:
            base_url = cors_origins[0].rstrip('/')
        else:
            # 如果没有配置，使用默认的本地地址
            base_url = "https://sourcefire.cn"
        
        logger.info(f"[本地存储] 文件保存路径: {full_path}")
        logger.info(f"[本地存储] 使用的基础URL: {base_url}")
        
        url = f"{base_url}/static/{file_path}"
        
        return {
            "url": url,
            "path": file_path,
            "filename": os.path.basename(file_path),
            "size": file_size
        }
    
    async def upload_avatar_to_local(
        self,
        file_content: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> dict:
        """
        上传头像到本地存储（强制使用本地存储，不使用OSS）
        
        Args:
            file_content: 文件内容（字节流）
            filename: 原始文件名
            content_type: 文件 MIME 类型（可选，会自动检测）
        
        Returns:
            包含文件信息的字典：
            {
                "url": "文件访问URL",
                "path": "文件存储路径",
                "filename": "文件名",
                "size": 文件大小（字节）
            }
        
        Raises:
            ServerErrorException: 上传失败时抛出
        """
        if not file_content:
            raise BadRequestException(msg="文件内容不能为空")
        
        # 自动检测 MIME 类型
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"
        
        # 生成存储路径（头像固定存储在 avatars 文件夹）
        file_path = self._generate_file_path(filename, folder="avatars")
        file_size = len(file_content)
        
        logger.info(f"[头像上传] 强制使用本地存储，文件路径: {file_path}")
        
        # 直接调用本地存储方法
        return await self._upload_to_local(file_content, file_path, filename, file_size)
    
    async def _upload_to_aliyun(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str,
        filename: str,
        file_size: int
    ) -> dict:
        """上传文件到阿里云 OSS"""
        import oss2
        from urllib.parse import urlparse
        
        # 检查客户端是否已初始化
        if self._client is None:
            raise ServerErrorException(msg="阿里云 OSS 客户端未初始化，请检查配置")
        
        # 检查 OSS_DOMAIN 是否包含路径前缀
        domain = getattr(settings, "OSS_DOMAIN", "")
        actual_upload_path = file_path  # 实际上传路径
        
        logger.info(f"[OSS上传] 原始文件路径: {file_path}")
        logger.info(f"[OSS上传] OSS_DOMAIN 配置: {domain}")
        
        if domain:
            # 如果配置了自定义域名，检查是否包含路径前缀
            parsed = urlparse(domain)
            path_prefix = parsed.path.rstrip('/')  # 移除末尾的斜杠
            
            logger.info(f"[OSS上传] 解析域名 - scheme: {parsed.scheme}, netloc: {parsed.netloc}, path: {parsed.path}")
            
            # 如果域名包含路径前缀（如 /static），在上传路径中也加上这个前缀
            # 这样可以确保上传路径和访问 URL 一致
            if path_prefix:
                # 移除开头的斜杠（如果有）
                prefix = path_prefix.lstrip('/')
                actual_upload_path = f"{prefix}/{file_path}"
                logger.info(f"[OSS上传] 检测到路径前缀 '{prefix}'，实际上传路径: {actual_upload_path}")
        
        # 设置文件元信息
        headers = {
            "Content-Type": content_type
        }
        
        try:
            # 上传文件（使用包含前缀的路径）
            logger.info(f"[OSS上传] 开始上传文件到路径: {actual_upload_path}")
            result = self._client.put_object(actual_upload_path, file_content, headers=headers)
            
            # 检查上传结果（oss2 的 put_object 返回 PutObjectResult）
            # 如果上传成功，通常不会抛出异常，如果失败会抛出异常
            # 检查 result 对象是否有 status 属性
            try:
                status = getattr(result, 'status', None)
                if status is not None:
                    if status != 200:
                        logger.error(f"[OSS上传] 上传失败，状态码: {status}")
                        raise ServerErrorException(msg=f"阿里云 OSS 上传失败，状态码: {status}")
                    else:
                        logger.info(f"[OSS上传] 文件上传成功，状态码: {status}")
                else:
                    # 如果没有 status 属性，假设上传成功（oss2 在某些情况下可能不返回 status）
                    logger.info(f"[OSS上传] 文件上传成功（未检查到status属性，类型: {type(result)}）")
            except AttributeError:
                # 如果访问属性出错，假设上传成功（oss2 在某些版本可能不返回 status）
                logger.info(f"[OSS上传] 文件上传成功（无法访问status属性，类型: {type(result)}）")
        except Exception as e:
            # 捕获所有异常（如网络错误、认证错误等）
            logger.error(f"阿里云 OSS 上传异常: {e}", exc_info=True)
            raise ServerErrorException(msg=f"阿里云 OSS 上传失败: {str(e)}")
        
        # 生成访问 URL
        if not domain:
            # 如果没有配置域名，使用 endpoint 构建
            endpoint = getattr(settings, "OSS_ENDPOINT", "")
            bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
            if not endpoint or not bucket_name:
                raise ServerErrorException(msg="阿里云 OSS 配置不完整，缺少 OSS_ENDPOINT 或 OSS_BUCKET_NAME")
            domain = f"https://{bucket_name}.{endpoint.replace('https://', '').replace('http://', '')}"
            url = f"{domain}/{actual_upload_path}"  # 使用实际上传路径
        else:
            # 如果配置了自定义域名
            parsed = urlparse(domain)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            # 如果域名本身包含路径前缀，直接拼接实际上传路径
            # 因为实际上传路径已经包含了前缀（如果有的话）
            url = f"{base_domain}/{actual_upload_path}"  # 使用实际上传路径
        
        logger.info(f"[OSS上传] 生成的访问 URL: {url}")
        logger.info(f"[OSS上传] 返回的 path: {file_path}")
        
        return {
            "url": url,
            "path": file_path,  # 返回原始路径（不包含前缀），保持向后兼容
            "filename": os.path.basename(file_path),
            "size": file_size
        }
    
    async def _upload_to_tencent(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str,
        filename: str,
        file_size: int
    ) -> dict:
        """上传文件到腾讯云 COS"""
        from qcloud_cos import CosS3Client
        from urllib.parse import urlparse
        
        # 上传文件
        response = self._client.put_object(
            Bucket=self._bucket_name,
            Body=file_content,
            Key=file_path,
            ContentType=content_type
        )
        
        if response.get("status_code") != 200:
            raise ServerErrorException(msg=f"腾讯云 COS 上传失败，状态码: {response.get('status_code')}")
        
        # 生成访问 URL
        domain = getattr(settings, "OSS_DOMAIN", "")
        if not domain:
            # 如果没有配置域名，使用默认域名
            region = getattr(settings, "OSS_REGION", "")
            domain = f"https://{self._bucket_name}.cos.{region}.myqcloud.com"
            url = f"{domain}/{file_path}"
        else:
            # 如果配置了自定义域名，需要处理路径前缀
            parsed = urlparse(domain)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            path_prefix = parsed.path.rstrip('/')  # 移除末尾的斜杠
            
            # 如果域名包含路径前缀（如 /static），在 URL 中保留它
            if path_prefix:
                url = f"{base_domain}{path_prefix}/{file_path}"
            else:
                url = f"{base_domain}/{file_path}"
        
        return {
            "url": url,
            "path": file_path,
            "filename": os.path.basename(file_path),
            "size": file_size
        }
    
    async def _upload_to_qiniu(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str,
        filename: str,
        file_size: int
    ) -> dict:
        """上传文件到七牛云"""
        from qiniu import put_data
        from urllib.parse import urlparse
        
        # 生成上传 token
        token = self._auth.upload_token(self._bucket_name, file_path, 3600)
        
        # 上传文件
        ret, info = put_data(token, file_path, file_content, mime_type=content_type)
        
        if info.status_code != 200:
            raise ServerErrorException(msg=f"七牛云上传失败，状态码: {info.status_code}")
        
        # 生成访问 URL
        domain = getattr(settings, "OSS_DOMAIN", "")
        if not domain:
            raise ServerErrorException(msg="七牛云需要配置 OSS_DOMAIN")
        
        # 处理路径前缀
        parsed = urlparse(domain)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        path_prefix = parsed.path.rstrip('/')  # 移除末尾的斜杠
        
        # 如果域名包含路径前缀（如 /static），在 URL 中保留它
        if path_prefix:
            url = f"{base_domain}{path_prefix}/{file_path}"
        else:
            url = f"{base_domain}/{file_path}"
        
        return {
            "url": url,
            "path": file_path,
            "filename": os.path.basename(file_path),
            "size": file_size
        }
    
    async def delete_file(self, file_path: str) -> bool:
        """
        删除 OSS 中的文件
        
        Args:
            file_path: 文件存储路径
        
        Returns:
            是否删除成功
        """
        try:
            if self.provider == "local":
                # 本地存储删除
                full_path = os.path.join("static", file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True
                return False
            
            elif self.provider == "aliyun":
                # 阿里云 OSS 删除
                result = self._client.delete_object(file_path)
                return result.status == 204
            
            elif self.provider == "tencent":
                # 腾讯云 COS 删除
                response = self._client.delete_object(
                    Bucket=self._bucket_name,
                    Key=file_path
                )
                return response.get("status_code") == 204
            
            elif self.provider == "qiniu":
                # 七牛云删除
                from qiniu import BucketManager
                bucket_manager = BucketManager(self._auth)
                ret, info = bucket_manager.delete(self._bucket_name, file_path)
                return info.status_code == 200
            
            return False
        
        except Exception as e:
            logger.error(f"删除文件失败: {file_path}, 错误: {e}")
            return False
    
    def get_file_url(self, file_path: str) -> str:
        """
        获取文件的访问 URL（不实际上传）
        
        Args:
            file_path: 文件存储路径
        
        Returns:
            文件访问 URL
        """
        from urllib.parse import urlparse
        
        if self.provider == "local":
            # 本地存储时，不使用 OSS_DOMAIN，使用本地服务器地址
            cors_origins = getattr(settings, "CORS_ORIGINS", [])
            if cors_origins:
                base_url = cors_origins[0]
            else:
                base_url = "http://localhost:8000"
            return f"{base_url}/static/{file_path}"
        
        elif self.provider == "aliyun":
            domain = getattr(settings, "OSS_DOMAIN", "")
            if not domain:
                endpoint = getattr(settings, "OSS_ENDPOINT", "")
                bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
                domain = f"https://{bucket_name}.{endpoint.replace('https://', '').replace('http://', '')}"
                return f"{domain}/{file_path}"
            else:
                # 如果配置了自定义域名，需要处理路径前缀
                parsed = urlparse(domain)
                base_domain = f"{parsed.scheme}://{parsed.netloc}"
                path_prefix = parsed.path.rstrip('/')  # 移除末尾的斜杠
                
                # 如果域名包含路径前缀（如 /static），在 URL 中保留它
                if path_prefix:
                    return f"{base_domain}{path_prefix}/{file_path}"
                else:
                    return f"{base_domain}/{file_path}"
        
        elif self.provider == "tencent":
            domain = getattr(settings, "OSS_DOMAIN", "")
            if not domain:
                region = getattr(settings, "OSS_REGION", "")
                bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
                domain = f"https://{bucket_name}.cos.{region}.myqcloud.com"
                return f"{domain}/{file_path}"
            else:
                # 如果配置了自定义域名，需要处理路径前缀
                parsed = urlparse(domain)
                base_domain = f"{parsed.scheme}://{parsed.netloc}"
                path_prefix = parsed.path.rstrip('/')  # 移除末尾的斜杠
                
                # 如果域名包含路径前缀（如 /static），在 URL 中保留它
                if path_prefix:
                    return f"{base_domain}{path_prefix}/{file_path}"
                else:
                    return f"{base_domain}/{file_path}"
        
        elif self.provider == "qiniu":
            domain = getattr(settings, "OSS_DOMAIN", "")
            if not domain:
                raise ServerErrorException(msg="七牛云需要配置 OSS_DOMAIN")
            
            # 处理路径前缀
            parsed = urlparse(domain)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            path_prefix = parsed.path.rstrip('/')  # 移除末尾的斜杠
            
            # 如果域名包含路径前缀（如 /static），在 URL 中保留它
            if path_prefix:
                return f"{base_domain}{path_prefix}/{file_path}"
            else:
                return f"{base_domain}/{file_path}"
        
        return ""


# 创建全局 OSS 服务实例
oss_service = OSSService()

