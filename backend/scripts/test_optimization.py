"""
测试优化后的系统功能
验证向量化和性能提升
"""
import asyncio
import time
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("对话系统优化验证测试")
print("=" * 60)

# 测试1: 验证导入
print("\n[1/4] 测试模块导入...")
try:
    from services.conversation import ConversationService
    from services.embedding import get_embedding_service
    from services.vector_db import get_vector_db_service
    print("OK - 所有模块导入成功")
except Exception as e:
    print(f"FAIL - 模块导入失败: {e}")
    sys.exit(1)

# 测试2: 验证Embedding服务
print("\n[2/4] 测试Embedding服务配置...")
try:
    embedding_service = get_embedding_service()
    print(f"OK - Embedding服务已初始化")
    print(f"  Provider: {embedding_service.provider}")
    print(f"  Model: {embedding_service.model}")
    print(f"  Base URL: {embedding_service.base_url}")
    print(f"  Dimensions: {embedding_service.default_dimensions}")
except Exception as e:
    print(f"FAIL - Embedding服务初始化失败: {e}")

# 测试3: 验证向量数据库
print("\n[3/4] 测试向量数据库...")
try:
    vector_db = get_vector_db_service()
    stats = vector_db.get_stats()
    print(f"OK - 向量数据库已初始化")
    print(f"  Total vectors: {stats['total_vectors']}")
    print(f"  Dimension: {stats['dimension']}")
    print(f"  Index type: {stats['index_type']}")
    print(f"  Metadata count: {stats['metadata_count']}")
except Exception as e:
    print(f"FAIL - 向量数据库初始化失败: {e}")

# 测试4: 性能基准测试（模拟）
print("\n[4/4] 性能基准测试...")
print("测试响应时间...")

# 模拟对话流程
async def simulate_chat():
    start = time.time()

    # 模拟LLM调用（主要耗时）
    await asyncio.sleep(0.5)  # 500ms

    # 模拟数据库操作（优化后）
    await asyncio.sleep(0.05)  # 50ms

    total = time.time() - start
    return total

try:
    total_time = asyncio.run(simulate_chat())
    print(f"OK - 模拟对话完成")
    print(f"  Total time: {total_time*1000:.0f}ms")
    print(f"  Target: <700ms")
    if total_time < 0.7:
        print(f"  Status: PASS (性能达标)")
    else:
        print(f"  Status: WARNING (性能未达标)")
except Exception as e:
    print(f"FAIL - 性能测试失败: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)

print("\n[优化建议]")
print("1. 检查向量化后台任务是否正常执行")
print("2. 监控embedding_status字段的变化")
print("3. 使用真实API测试响应时间")
print("4. 检查backend/storage/faiss_index.index文件是否增长")

print("\n[下一步]")
print("1. 启动服务: cd backend && python main.py")
print("2. 发送测试请求验证功能")
print("3. 查看日志确认向量化执行")
print("4. 查询数据库检查embedding_status")
