import requests
import json

def test_proxy():
    # 替换为你实际的测试地址
    url = "https://sfire.top/wavespeed/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        # 如果你的接口需要鉴权，请加上：
        "Authorization": "Bearer dbbe406d475dd73daefb0e77731d7d82628de728b1bd6a9aaf1141ef91ad7b5a" 
    }
    
    payload = {
        "model": "anthropic/claude-haiku-4-5",
        "messages": [{"role": "user", "content": "Ping"}],
        "stream": False
    }

    print(f"正在请求: {url} ...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 转发成功!")
            print(f"响应内容: {response.text}")
        else:
            print(f"❌ 请求失败!")
            # 如果返回的是 HTML，说明是 Nginx 报错；如果是 JSON，说明是后端业务报错
            if "<html>" in response.text:
                print("检测到 HTML 响应：502 错误通常来自 Nginx 代理层。")
            else:
                print(f"后端返回: {response.text}")
                
    except Exception as e:
        print(f"网络异常: {e}")

if __name__ == "__main__":
    test_proxy()