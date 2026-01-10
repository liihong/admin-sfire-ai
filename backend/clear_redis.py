import redis

# 尝试连接本地 Redis
# 如果你的 Redis 有密码，请把 password=None 改成 password='你的密码'
# 如果端口不是 6379，请修改 port
try:
    r = redis.Redis(host='127.0.0.1', port=6379, db=0, password=None, decode_responses=True)
    
    # 检查连接是否成功
    r.ping()
    
    # 清空所有数据库的缓存
    r.flushall()
    print("✅ 成功！Redis 缓存已全部清空。")
    print("现在可以重启你的后端服务了。")

except Exception as e:
    print(f"❌ 出错了: {e}")
    print("提示：如果你没有安装 redis 库，请执行 pip install redis")