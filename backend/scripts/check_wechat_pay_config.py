"""
微信支付配置诊断脚本
用于检查微信支付配置是否正确
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from loguru import logger


def check_wechat_pay_config():
    """检查微信支付配置"""
    print("=" * 60)
    print("微信支付配置诊断")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # 1. 检查 AppID
    print(f"\n1. 微信小程序 AppID:")
    if settings.WECHAT_APP_ID:
        print(f"   [OK] WECHAT_APP_ID = {settings.WECHAT_APP_ID}")
    else:
        print(f"   [ERROR] WECHAT_APP_ID 未配置")
        issues.append("WECHAT_APP_ID 未配置")
    
    # 2. 检查商户号
    print(f"\n2. 微信支付商户号:")
    if settings.WECHAT_PAY_MCH_ID:
        print(f"   [OK] WECHAT_PAY_MCH_ID = {settings.WECHAT_PAY_MCH_ID}")
    else:
        print(f"   [ERROR] WECHAT_PAY_MCH_ID 未配置")
        issues.append("WECHAT_PAY_MCH_ID 未配置")
    
    # 3. 检查API密钥（重点）
    print(f"\n3. 微信支付API密钥:")
    if settings.WECHAT_PAY_API_KEY:
        key_length = len(settings.WECHAT_PAY_API_KEY)
        print(f"   WECHAT_PAY_API_KEY 长度 = {key_length} 字符")
        
        if key_length == 32:
            print(f"   [OK] API密钥长度正确（32字符）")
            # 检查是否只包含字母和数字
            if settings.WECHAT_PAY_API_KEY.isalnum():
                print(f"   [OK] API密钥格式正确（仅包含字母和数字）")
            else:
                print(f"   [WARN] API密钥包含特殊字符（微信支付v2 API密钥应仅包含字母和数字）")
                warnings.append("API密钥包含特殊字符")
        else:
            print(f"   [ERROR] API密钥长度错误！")
            print(f"   当前长度: {key_length} 字符")
            print(f"   正确长度: 32 字符")
            print(f"   密钥值: {settings.WECHAT_PAY_API_KEY[:20]}...（已隐藏）")
            issues.append(f"API密钥长度错误（当前{key_length}字符，应为32字符）")
    else:
        print(f"   [ERROR] WECHAT_PAY_API_KEY 未配置")
        issues.append("WECHAT_PAY_API_KEY 未配置")
    
    # 4. 检查回调地址
    print(f"\n4. 微信支付回调地址:")
    if settings.WECHAT_PAY_NOTIFY_URL:
        if settings.WECHAT_PAY_NOTIFY_URL.startswith("https://"):
            print(f"   [OK] WECHAT_PAY_NOTIFY_URL = {settings.WECHAT_PAY_NOTIFY_URL}")
        else:
            print(f"   [WARN] WECHAT_PAY_NOTIFY_URL 不是HTTPS地址")
            warnings.append("回调地址不是HTTPS")
    else:
        print(f"   [ERROR] WECHAT_PAY_NOTIFY_URL 未配置")
        issues.append("WECHAT_PAY_NOTIFY_URL 未配置")
    
    # 5. 检查IP白名单
    print(f"\n5. 微信支付IP白名单:")
    if settings.WECHAT_PAY_IP_WHITELIST:
        print(f"   [OK] WECHAT_PAY_IP_WHITELIST = {settings.WECHAT_PAY_IP_WHITELIST}")
    else:
        print(f"   [WARN] WECHAT_PAY_IP_WHITELIST 未配置（可选，但建议配置）")
        warnings.append("IP白名单未配置（可选）")
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断结果:")
    print("=" * 60)
    
    if not issues:
        print("[OK] 所有必需配置项检查通过！")
        if warnings:
            print("\n[WARN] 警告:")
            for warning in warnings:
                print(f"   - {warning}")
    else:
        print("[ERROR] 发现配置问题:")
        for issue in issues:
            print(f"   - {issue}")
        if warnings:
            print("\n[WARN] 警告:")
            for warning in warnings:
                print(f"   - {warning}")
    
    print("\n" + "=" * 60)
    print("配置说明:")
    print("=" * 60)
    print("1. API密钥必须是32位字符串（仅包含字母和数字）")
    print("2. 在微信支付商户平台 -> API安全 -> API密钥中设置")
    print("3. 设置后需要等待几分钟生效")
    print("4. 回调地址必须是HTTPS且公网可访问")
    print("=" * 60)
    
    return len(issues) == 0


if __name__ == "__main__":
    try:
        success = check_wechat_pay_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"诊断脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

