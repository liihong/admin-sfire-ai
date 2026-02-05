#!/usr/bin/env python3
"""
测试配置加载脚本
用于诊断 .env 文件加载问题
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from loguru import logger

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("配置加载测试")
    print("=" * 60)
    
    # 检查 .env 文件路径
    env_file_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_file_abs = os.path.abspath(env_file_path)
    
    print(f"\n1. .env 文件路径: {env_file_abs}")
    print(f"   文件是否存在: {os.path.exists(env_file_abs)}")
    
    if os.path.exists(env_file_abs):
        file_stat = os.stat(env_file_abs)
        print(f"   文件权限: {oct(file_stat.st_mode)}")
        print(f"   文件大小: {file_stat.st_size} 字节")
        print(f"   文件所有者: UID={file_stat.st_uid}, GID={file_stat.st_gid}")
        
        # 尝试读取文件内容（仅显示微信支付相关配置）
        try:
            with open(env_file_abs, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n2. .env 文件内容（微信支付相关）:")
                found_wechat_config = False
                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    if line_stripped and not line_stripped.startswith('#'):
                        if 'WECHAT' in line_stripped.upper():
                            found_wechat_config = True
                            key, *value_parts = line_stripped.split('=', 1)
                            value = '='.join(value_parts) if value_parts else ''
                            # 隐藏敏感信息
                            if 'KEY' in key.upper() or 'SECRET' in key.upper():
                                display_value = f"{'*' * min(len(value), 8)}" if value else "(空)"
                            else:
                                display_value = value[:20] + "..." if len(value) > 20 else value
                            print(f"   第 {i} 行: {key}={display_value}")
                            print(f"           原始值长度: {len(value)}, 是否为空: {not bool(value)}")
                
                if not found_wechat_config:
                    print("   ⚠️ 未找到微信支付相关配置")
        except Exception as e:
            print(f"   ❌ 读取文件失败: {e}")
    
    # 检查配置值
    print(f"\n3. 配置值检查:")
    print(f"   WECHAT_APP_ID: {settings.WECHAT_APP_ID[:10]}..." if settings.WECHAT_APP_ID else "   WECHAT_APP_ID: (空)")
    print(f"   WECHAT_PAY_MCH_ID: {settings.WECHAT_PAY_MCH_ID} (长度: {len(settings.WECHAT_PAY_MCH_ID) if settings.WECHAT_PAY_MCH_ID else 0})")
    print(f"   WECHAT_PAY_API_KEY: {'*' * min(len(settings.WECHAT_PAY_API_KEY), 8)}... (长度: {len(settings.WECHAT_PAY_API_KEY) if settings.WECHAT_PAY_API_KEY else 0})")
    print(f"   WECHAT_PAY_NOTIFY_URL: {settings.WECHAT_PAY_NOTIFY_URL}")
    
    # 验证配置完整性
    print(f"\n4. 配置完整性验证:")
    mch_id_ok = bool(settings.WECHAT_PAY_MCH_ID and settings.WECHAT_PAY_MCH_ID.strip())
    api_key_ok = bool(settings.WECHAT_PAY_API_KEY and settings.WECHAT_PAY_API_KEY.strip())
    
    if mch_id_ok and api_key_ok:
        print("   ✅ 微信支付配置完整")
    else:
        print("   ❌ 微信支付配置不完整:")
        print(f"      - WECHAT_PAY_MCH_ID: {'✅' if mch_id_ok else '❌ 为空或只有空格'}")
        print(f"      - WECHAT_PAY_API_KEY: {'✅' if api_key_ok else '❌ 为空或只有空格'}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_config_loading()

