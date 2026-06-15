"""诊断 dingma 菜单不显示问题"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from db.session import init_db, close_db


async def main():
    await init_db()
    from db import session as db_session
    from models.menu import Menu
    from models.role import Role
    from models.admin_user import AdminUser
    from services.system.menu import MenuService
    from services.system.role import RoleService

    async with db_session.async_session_maker() as db:
        print("=== 技能组装相关菜单 ===")
        r = await db.execute(
            select(Menu).where(
                (Menu.id == 17)
                | (Menu.parent_id == 17)
                | (Menu.name.in_(["skillAssembly", "dingmaProductKnowledge", "skillLibrary", "agentBuilder"]))
            ).order_by(Menu.parent_id, Menu.sort_order)
        )
        menus = r.scalars().all()
        for m in menus:
            print(
                f"id={m.id} parent={m.parent_id} name={m.name} title={m.title} "
                f"path={m.path} component={m.component} enabled={m.is_enabled} hide={m.is_hide}"
            )

        print("\n=== 产品配方菜单(30) ===")
        r30 = await db.execute(select(Menu).where(Menu.id == 30))
        m30 = r30.scalar_one_or_none()
        print(m30 if m30 else "菜单 id=30 不存在（可能已删除）")

        rpk = await db.execute(select(Menu).where(Menu.name == "dingmaProductKnowledge"))
        mpk = rpk.scalar_one_or_none()
        print("by name dingmaProductKnowledge:", mpk)

        print("\n=== dingma 管理员账号 ===")
        r2 = await db.execute(
            select(AdminUser).where(AdminUser.username.like("%dingma%"))
        )
        admins = r2.scalars().all()
        for a in admins:
            print(f"id={a.id} user={a.username} tenant_id={a.tenant_id} role_id={a.role_id}")

        print("\n=== 角色 menu_ids ===")
        r3 = await db.execute(select(Role))
        for role in r3.scalars().all():
            print(f"role id={role.id} name={role.name} menu_ids={role.menu_ids}")

        if admins:
            admin = admins[0]
            role_service = RoleService(db)
            menu_service = MenuService(db)
            perms = await role_service.get_role_permissions(admin.role_id) if admin.role_id else None
            allowed = await menu_service.resolve_admin_allowed_menu_ids(
                tenant_id=admin.tenant_id,
                role_id=admin.role_id,
                role_permissions=perms,
            )
            print(f"\n=== {admin.username} 允许的菜单ID ===")
            print("allowed_ids=", sorted(allowed) if allowed is not None else "ALL(None)")

            tree = await menu_service.get_menu_tree(include_hidden=True, allowed_menu_ids=allowed)
            # 找技能组装节点
            def find_node(nodes, name):
                for n in nodes:
                    if n.get("name") == name:
                        return n
                    ch = n.get("children") or []
                    found = find_node(ch, name)
                    if found:
                        return found
                return None

            sa = find_node(tree, "skillAssembly")
            if not sa:
                # 可能 name 不是 skillAssembly
                for n in tree:
                    if "skill" in (n.get("name") or "").lower() or "技能" in (n.get("meta", {}).get("title") or ""):
                        sa = n
                        break
            print("\n=== 菜单树中的技能组装节点 ===")
            if sa:
                children = sa.get("children") or []
                print(json.dumps({
                    "name": sa.get("name"),
                    "path": sa.get("path"),
                    "children": [{"name": c.get("name"), "title": c.get("meta", {}).get("title"), "path": c.get("path"), "component": c.get("component")} for c in children]
                }, ensure_ascii=False, indent=2))
            else:
                print("未在返回树中找到技能组装节点")
                print("顶层菜单:", [n.get("name") for n in tree])

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
