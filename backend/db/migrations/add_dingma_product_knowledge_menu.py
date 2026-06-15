"""

菜单迁移：顶妈产品配方配置页（挂到已有「技能组装」id=17）



执行：

    cd backend && python -m db.migrations.add_dingma_product_knowledge_menu

"""

import asyncio

import sys

from pathlib import Path

from typing import Optional



from loguru import logger

from sqlalchemy import delete, or_, select



_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(_BACKEND_ROOT))



from db.session import init_db, close_db





MENU_NAME = "dingmaProductKnowledge"

# 线上已有父菜单 name=skill-assembly（id=17），勿用 skillAssembly 重复创建

SKILL_PARENT_NAMES = ("skill-assembly", "skillAssembly")

MENU_PATH = "/skill-assembly/product-knowledge"

MENU_SORT_ORDER = 3





async def _resolve_skill_parent(session) -> Optional[object]:

    """解析技能组装父菜单（优先已有 skill-assembly）"""

    from models.menu import Menu



    result = await session.execute(

        select(Menu).where(Menu.name.in_(SKILL_PARENT_NAMES)).order_by(Menu.id)

    )

    parents = list(result.scalars().all())

    if not parents:

        return None

    if len(parents) > 1:

        # 保留 id 较小的（通常是线上原始菜单 17），删除重复项

        keep = parents[0]

        for dup in parents[1:]:

            logger.warning(f"删除重复的技能组装父菜单 id={dup.id} name={dup.name}")

            await session.delete(dup)

        await session.flush()

        return keep

    return parents[0]





async def upgrade():

    """插入/修复产品配方菜单，挂到已有技能组装父级"""

    from db import session as db_session

    from models.menu import Menu

    from models.role import Role



    if db_session.async_session_maker is None:

        await db_session.init_db()



    async with db_session.async_session_maker() as session:

        parent = await _resolve_skill_parent(session)

        if parent is None:

            raise RuntimeError(

                "未找到技能组装父菜单（name=skill-assembly），请先在菜单管理中创建"

            )



        parent_id = int(parent.id)

        logger.info(f"使用技能组装父菜单 id={parent_id} name={parent.name}")



        # 清理误建的重复父菜单（无子节点、name=skillAssembly 且 id!=parent_id）

        dup_result = await session.execute(

            select(Menu).where(

                Menu.name == "skillAssembly",

                Menu.parent_id.is_(None),

                Menu.id != parent_id,

            )

        )

        for dup in dup_result.scalars().all():

            child_count = await session.execute(

                select(Menu.id).where(Menu.parent_id == dup.id).limit(1)

            )

            if child_count.scalar_one_or_none() is None:

                logger.warning(f"删除孤立重复父菜单 id={dup.id}")

                await session.delete(dup)



        existing = await session.execute(select(Menu).where(Menu.name == MENU_NAME))

        menu = existing.scalar_one_or_none()



        if menu is None:

            menu = Menu(

                parent_id=parent_id,

                name=MENU_NAME,

                path=MENU_PATH,

                component="/dingma/productKnowledge/index",

                sort_order=MENU_SORT_ORDER,

                icon="Notebook",

                title="产品配方",

                is_hide=False,

                is_full=False,

                is_affix=False,

                is_keep_alive=True,

                is_enabled=True,

            )

            session.add(menu)

            await session.flush()

            logger.info(f"已创建菜单：产品配方 (id={menu.id}, parent_id={parent_id})")

        else:

            menu.parent_id = parent_id

            menu.path = MENU_PATH

            menu.component = "/dingma/productKnowledge/index"

            menu.title = "产品配方"

            menu.icon = "Notebook"

            menu.sort_order = MENU_SORT_ORDER

            menu.is_hide = False

            menu.is_enabled = True

            await session.flush()

            logger.info(f"已修复菜单：产品配方 (id={menu.id}, parent_id={parent_id})")



        menu_id = int(menu.id)



        # 自定义角色：追加新菜单 ID，并移除已失效的 30

        roles_result = await session.execute(select(Role))

        patched_roles = 0

        for role in roles_result.scalars().all():

            if role.id == 1:

                continue

            raw = role.menu_ids

            if not raw:

                continue

            ids = [int(x) for x in raw]

            changed = False

            # 移除指向已删除菜单的 30

            if 30 in ids and menu_id != 30:

                ids = [x for x in ids if x != 30]

                changed = True

            if menu_id not in ids:

                ids.append(menu_id)

                changed = True

            if changed:

                role.menu_ids = ids

                patched_roles += 1

                logger.info(f"角色 id={role.id} menu_ids 已更新为 {ids}")



        await session.commit()

        logger.info(f"迁移完成。产品配方菜单 ID={menu_id}，父菜单 ID={parent_id}")





async def main():

    await init_db()

    try:

        await upgrade()

    finally:

        await close_db()





if __name__ == "__main__":

    asyncio.run(main())


