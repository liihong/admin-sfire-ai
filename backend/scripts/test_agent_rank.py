"""
测试智能体排行功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from db.session import async_session_maker
from models.conversation import Conversation
from models.agent import Agent
from services.dashboard import DashboardService


async def test_agent_rank():
    """测试智能体排行功能"""
    print("=" * 50)
    print("测试智能体排行功能")
    print("=" * 50)

    # 初始化数据库连接
    from db.session import init_db
    await init_db()

    from db.session import async_session_maker

    async with async_session_maker() as db:
        # 1. 检查数据库中的数据
        print("\n1. 检查数据库数据...")

        # 检查智能体数量
        result = await db.execute(select(func.count(Agent.id)))
        agent_count = result.scalar()
        print(f"   智能体总数: {agent_count}")

        # 检查会话数量
        result = await db.execute(select(func.count(Conversation.id)))
        conv_count = result.scalar()
        print(f"   会话总数: {conv_count}")

        # 检查有agent_id的会话数量
        result = await db.execute(
            select(func.count(Conversation.id)).where(Conversation.agent_id.isnot(None))
        )
        conv_with_agent = result.scalar()
        print(f"   关联智能体的会话数: {conv_with_agent}")

        # 2. 测试统计查询
        print("\n2. 测试统计查询...")
        result = await db.execute(
            select(
                Conversation.agent_id,
                func.count(Conversation.id).label("call_count")
            ).where(
                Conversation.agent_id.isnot(None)
            ).group_by(
                Conversation.agent_id
            ).order_by(
                func.count(Conversation.id).desc()
            ).limit(5)
        )

        stats = result.fetchall()
        print(f"   统计结果数量: {len(stats)}")
        if stats:
            print("   Top 5 智能体调用统计:")
            for row in stats:
                print(f"     Agent ID: {row.agent_id}, 调用次数: {row.call_count}")

        # 3. 获取智能体详细信息
        if stats:
            agent_ids = [row.agent_id for row in stats]
            agents_result = await db.execute(
                select(Agent).where(Agent.id.in_(agent_ids))
            )
            agents = agents_result.scalars().all()

            print("\n3. 智能体详细信息:")
            for agent in agents:
                call_count = next((r.call_count for r in stats if r.agent_id == agent.id), 0)
                print(f"   - {agent.name} (ID: {agent.id}, icon: {agent.icon}, 调用次数: {call_count})")

        # 4. 测试 DashboardService.get_agent_rank 方法
        print("\n4. 测试 DashboardService.get_agent_rank 方法...")
        dashboard_service = DashboardService(db)
        agent_rank = await dashboard_service.get_agent_rank(limit=5)

        print(f"   返回结果数量: {len(agent_rank)}")
        if agent_rank:
            print("   智能体排行:")
            for idx, item in enumerate(agent_rank, 1):
                print(f"     {idx}. {item.name} - {item.call_count} 次")

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_agent_rank())
