#!/usr/bin/env python3
"""
API连接测试脚本
测试API接口和nginx中转服务的可用性
"""
import httpx
import json
import sys
import os
from datetime import datetime
from typing import Optional

# Windows控制台编码修复
if sys.platform == 'win32':
    try:
        # 尝试设置UTF-8编码
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    except:
        pass


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str):
    """打印成功消息"""
    try:
        print(f"{Colors.GREEN}[OK] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[OK] {msg}")


def print_error(msg: str):
    """打印错误消息"""
    try:
        print(f"{Colors.RED}[ERROR] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[ERROR] {msg}")


def print_warning(msg: str):
    """打印警告消息"""
    try:
        print(f"{Colors.YELLOW}[WARN] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[WARN] {msg}")


def print_info(msg: str):
    """打印信息消息"""
    try:
        print(f"{Colors.BLUE}[INFO] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[INFO] {msg}")


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


async def test_basic_connectivity(url: str) -> bool:
    """
    测试基本连接性（GET请求）
    
    Args:
        url: 要测试的URL
        
    Returns:
        是否连接成功
    """
    print_section("1. 基本连接测试 (GET请求)")
    print_info(f"测试URL: {url}")
    
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            verify=False,  # 不验证SSL证书
            follow_redirects=True,
            trust_env=False
        ) as client:
            # 尝试GET请求（测试nginx是否响应）
            try:
                response = await client.get(url)
                print_success(f"HTTP连接成功")
                print_info(f"  - 状态码: {response.status_code}")
                print_info(f"  - 响应头: {dict(response.headers)}")
                
                # 检查是否是nginx响应
                server_header = response.headers.get('Server', '').lower()
                if 'nginx' in server_header:
                    print_success(f"检测到nginx服务器: {response.headers.get('Server')}")
                else:
                    print_warning(f"服务器标识: {response.headers.get('Server', '未知')}")
                
                # 尝试读取响应内容（限制长度）
                try:
                    content = response.text[:500]
                    print_info(f"  - 响应内容预览: {content[:200]}...")
                except:
                    pass
                
                return True
                
            except httpx.ConnectError as e:
                print_error(f"连接失败: {str(e)}")
                if hasattr(e, '__cause__') and e.__cause__:
                    print_error(f"  底层错误: {type(e.__cause__).__name__}: {str(e.__cause__)}")
                print_warning("可能原因:")
                print_warning("  1. 服务器未启动或不可达")
                print_warning("  2. 防火墙阻止连接")
                print_warning("  3. DNS解析失败")
                print_warning("  4. 端口被占用或未开放")
                return False
                
            except httpx.TimeoutException as e:
                print_error(f"连接超时: {str(e)}")
                print_warning("可能原因:")
                print_warning("  1. 网络延迟过高")
                print_warning("  2. 服务器响应慢")
                print_warning("  3. 防火墙规则限制")
                return False
                
            except Exception as e:
                print_error(f"未知错误: {type(e).__name__}: {str(e)}")
                return False
                
    except Exception as e:
        print_error(f"客户端初始化失败: {type(e).__name__}: {str(e)}")
        return False


async def test_ssl_certificate(url: str) -> bool:
    """
    测试SSL证书
    
    Args:
        url: 要测试的URL
        
    Returns:
        SSL证书是否有效
    """
    print_section("2. SSL证书测试")
    
    try:
        # 先测试不验证证书的连接
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            verify=False,
            trust_env=False
        ) as client:
            try:
                response = await client.get(url)
                print_success("不验证证书的连接成功")
            except Exception as e:
                print_error(f"不验证证书的连接失败: {str(e)}")
                return False
        
        # 再测试验证证书的连接
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            verify=True,  # 验证SSL证书
            trust_env=False
        ) as client:
            try:
                response = await client.get(url)
                print_success("SSL证书验证通过")
                return True
            except httpx.ConnectError as e:
                # 如果是连接错误，可能是证书问题
                if 'certificate' in str(e).lower() or 'ssl' in str(e).lower():
                    print_warning("SSL证书验证失败（但连接可用）")
                    print_warning("  这通常不影响使用，因为代码中设置了 verify=False")
                    return False
                else:
                    # 其他连接错误
                    print_warning("无法验证SSL证书（连接错误）")
                    return False
            except Exception as e:
                print_warning(f"SSL证书验证时出错: {str(e)}")
                return False
                
    except Exception as e:
        print_error(f"SSL测试失败: {type(e).__name__}: {str(e)}")
        return False


