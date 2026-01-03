# -*- coding: utf-8 -*-
"""
MySQL 数据库初始化脚本
创建所有表结构并为每个表插入 mock 数据
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import init_db, async_session_maker, close_db, create_tables
from app.models.user import User, UserLevel
from app.models.menu import Menu
from app.models.compute import ComputeLog, ComputeType
from app.models.llm_model import LLMModel
from app.core.security import hash_password


# ========== Mock 数据定义 ==========

# 用户 Mock 数据
MOCK_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "level": UserLevel.PARTNER,
        "balance": Decimal("10000.0000"),
        "frozen_balance": Decimal("0.0000"),
        "nickname": "系统管理员",
        "phone": "13800138000",
        "avatar": "https://avatars.githubusercontent.com/u/1",
        "is_active": True,
    },
    {
        "username": "user001",
        "password": "123456",
        "level": UserLevel.MEMBER,
        "balance": Decimal("5000.5000"),
        "frozen_balance": Decimal("100.0000"),
        "nickname": "张三",
        "phone": "13800138001",
        "avatar": "https://avatars.githubusercontent.com/u/2",
        "is_active": True,
        "parent_id": 1,  # 上级是 admin
    },
    {
        "username": "user002",
        "password": "123456",
        "level": UserLevel.MEMBER,
        "balance": Decimal("3000.0000"),
        "frozen_balance": Decimal("50.0000"),
        "nickname": "李四",
        "phone": "13800138002",
        "avatar": "https://avatars.githubusercontent.com/u/3",
        "is_active": True,
        "parent_id": 1,
    },
    {
        "username": "user003",
        "password": "123456",
        "level": UserLevel.NORMAL,
        "balance": Decimal("1000.0000"),
        "frozen_balance": Decimal("0.0000"),
        "nickname": "王五",
        "phone": "13800138003",
        "avatar": "https://avatars.githubusercontent.com/u/4",
        "is_active": True,
        "parent_id": 2,  # 上级是 user001
    },
    {
        "username": "user004",
        "password": "123456",
        "level": UserLevel.NORMAL,
        "balance": Decimal("500.0000"),
        "frozen_balance": Decimal("0.0000"),
        "nickname": "赵六",
        "phone": "13800138004",
        "avatar": "https://avatars.githubusercontent.com/u/5",
        "is_active": True,
        "parent_id": 2,
    },
    {
        "username": "user005",
        "password": "123456",
        "level": UserLevel.PARTNER,
        "balance": Decimal("8000.0000"),
        "frozen_balance": Decimal("200.0000"),
        "nickname": "钱七",
        "phone": "13800138005",
        "avatar": "https://avatars.githubusercontent.com/u/6",
        "is_active": True,
        "parent_id": None,
    },
]

# 菜单 Mock 数据
MOCK_MENUS = [
    # 首页/控制台
    {
        "name": "home",
        "path": "/home/index",
        "component": "/home/index",
        "title": "数据看板",
        "icon": "HomeFilled",
        "sort_order": 0,
        "is_affix": True,
        "is_keep_alive": True,
    },
    # 用户管理
    {
        "name": "user",
        "path": "/user",
        "redirect": "/user/index",
        "title": "用户管理",
        "icon": "User",
        "sort_order": 10,
        "children": [
            {
                "name": "userManage",
                "path": "/user/index",
                "component": "/user/index",
                "title": "用户列表",
                "icon": "Menu",
                "sort_order": 0,
            },
        ],
    },
    # 财务管理
    {
        "name": "finance",
        "path": "/finance",
        "redirect": "/finance/compute-log",
        "title": "财务管理",
        "icon": "Money",
        "sort_order": 20,
        "children": [
            {
                "name": "computeLog",
                "path": "/finance/compute-log",
                "component": "/finance/compute-log",
                "title": "算力明细",
                "icon": "Menu",
                "sort_order": 0,
            },
        ],
    },
    # 小程序管理
    {
        "name": "miniprogram",
        "path": "/miniprogram",
        "redirect": "/miniprogram/users",
        "title": "小程序管理",
        "icon": "Iphone",
        "sort_order": 30,
        "children": [
            {
                "name": "miniprogramUserManage",
                "path": "/miniprogram/users",
                "component": "/system/userManage/index",
                "title": "用户管理",
                "icon": "User",
                "sort_order": 0,
            },
            {
                "name": "bannerManage",
                "path": "/miniprogram/banner",
                "component": "/miniprogram/banner/index",
                "title": "Banner管理",
                "icon": "Picture",
                "sort_order": 10,
            },
            {
                "name": "homeConfig",
                "path": "/miniprogram/config",
                "component": "/miniprogram/config/index",
                "title": "首页配置",
                "icon": "Setting",
                "sort_order": 20,
            },
        ],
    },
    # 系统管理
    {
        "name": "system",
        "path": "/system",
        "redirect": "/system/menuMange",
        "title": "系统管理",
        "icon": "Tools",
        "sort_order": 100,
        "children": [
            {
                "name": "menuMange",
                "path": "/system/menuMange",
                "component": "/system/menuMange/index",
                "title": "菜单管理",
                "icon": "Menu",
                "sort_order": 0,
            },
            {
                "name": "userManage",
                "path": "/system/userManage",
                "component": "/system/userManage/index",
                "title": "用户管理",
                "icon": "User",
                "sort_order": 5,
            },
            {
                "name": "roleManage",
                "path": "/system/roleManage",
                "component": "/system/roleManage/index",
                "title": "角色管理",
                "icon": "Menu",
                "sort_order": 10,
            },
            {
                "name": "llmModelManage",
                "path": "/system/llmModelManage",
                "component": "/system/llmModelManage/index",
                "title": "大模型管理",
                "icon": "Cpu",
                "sort_order": 15,
            },
        ],
    },
]


async def create_menu(
    session: AsyncSession,
    menu_data: dict,
    parent_id: int = None,
) -> Menu:
    """
    递归创建菜单
    
    Args:
        session: 数据库会话
        menu_data: 菜单数据
        parent_id: 父菜单ID
    
    Returns:
        Menu: 创建的菜单对象
    """
    children_data = menu_data.pop("children", None)
    
    # 检查菜单是否已存在
    result = await session.execute(
        select(Menu).where(Menu.name == menu_data["name"])
    )
    existing = result.scalar_one_or_none()
    if existing:
        logger.info(f"菜单 {menu_data['name']} 已存在，跳过创建")
        return existing
    
    # 创建菜单
    menu = Menu(
        parent_id=parent_id,
        name=menu_data.get("name"),
        path=menu_data.get("path"),
        component=menu_data.get("component"),
        redirect=menu_data.get("redirect"),
        title=menu_data.get("title"),
        icon=menu_data.get("icon", "Menu"),
        sort_order=menu_data.get("sort_order", 0),
        is_link=menu_data.get("is_link", ""),
        is_hide=menu_data.get("is_hide", False),
        is_full=menu_data.get("is_full", False),
        is_affix=menu_data.get("is_affix", False),
        is_keep_alive=menu_data.get("is_keep_alive", True),
        is_enabled=True,
    )
    
    session.add(menu)
    await session.flush()
    
    logger.info(f"创建菜单: {menu.title} (name={menu.name})")
    
    # 递归创建子菜单
    if children_data:
        for child_data in children_data:
            await create_menu(session, child_data.copy(), menu.id)
    
    return menu


async def init_users(session: AsyncSession) -> dict:
    """
    初始化用户数据
    
    Returns:
        dict: 已创建用户的字典，key 为 username
    """
    logger.info("开始初始化用户数据...")
    
    created_users = {}  # 存储已创建的用户，用于关联 parent_id
    
    for user_data in MOCK_USERS:
        # 检查用户是否已存在
        result = await session.execute(
            select(User).where(User.username == user_data["username"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.warning(f"用户 {user_data['username']} 已存在，跳过创建")
            created_users[user_data["username"]] = existing
            continue
        
        # 处理 parent_id（如果存在）
        parent_id = user_data.get("parent_id")
        if parent_id:
            # parent_id 是数字索引（1表示第一个用户），需要找到对应的用户
            # 找到 parent_id 对应的用户名
            parent_index = parent_id - 1  # 转换为索引（1 -> 0, 2 -> 1, ...）
            if 0 <= parent_index < len(MOCK_USERS):
                parent_username = MOCK_USERS[parent_index]["username"]
                if parent_username in created_users:
                    parent_id = created_users[parent_username].id
                else:
                    logger.warning(f"用户 {user_data['username']} 的上级用户 {parent_username} 尚未创建，跳过 parent_id")
                    parent_id = None
            else:
                parent_id = None
        
        # 创建用户
        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            level=user_data["level"],
            balance=user_data["balance"],
            frozen_balance=user_data["frozen_balance"],
            nickname=user_data.get("nickname"),
            phone=user_data.get("phone"),
            avatar=user_data.get("avatar"),
            is_active=user_data.get("is_active", True),
            is_deleted=False,
            parent_id=parent_id,
        )
        
        session.add(user)
        await session.flush()
        
        created_users[user_data["username"]] = user
        logger.info(f"创建用户: {user.username} (level={user.level.value}, balance={user.balance}, parent_id={parent_id})")
    
    await session.commit()
    logger.info(f"用户数据初始化完成，共创建 {len(created_users)} 个用户")
    
    return created_users


async def init_menus(session: AsyncSession) -> None:
    """
    初始化菜单数据
    """
    logger.info("开始初始化菜单数据...")
    
    # 检查是否已有菜单数据
    result = await session.execute(select(Menu).limit(1))
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("菜单数据已存在，跳过初始化")
        return
    
    for menu_data in MOCK_MENUS:
        await create_menu(session, menu_data.copy())
    
    await session.commit()
    logger.info("菜单数据初始化完成")


async def init_compute_logs(session: AsyncSession) -> None:
    """
    初始化算力变动记录数据
    """
    logger.info("开始初始化算力变动记录数据...")
    
    # 获取所有用户
    result = await session.execute(select(User))
    users = result.scalars().all()
    
    if not users:
        logger.warning("没有用户数据，跳过算力记录初始化")
        return
    
    # 检查是否已有记录
    result = await session.execute(select(ComputeLog).limit(1))
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning("算力变动记录已存在，跳过初始化")
        return
    
    # 为每个用户创建几条算力变动记录
    now = datetime.now()
    logs_created = 0
    
    for user in users:
        current_balance = user.balance
        
        # 为每个用户创建 5-10 条记录
        import random
        num_logs = random.randint(5, 10)
        
        for i in range(num_logs):
            # 随机选择变动类型
            if i == 0:
                # 第一条记录通常是充值
                log_type = ComputeType.RECHARGE
                amount = Decimal(str(random.randint(100, 5000)))
            elif i == 1:
                # 第二条可能是奖励
                log_type = ComputeType.REWARD
                amount = Decimal(str(random.randint(10, 500)))
            elif i == 2:
                # 第三条可能是消耗
                log_type = ComputeType.CONSUME
                amount = -Decimal(str(random.randint(10, 200)))
            elif i == 3:
                # 第四条可能是佣金
                log_type = ComputeType.COMMISSION
                amount = Decimal(str(random.randint(5, 100)))
            else:
                # 其他随机类型
                types = [
                    ComputeType.RECHARGE,
                    ComputeType.CONSUME,
                    ComputeType.REWARD,
                    ComputeType.COMMISSION,
                ]
                log_type = random.choice(types)
                if log_type in [ComputeType.CONSUME]:
                    amount = -Decimal(str(random.randint(10, 200)))
                else:
                    amount = Decimal(str(random.randint(10, 500)))
            
            before_balance = current_balance
            after_balance = before_balance + amount
            current_balance = after_balance
            
            # 生成备注
            remarks = {
                ComputeType.RECHARGE: f"充值算力 {amount}",
                ComputeType.CONSUME: f"使用算力 {abs(amount)}",
                ComputeType.REWARD: f"系统奖励 {amount}",
                ComputeType.COMMISSION: f"分销佣金 {amount}",
            }
            remark = remarks.get(log_type, f"算力变动 {amount}")
            
            # 创建时间（最近30天内随机）
            days_ago = random.randint(0, 30)
            created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            log = ComputeLog(
                user_id=user.id,
                type=log_type,
                amount=amount,
                before_balance=before_balance,
                after_balance=after_balance,
                remark=remark,
                order_id=f"ORD{user.id}{i:04d}" if log_type == ComputeType.RECHARGE else None,
                source="admin",
            )
            
            # 设置创建时间
            log.created_at = created_at
            
            session.add(log)
            logs_created += 1
    
    await session.commit()
    logger.info(f"算力变动记录初始化完成，共创建 {logs_created} 条记录")


# 默认大模型数据
DEFAULT_LLM_MODELS = [
    {
        "name": "GPT-4o",
        "model_id": "gpt-4o",
        "provider": "openai",
        "api_key": None,  # 留空，由用户配置
        "base_url": None,  # 使用默认 URL
        "is_enabled": True,
        "sort_order": 0,
        "remark": "OpenAI 最新多模态模型"
    },
    {
        "name": "GPT-4o Mini",
        "model_id": "gpt-4o-mini",
        "provider": "openai",
        "api_key": None,
        "base_url": None,
        "is_enabled": True,
        "sort_order": 1,
        "remark": "OpenAI 更快速的 GPT-4o 版本"
    },
    {
        "name": "Claude 3.5 Sonnet",
        "model_id": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "api_key": None,
        "base_url": None,
        "is_enabled": True,
        "sort_order": 10,
        "remark": "Anthropic 最新的 Claude 3.5 模型"
    },
    {
        "name": "Claude 3 Opus",
        "model_id": "claude-3-opus-20240229",
        "provider": "anthropic",
        "api_key": None,
        "base_url": None,
        "is_enabled": True,
        "sort_order": 11,
        "remark": "Anthropic Claude 3 Opus 模型"
    },
    {
        "name": "DeepSeek Chat",
        "model_id": "deepseek-chat",
        "provider": "deepseek",
        "api_key": None,
        "base_url": None,
        "is_enabled": True,
        "sort_order": 20,
        "remark": "DeepSeek 对话模型"
    },
    {
        "name": "DeepSeek Coder",
        "model_id": "deepseek-coder",
        "provider": "deepseek",
        "api_key": None,
        "base_url": None,
        "is_enabled": True,
        "sort_order": 21,
        "remark": "DeepSeek 代码专用模型"
    },
]


async def init_llm_models(session: AsyncSession) -> None:
    """
    初始化大模型数据
    """
    logger.info("开始初始化大模型数据...")
    
    models_created = 0
    
    for model_data in DEFAULT_LLM_MODELS:
        # 检查模型是否已存在
        result = await session.execute(
            select(LLMModel).where(LLMModel.model_id == model_data["model_id"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"大模型 {model_data['model_id']} 已存在，跳过创建")
            continue
        
        # 创建模型
        model = LLMModel(
            name=model_data["name"],
            model_id=model_data["model_id"],
            provider=model_data["provider"],
            api_key=model_data["api_key"],
            base_url=model_data["base_url"],
            is_enabled=model_data["is_enabled"],
            sort_order=model_data["sort_order"],
            remark=model_data["remark"],
        )
        
        session.add(model)
        models_created += 1
        logger.info(f"创建大模型: {model.name} ({model.model_id})")
    
    await session.commit()
    logger.info(f"大模型初始化完成，共创建 {models_created} 个模型")


async def main():
    """
    主函数：执行数据库初始化
    """
    logger.info("=" * 60)
    logger.info("开始 MySQL 数据库初始化...")
    logger.info("=" * 60)
    
    try:
        # 初始化数据库连接
        logger.info("正在连接 MySQL 数据库...")
        await init_db()
        logger.info("数据库连接成功")
        
        # 创建数据库表（如果不存在）
        logger.info("正在创建数据库表...")
        await create_tables()
        logger.info("数据库表创建完成")
        
        # 获取数据库会话（重新导入以确保使用正确的会话工厂）
        from app.db.session import async_session_maker
        if async_session_maker is None:
            raise RuntimeError("async_session_maker 未初始化")
        
        # 获取数据库会话
        async with async_session_maker() as session:
            try:
                # 初始化用户数据（返回用户字典供后续使用）
                users_dict = await init_users(session)
                
                # 初始化菜单数据
                await init_menus(session)
                
                # 初始化算力变动记录数据
                await init_compute_logs(session)
                
                # 初始化大模型数据
                await init_llm_models(session)
                
                logger.info("=" * 60)
                logger.info("MySQL 数据库初始化完成！")
                logger.info("=" * 60)
                logger.info("默认管理员账号: admin / admin123")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"初始化失败: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"数据库初始化过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        # 关闭数据库连接
        await close_db()
        logger.info("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())

