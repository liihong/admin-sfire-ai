"""
调试脚本：检查项目人设信息
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings
from models.project import Project


async def debug_project(project_id: int):
    """调试项目人设信息"""
    # 创建数据库连接
    engine = create_async_engine(settings.MYSQL_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as db:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            print(f"❌ 项目 {project_id} 不存在")
            return
        
        print("=" * 60)
        print(f"[Project] ID: {project.id}")
        print(f"[Project] Name: {project.name}")
        print(f"[Project] Industry: {project.industry}")
        print(f"[Project] User ID: {project.user_id}")
        print("=" * 60)
        print(f"[Persona Settings] Raw Value:")
        print(f"   Type: {type(project.persona_settings)}")
        print(f"   Content: {project.persona_settings}")
        print("=" * 60)
        
        # 测试 get_persona_settings_dict 方法
        persona = project.get_persona_settings_dict()
        print(f"[get_persona_settings_dict()] Return:")
        print(f"   Type: {type(persona)}")
        print(f"   Content: {persona}")
        print("=" * 60)
        
        # 测试 build_ip_persona_prompt 函数
        from routers.client.creation import build_ip_persona_prompt
        ip_persona_prompt = build_ip_persona_prompt(project)
        print(f"[build_ip_persona_prompt] Generated Prompt:")
        print("-" * 40)
        print(ip_persona_prompt if ip_persona_prompt else "(EMPTY)")
        print("-" * 40)
        
        if not ip_persona_prompt:
            print("[WARNING] Persona prompt is empty!")
        else:
            print(f"[OK] Persona prompt length: {len(ip_persona_prompt)} characters")


if __name__ == "__main__":
    project_id = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    asyncio.run(debug_project(project_id))