async def test_chat_completions_api(
    url: str,
    api_key: Optional[str] = None,
    gate_key: str = "Huoyuan2026"
) -> bool:
    """
    测试Chat Completions API接口
    
    Args:
        url: API URL
        api_key: API密钥（可选）
        gate_key: 网关认证密钥
        
    Returns:
        是否测试成功
    """
    print_section("3. Chat Completions API测试 (POST请求)")
    print_info(f"测试URL: {url}")
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "X-My-Gate-Key": gate_key,
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        print_info(f"使用API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
    else:
        print_warning("未提供API Key，将测试无认证请求")
    
    # 构建测试请求体
    test_payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message."
            }
        ],
        "max_tokens": 10,
        "temperature": 0.7,
        "stream": False
    }
    
    print_info(f"请求体大小: {len(json.dumps(test_payload))} bytes")
    
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            verify=False,
            http2=True,  # 启用HTTP/2
            trust_env=False
        ) as client:
            try:
                print_info("发送POST请求...")
                response = await client.post(
                    url,
                    headers=headers,
                    json=test_payload
                )
                
                print_info(f"收到响应:")
                print_info(f"  - 状态码: {response.status_code}")
                print_info(f"  - 响应头: {dict(response.headers)}")
                
                # 检查响应状态
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        print_success("API请求成功！")
                        print_info(f"  - 响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}")
                        return True
                    except json.JSONDecodeError:
                        print_warning("响应不是有效的JSON格式")
                        print_info(f"  - 响应内容: {response.text[:500]}")
                        return False
                        
                elif response.status_code == 401:
                    print_error("认证失败 (401 Unauthorized)")
                    print_warning("可能原因:")
                    print_warning("  1. API Key无效或缺失")
                    print_warning("  2. 网关认证密钥(X-My-Gate-Key)无效")
                    print_info(f"  - 响应内容: {response.text[:500]}")
                    return False
                    
                elif response.status_code == 404:
                    print_error("接口不存在 (404 Not Found)")
                    print_warning("可能原因:")
                    print_warning("  1. URL路径错误")
                    print_warning("  2. nginx配置错误")
                    print_info(f"  - 响应内容: {response.text[:500]}")
                    return False
                    
                elif response.status_code == 502:
                    print_error("网关错误 (502 Bad Gateway)")
                    print_warning("可能原因:")
                    print_warning("  1. nginx无法连接到后端服务")
                    print_warning("  2. 后端服务未启动")
                    print_info(f"  - 响应内容: {response.text[:500]}")
                    return False
                    
                elif response.status_code == 503:
                    print_error("服务不可用 (503 Service Unavailable)")
                    print_warning("可能原因:")
                    print_warning("  1. 服务过载")
                    print_warning("  2. 维护中")
                    print_info(f"  - 响应内容: {response.text[:500]}")
                    return False
                    
                else:
                    print_error(f"请求失败，状态码: {response.status_code}")
                    print_info(f"  - 响应内容: {response.text[:500]}")
                    return False
                    
            except httpx.ConnectError as e:
                print_error(f"连接失败: {str(e)}")
                if hasattr(e, '__cause__') and e.__cause__:
                    print_error(f"  底层错误: {type(e.__cause__).__name__}: {str(e.__cause__)}")
                print_warning("可能原因:")
                print_warning("  1. 服务器未启动")
                print_warning("  2. 防火墙阻止")
                print_warning("  3. DNS解析失败")
                return False
                
            except httpx.TimeoutException as e:
                print_error(f"请求超时: {str(e)}")
                print_warning("可能原因:")
                print_warning("  1. 服务器响应慢")
                print_warning("  2. 网络延迟高")
                return False
                
            except Exception as e:
                print_error(f"未知错误: {type(e).__name__}: {str(e)}")
                import traceback
                print_error(f"  详细错误:\n{traceback.format_exc()}")
                return False
                
    except Exception as e:
        print_error(f"客户端初始化失败: {type(e).__name__}: {str(e)}")
        return False


async def test_nginx_health(base_url: str) -> bool:
    """
    测试nginx健康检查端点（如果存在）
    
    Args:
        base_url: 基础URL（不含路径）
        
    Returns:
        是否找到健康检查端点
    """
    print_section("4. Nginx健康检查")
    
    # 常见的健康检查路径
    health_paths = [
        "/health",
        "/healthz",
        "/ping",
        "/status",
        "/nginx_status",
    ]
    
    found_health = False
    
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(5.0, connect=3.0),
        verify=False,
        trust_env=False
    ) as client:
        for path in health_paths:
            try:
                url = f"{base_url.rstrip('/')}{path}"
                response = await client.get(url)
                if response.status_code == 200:
                    print_success(f"找到健康检查端点: {url}")
                    print_info(f"  响应: {response.text[:200]}")
                    found_health = True
            except:
                pass
    
    if not found_health:
        print_warning("未找到常见的健康检查端点")
        print_info("这通常不影响API功能")
    
    return found_health


async def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("  API连接测试工具")
    print("="*60)
    print(f"{Colors.RESET}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 从命令行参数或默认值获取URL
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    else:
        api_url = "https://47.82.181.13/api/v1/chat/completions"
    
    # 从命令行参数获取API Key（可选）
    api_key = None
    if len(sys.argv) > 2:
        api_key = sys.argv[2]
    
    # 从环境变量获取API Key（如果未通过参数提供）
    if not api_key:
        import os
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_COLLECT_API_KEY")
    
    # 提取基础URL（从完整URL中提取协议+域名+端口）
    from urllib.parse import urlparse
    parsed = urlparse(api_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    print_info(f"目标URL: {api_url}")
    print_info(f"基础URL: {base_url}")
    if api_key:
        print_info(f"API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    print()
    
    # 执行测试
    results = {}
    
    # 1. 基本连接测试
    results['basic_connectivity'] = await test_basic_connectivity(base_url)
    
    # 2. SSL证书测试
    results['ssl_certificate'] = await test_ssl_certificate(base_url)
    
    # 3. Nginx健康检查
    results['nginx_health'] = await test_nginx_health(base_url)
    
    # 4. API接口测试
    results['api_test'] = await test_chat_completions_api(api_url, api_key)
    
    # 输出测试总结
    print_section("测试总结")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print_info(f"总测试数: {total_tests}")
    print_info(f"通过: {passed_tests}")
    print_info(f"失败: {total_tests - passed_tests}")
    print()
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        test_display = {
            'basic_connectivity': '基本连接',
            'ssl_certificate': 'SSL证书',
            'nginx_health': 'Nginx健康检查',
            'api_test': 'API接口'
        }.get(test_name, test_name)
        print(f"  {status} - {test_display}")
    
    print()
    
    # 最终判断
    if results['basic_connectivity'] and results['api_test']:
        print_success("服务基本可用！")
        return 0
    else:
        print_error("服务存在问题，请检查上述错误信息")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

