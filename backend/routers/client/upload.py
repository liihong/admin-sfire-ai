"""
Client Upload Endpoints
C端文件上传相关接口（小程序 & PC官网）
"""
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from utils.exceptions import BadRequestException, ServerErrorException
from utils.response import success
from utils.oss_service import oss_service
from core.deps import get_current_miniprogram_user
from models.user import User

router = APIRouter()

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
# 最大文件大小 (2MB)
MAX_FILE_SIZE = 2 * 1024 * 1024
# 头像文件大小限制 (1MB)
MAX_AVATAR_SIZE = 1 * 1024 * 1024


@router.post("/image", summary="上传图片")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传图片文件（C端用户）

    - 支持 JPG、PNG、GIF、WEBP 格式
    - 最大文件大小: 2MB
    - 需要用户登录
    - 使用 OSS 服务存储（支持本地存储、阿里云 OSS、腾讯云 COS、七牛云等）
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestException(msg="不支持的文件格式，仅支持 JPG、PNG、GIF、WEBP")

    # 读取文件内容检查大小
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise BadRequestException(msg="文件大小不能超过 2MB")

    # 使用 OSS 服务上传文件
    try:
        result = await oss_service.upload_file(
            file_content=content,
            filename=file.filename or "image.jpg",
            folder="images",  # 图片存储文件夹
            content_type=file.content_type
        )
        
        # 返回统一格式的响应
        return success(
            data={
                "url": result["url"],
                "path": result["path"],
                "filename": result["filename"],
                "original_name": file.filename,
                "size": result["size"],
                "content_type": file.content_type
            },
            msg="上传成功"
        )
    except (BadRequestException, ServerErrorException):
        # 重新抛出已知异常
        raise
    except Exception as e:
        # 捕获其他未知异常
        raise ServerErrorException(msg=f"文件上传失败: {str(e)}")


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传头像图片（C端用户）

    - 支持 JPG、PNG、GIF、WEBP 格式
    - 最大文件大小: 1MB
    - 需要用户登录
    - 强制使用本地存储（不使用OSS）
    - 上传成功后返回头像 URL，可用于更新用户信息
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestException(msg="不支持的文件格式，仅支持 JPG、PNG、GIF、WEBP")

    # 读取文件内容检查大小
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_AVATAR_SIZE:
        raise BadRequestException(msg="头像文件大小不能超过 1MB")

    # 使用本地存储上传头像文件（强制使用本地存储，不使用OSS）
    try:
        # 生成包含用户ID的文件名（用于标识）
        filename = file.filename or f"avatar_{current_user.id}.jpg"
        
        result = await oss_service.upload_avatar_to_local(
            file_content=content,
            filename=filename,
            content_type=file.content_type
        )
        
        # 返回统一格式的响应
        return success(
            data={
                "url": result["url"],
                "path": result["path"],
                "filename": result["filename"],
                "original_name": file.filename,
                "size": result["size"],
                "content_type": file.content_type
            },
            msg="头像上传成功"
        )
    except (BadRequestException, ServerErrorException):
        # 重新抛出已知异常
        raise
    except Exception as e:
        # 捕获其他未知异常
        raise ServerErrorException(msg=f"头像上传失败: {str(e)}")

