"""
数据字典初始化脚本
初始化行业赛道和语气风格等字典数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import session as db_session
from models.dictionary import Dictionary, DictionaryItem


# 初始字典数据
INITIAL_DICTIONARIES = [
    {
        "dict_code": "industry",
        "dict_name": "行业赛道",
        "description": "项目所属的行业领域",
        "sort_order": 1,
        "items": [
            {"item_value": "通用", "item_label": "通用", "sort_order": 0},
            {"item_value": "医疗健康", "item_label": "医疗健康", "sort_order": 1},
            {"item_value": "教育培训", "item_label": "教育培训", "sort_order": 2},
            {"item_value": "金融理财", "item_label": "金融理财", "sort_order": 3},
            {"item_value": "科技互联网", "item_label": "科技互联网", "sort_order": 4},
            {"item_value": "电商零售", "item_label": "电商零售", "sort_order": 5},
            {"item_value": "餐饮美食", "item_label": "餐饮美食", "sort_order": 6},
            {"item_value": "旅游出行", "item_label": "旅游出行", "sort_order": 7},
            {"item_value": "房产家居", "item_label": "房产家居", "sort_order": 8},
            {"item_value": "美妆护肤", "item_label": "美妆护肤", "sort_order": 9},
            {"item_value": "母婴育儿", "item_label": "母婴育儿", "sort_order": 10},
            {"item_value": "体育健身", "item_label": "体育健身", "sort_order": 11},
            {"item_value": "娱乐影视", "item_label": "娱乐影视", "sort_order": 12},
            {"item_value": "游戏动漫", "item_label": "游戏动漫", "sort_order": 13},
            {"item_value": "法律咨询", "item_label": "法律咨询", "sort_order": 14},
            {"item_value": "职场成长", "item_label": "职场成长", "sort_order": 15},
            {"item_value": "情感心理", "item_label": "情感心理", "sort_order": 16},
            {"item_value": "三农乡村", "item_label": "三农乡村", "sort_order": 17},
            {"item_value": "其他", "item_label": "其他", "sort_order": 99},
        ]
    },
    {
        "dict_code": "tone",
        "dict_name": "语气风格",
        "description": "内容创作的语气风格",
        "sort_order": 2,
        "items": [
            {"item_value": "专业亲和", "item_label": "专业亲和", "sort_order": 0},
            {"item_value": "幽默风趣", "item_label": "幽默风趣", "sort_order": 1},
            {"item_value": "严肃正式", "item_label": "严肃正式", "sort_order": 2},
            {"item_value": "温暖治愈", "item_label": "温暖治愈", "sort_order": 3},
            {"item_value": "犀利直接", "item_label": "犀利直接", "sort_order": 4},
            {"item_value": "娓娓道来", "item_label": "娓娓道来", "sort_order": 5},
            {"item_value": "激情澎湃", "item_label": "激情澎湃", "sort_order": 6},
            {"item_value": "冷静理性", "item_label": "冷静理性", "sort_order": 7},
        ]
    },
]


async def init_dictionary(session: AsyncSession, dict_data: dict) -> Dictionary:
    """
    初始化单个字典类型及其字典项
    
    Args:
        session: 数据库会话
        dict_data: 字典数据
    
    Returns:
        Dictionary: 创建的字典类型对象
    """
    items_data = dict_data.pop("items", [])
    
    # 创建字典类型
    dict_obj = Dictionary(
        dict_code=dict_data["dict_code"],
        dict_name=dict_data["dict_name"],
        description=dict_data.get("description"),
        sort_order=dict_data.get("sort_order", 0),
        is_enabled=True,
    )
    
    session.add(dict_obj)
    await session.flush()
    
    logger.info(f"创建字典类型: {dict_obj.dict_code} - {dict_obj.dict_name}")
    
    # 创建字典项
    for item_data in items_data:
        item = DictionaryItem(
            dict_id=dict_obj.id,
            item_value=item_data["item_value"],
            item_label=item_data["item_label"],
            description=item_data.get("description"),
            sort_order=item_data.get("sort_order", 0),
            is_enabled=True,
        )
        session.add(item)
        logger.debug(f"  - 创建字典项: {item.item_label}")
    
    await session.flush()
    return dict_obj


async def init_dictionaries(session: AsyncSession) -> None:
    """
    初始化所有字典数据
    """
    logger.info("开始初始化数据字典...")
    
    for dict_data in INITIAL_DICTIONARIES:
        # 检查字典类型是否已存在
        result = await session.execute(
            select(Dictionary).where(Dictionary.dict_code == dict_data["dict_code"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.warning(f"字典类型 '{dict_data['dict_code']}' 已存在，跳过")
            continue
        
        # 创建字典类型及其字典项
        await init_dictionary(session, dict_data.copy())
    
    await session.commit()
    logger.info("数据字典初始化完成")


async def main():
    """
    主函数
    """
    logger.info("=" * 50)
    logger.info("开始初始化数据字典...")
    logger.info("=" * 50)
    
    # 初始化数据库连接
    await db_session.init_db()
    
    # 创建数据库表（如果不存在）
    await db_session.create_tables()
    
    # 获取数据库会话（通过模块访问全局变量）
    async with db_session.async_session_maker() as session:
        try:
            await init_dictionaries(session)
            
            logger.info("=" * 50)
            logger.info("数据字典初始化完成！")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            await session.rollback()
            raise
    
    # 关闭数据库连接
    await db_session.close_db()


if __name__ == "__main__":
    asyncio.run(main())

