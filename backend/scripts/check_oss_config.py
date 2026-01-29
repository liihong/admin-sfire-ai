"""
OSS 配置检查脚本
用于诊断 OSS 配置是否正确
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from utils.oss_service import oss_service
from loguru import logger


def check_oss_config():
    """检查 OSS 配置"""
    print("=" * 60)
    print("OSS 配置检查")
    print("=" * 60)
    
    # 检查基础配置
    provider = getattr(settings, "OSS_PROVIDER", "local")
    print(f"\n1. OSS 服务提供商: {provider}")
    
    access_key_id = getattr(settings, "OSS_ACCESS_KEY_ID", "")
    access_key_secret = getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
    bucket_name = getattr(settings, "OSS_BUCKET_NAME", "")
    endpoint = getattr(settings, "OSS_ENDPOINT", "")
    region = getattr(settings, "OSS_REGION", "")
    domain = getattr(settings, "OSS_DOMAIN", "")
    
    print(f"\n2. 配置字段检查:")
    print(f"   OSS_ACCESS_KEY_ID: {'[OK] 已设置' if access_key_id else '[X] 未设置'}")
    print(f"   OSS_ACCESS_KEY_SECRET: {'[OK] 已设置' if access_key_secret else '[X] 未设置'}")
    print(f"   OSS_BUCKET_NAME: {'[OK] 已设置' if bucket_name else '[X] 未设置'}")
    
    if provider == "aliyun":
        print(f"   OSS_ENDPOINT: {'[OK] 已设置' if endpoint else '[X] 未设置'}")
    elif provider == "tencent":
        print(f"   OSS_REGION: {'[OK] 已设置' if region else '[X] 未设置'}")
    elif provider == "qiniu":
        print(f"   OSS_DOMAIN: {'[OK] 已设置' if domain else '[X] 未设置（七牛云需要配置）'}")
    
    print(f"   OSS_DOMAIN: {'[OK] 已设置' if domain else '[!] 未设置（可选，建议配置）'}")
    
    # 检查实际使用的服务
    print(f"\n3. 实际使用的服务: {oss_service.provider}")
    
    if oss_service.provider == "local":
        print("   [!] 当前使用本地存储模式")
        print("   原因:")
        if provider == "local":
            print("      - OSS_PROVIDER 设置为 'local'")
        elif provider == "aliyun":
            if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
                print("      - 阿里云 OSS 配置不完整")
        elif provider == "tencent":
            if not all([access_key_id, access_key_secret, region, bucket_name]):
                print("      - 腾讯云 COS 配置不完整")
        elif provider == "qiniu":
            if not all([access_key_id, access_key_secret, bucket_name]):
                print("      - 七牛云配置不完整")
        else:
            print(f"      - 不支持的 OSS 服务商: {provider}")
    else:
        print(f"   [OK] 当前使用 {oss_service.provider.upper()} OSS 服务")
    
    # 检查依赖
    print(f"\n4. 依赖检查:")
    if provider == "aliyun":
        try:
            import oss2
            print("   [OK] oss2 库已安装")
        except ImportError:
            print("   [X] oss2 库未安装，请运行: pip install oss2")
    elif provider == "tencent":
        try:
            from qcloud_cos import CosConfig
            print("   [OK] qcloud_cos 库已安装")
        except ImportError:
            print("   [X] qcloud_cos 库未安装，请运行: pip install cos-python-sdk-v5")
    elif provider == "qiniu":
        try:
            from qiniu import Auth
            print("   [OK] qiniu 库已安装")
        except ImportError:
            print("   [X] qiniu 库未安装，请运行: pip install qiniu")
    
    # 配置建议
    print(f"\n5. 配置建议:")
    if provider == "local":
        print("   如果要使用云存储，请在 .env 文件中设置:")
        print("   OSS_PROVIDER=aliyun  # 或 tencent、qiniu")
        print("   OSS_ACCESS_KEY_ID=your_access_key_id")
        print("   OSS_ACCESS_KEY_SECRET=your_access_key_secret")
        print("   OSS_BUCKET_NAME=your_bucket_name")
        if provider == "aliyun":
            print("   OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com")
        elif provider == "tencent":
            print("   OSS_REGION=ap-guangzhou")
        print("   OSS_DOMAIN=https://cdn.example.com  # 可选，建议配置")
    elif oss_service.provider == "local" and provider != "local":
        print("   配置不完整，请检查以下字段:")
        if provider == "aliyun":
            if not access_key_id:
                print("   - OSS_ACCESS_KEY_ID")
            if not access_key_secret:
                print("   - OSS_ACCESS_KEY_SECRET")
            if not endpoint:
                print("   - OSS_ENDPOINT")
            if not bucket_name:
                print("   - OSS_BUCKET_NAME")
        elif provider == "tencent":
            if not access_key_id:
                print("   - OSS_ACCESS_KEY_ID")
            if not access_key_secret:
                print("   - OSS_ACCESS_KEY_SECRET")
            if not region:
                print("   - OSS_REGION")
            if not bucket_name:
                print("   - OSS_BUCKET_NAME")
        elif provider == "qiniu":
            if not access_key_id:
                print("   - OSS_ACCESS_KEY_ID")
            if not access_key_secret:
                print("   - OSS_ACCESS_KEY_SECRET")
            if not bucket_name:
                print("   - OSS_BUCKET_NAME")
            if not domain:
                print("   - OSS_DOMAIN（七牛云必填）")
    
    print("\n" + "=" * 60)
    print("详细配置说明请查看: backend/docs/OSS_CONFIG.md")
    print("=" * 60)


if __name__ == "__main__":
    check_oss_config()

