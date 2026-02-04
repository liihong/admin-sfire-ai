"""
Client Tikhub Endpoints
C端抖音分析接口（小程序 & PC官网）
支持抖音账号分析、IP画像提取、热点榜单等功能
"""
import re
import httpx
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from core.config import settings
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException
from loguru import logger

router = APIRouter()


# ============== Request/Response Models ==============

class AnalyzeDouyinRequest(BaseModel):
    """抖音账号分析请求"""
    url: str = Field(..., description="抖音主页链接或分享链接")


class DouyinProfileData(BaseModel):
    """抖音账号画像数据"""
    nickname: str = Field(default="", description="抖音昵称")
    signature: str = Field(default="", description="抖音简介")
    avatar_url: str = Field(default="", description="头像 URL")
    industry_guess: str = Field(default="通用", description="推测赛道")
    keywords: List[str] = Field(default_factory=list, description="提取的关键词")
    tone_guess: str = Field(default="专业亲和", description="推测语气风格")
    target_audience_guess: str = Field(default="", description="推测目标受众")
    follower_count: Optional[int] = Field(default=None, description="粉丝数")
    video_count: Optional[int] = Field(default=None, description="作品数")


class AnalyzeDouyinResponse(BaseModel):
    """抖音账号分析响应"""
    success: bool = True
    data: Optional[DouyinProfileData] = None
    message: str = ""


# ============== Helper Functions ==============

def extract_sec_uid_from_url(url: str) -> Optional[str]:
    """从抖音链接中提取 sec_uid"""
    match = re.search(r'douyin\.com/user/([A-Za-z0-9_-]+)', url)
    if match:
        return match.group(1)
    
    if 'v.douyin.com' in url:
        return None
    
    return None


def guess_industry_from_content(nickname: str, signature: str, keywords: List[str]) -> str:
    """根据内容推测行业赛道"""
    content = f"{nickname} {signature} {' '.join(keywords)}".lower()
    
    industry_keywords = {
        "医疗健康": ["医生", "健康", "医院", "诊所", "中医", "养生", "保健", "医疗", "护士", "药"],
        "教育培训": ["老师", "教育", "培训", "学习", "考试", "课程", "知识", "讲师", "教授"],
        "金融理财": ["理财", "投资", "股票", "基金", "金融", "保险", "财务", "经济"],
        "科技互联网": ["科技", "互联网", "程序员", "代码", "AI", "人工智能", "数码", "电脑"],
        "电商零售": ["带货", "好物", "推荐", "测评", "开箱", "种草", "购物"],
        "餐饮美食": ["美食", "吃货", "探店", "做饭", "烹饪", "厨师", "料理", "餐厅"],
        "美妆护肤": ["美妆", "护肤", "化妆", "彩妆", "美容", "皮肤", "素颜"],
        "母婴育儿": ["宝宝", "育儿", "宝妈", "母婴", "孕期", "儿童", "早教"],
        "体育健身": ["健身", "运动", "减肥", "瘦身", "教练", "跑步", "瑜伽", "增肌"],
        "职场成长": ["职场", "工作", "创业", "管理", "领导", "团队", "成长"],
        "情感心理": ["情感", "心理", "恋爱", "婚姻", "治愈", "解压"],
    }
    
    for industry, kws in industry_keywords.items():
        for kw in kws:
            if kw in content:
                return industry
    
    return "通用"


def guess_tone_from_signature(signature: str) -> str:
    """根据简介推测语气风格"""
    if not signature:
        return "专业亲和"
    
    tone_indicators = {
        "幽默风趣": ["哈哈", "搞笑", "段子", "快乐", "开心", "乐"],
        "温暖治愈": ["治愈", "温暖", "陪伴", "温柔", "暖心"],
        "犀利直接": ["真话", "直言", "犀利", "不装", "真实"],
        "严肃正式": ["专业", "权威", "官方", "正经"],
        "激情澎湃": ["加油", "冲", "奋斗", "热血", "激情"],
    }
    
    for tone, indicators in tone_indicators.items():
        for indicator in indicators:
            if indicator in signature:
                return tone
    
    return "专业亲和"


def extract_keywords_from_signature(signature: str) -> List[str]:
    """从简介中提取关键词"""
    if not signature:
        return []
    
    keywords = []
    parts = re.split(r'[,，、|/\s]+', signature)
    
    for part in parts:
        part = part.strip()
        if 2 <= len(part) <= 10 and not part.startswith(('#', '@')):
            keywords.append(part)
    
    return keywords[:5]


async def mock_analyze_douyin(url: str) -> AnalyzeDouyinResponse:
    """Mock 数据用于演示和开发测试"""
    import hashlib
    import asyncio
    
    await asyncio.sleep(2)
    
    url_hash = hashlib.md5(url.encode()).hexdigest()
    
    mock_profiles = [
        {
            "nickname": "李医生说健康",
            "signature": "三甲医院主治医师 | 健康科普 | 让医学知识更简单",
            "industry_guess": "医疗健康",
            "keywords": ["健康科普", "医学知识", "养生", "疾病预防"],
            "tone_guess": "专业亲和",
            "target_audience_guess": "25-55岁关注健康的用户",
        },
        {
            "nickname": "小美爱分享",
            "signature": "好物种草官 | 每天发现生活小确幸 ✨",
            "industry_guess": "电商零售",
            "keywords": ["好物推荐", "生活分享", "种草", "测评"],
            "tone_guess": "温暖治愈",
            "target_audience_guess": "18-35岁女性用户",
        },
        {
            "nickname": "职场老王",
            "signature": "10年HR老兵 | 说点职场真话 | 简历指导",
            "industry_guess": "职场成长",
            "keywords": ["职场", "面试", "简历", "升职加薪"],
            "tone_guess": "犀利直接",
            "target_audience_guess": "职场新人和求职者",
        },
        {
            "nickname": "码农小张",
            "signature": "全栈开发 | 技术干货 | 带你入门编程",
            "industry_guess": "科技互联网",
            "keywords": ["编程", "代码", "程序员", "技术"],
            "tone_guess": "幽默风趣",
            "target_audience_guess": "编程爱好者和技术从业者",
        },
    ]
    
    index = int(url_hash[:2], 16) % len(mock_profiles)
    profile = mock_profiles[index]
    
    profile_data = DouyinProfileData(
        nickname=profile["nickname"],
        signature=profile["signature"],
        avatar_url="https://p3.douyinpic.com/aweme/100x100/aweme-avatar/mock_avatar.jpeg",
        industry_guess=profile["industry_guess"],
        keywords=profile["keywords"],
        tone_guess=profile["tone_guess"],
        target_audience_guess=profile["target_audience_guess"],
        follower_count=int(url_hash[:5], 16) % 500000 + 10000,
        video_count=int(url_hash[5:8], 16) % 200 + 20
    )
    
    return AnalyzeDouyinResponse(
        success=True,
        data=profile_data,
        message="采集成功（演示数据）"
    )


# ============== API Endpoints ==============

@router.post("/analyze-douyin", response_model=AnalyzeDouyinResponse)
async def analyze_douyin_profile(
    request: AnalyzeDouyinRequest,
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """分析抖音账号，提取 IP 画像信息"""
    url = request.url.strip()
    
    if not url:
        raise BadRequestException("请提供抖音链接")
    
    tikhub_api_key = settings.TIKHUB_API_KEY
    
    if not tikhub_api_key:
        return await mock_analyze_douyin(url)
    
    try:
        sec_uid = extract_sec_uid_from_url(url)
        
        if not sec_uid:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                response = await client.head(url)
                final_url = str(response.url)
                sec_uid = extract_sec_uid_from_url(final_url)
        
        if not sec_uid:
            raise BadRequestException("无法解析抖音链接，请检查链接格式")
        
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {tikhub_api_key}",
                "Content-Type": "application/json"
            }
            
            api_url = f"https://api.tikhub.io/api/v1/douyin/user/info?sec_uid={sec_uid}"
            
            response = await client.get(api_url, headers=headers)
            
            if response.status_code != 200:
                return await mock_analyze_douyin(url)
            
            data = response.json()
            user_info = data.get("data", {}).get("user", {})
            
            nickname = user_info.get("nickname", "")
            signature = user_info.get("signature", "")
            avatar_url = user_info.get("avatar_larger", {}).get("url_list", [""])[0]
            follower_count = user_info.get("follower_count")
            video_count = user_info.get("aweme_count")
            
            keywords = extract_keywords_from_signature(signature)
            industry_guess = guess_industry_from_content(nickname, signature, keywords)
            tone_guess = guess_tone_from_signature(signature)
            
            target_audience = ""
            if follower_count:
                if follower_count > 1000000:
                    target_audience = "广泛用户群体"
                elif follower_count > 100000:
                    target_audience = "垂直领域关注者"
                else:
                    target_audience = "精准目标用户"
            
            profile_data = DouyinProfileData(
                nickname=nickname,
                signature=signature,
                avatar_url=avatar_url,
                industry_guess=industry_guess,
                keywords=keywords,
                tone_guess=tone_guess,
                target_audience_guess=target_audience,
                follower_count=follower_count,
                video_count=video_count
            )
            
            return AnalyzeDouyinResponse(
                success=True,
                data=profile_data,
                message="采集成功"
            )
            
    except httpx.TimeoutException:
        raise ServerErrorException("请求超时，请稍后重试")
    except Exception as e:
        return await mock_analyze_douyin(url)


# ============== 热点榜单相关 Models ==============

class HotspotItem(BaseModel):
    """热点榜单项"""
    rank: int = Field(..., description="排名")
    title: str = Field(..., description="热点标题")
    hot_value: Optional[int] = Field(None, description="热度值")
    word: Optional[str] = Field(None, description="关键词")
    label: Optional[str] = Field(None, description="标签")
    url: Optional[str] = Field(None, description="链接")
    update_time: Optional[str] = Field(None, description="更新时间")


class HotspotListResponse(BaseModel):
    """热点榜单响应"""
    list: List[HotspotItem] = Field(default_factory=list, description="热点列表")
    update_time: Optional[str] = Field(None, description="榜单更新时间")


async def mock_hotspot_list() -> HotspotListResponse:
    """Mock 热点榜单数据用于演示和开发测试"""
    import asyncio
    await asyncio.sleep(1)
    
    mock_list = [
        {"rank": 1, "title": "AI技术突破新进展", "hot_value": 1250000, "word": "AI技术", "label": "科技", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 2, "title": "健康生活方式分享", "hot_value": 980000, "word": "健康生活", "label": "生活", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 3, "title": "职场技能提升技巧", "hot_value": 850000, "word": "职场技能", "label": "职场", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 4, "title": "美食探店新发现", "hot_value": 720000, "word": "美食探店", "label": "美食", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 5, "title": "旅行攻略分享", "hot_value": 650000, "word": "旅行攻略", "label": "旅行", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 6, "title": "时尚穿搭指南", "hot_value": 580000, "word": "时尚穿搭", "label": "时尚", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 7, "title": "教育学习方法", "hot_value": 520000, "word": "教育学习", "label": "教育", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 8, "title": "理财投资建议", "hot_value": 480000, "word": "理财投资", "label": "财经", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 9, "title": "情感关系话题", "hot_value": 450000, "word": "情感关系", "label": "情感", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"rank": 10, "title": "运动健身心得", "hot_value": 420000, "word": "运动健身", "label": "运动", "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]
    
    return HotspotListResponse(
        list=[HotspotItem(**item) for item in mock_list],
        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@router.get("/hotspot-list", summary="获取抖音热点榜单")
async def get_hotspot_list(
    billboard_type: str = Query("hot", description="榜单类型：hot-热点榜, music-音乐榜, topic-话题榜"),
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取抖音最近一小时热点榜单
    
    使用 TikHub API 获取抖音热点榜单数据
    如果 API Key 未配置或请求失败，返回 Mock 数据
    
    路径：GET /api/v1/client/tikhub/hotspot-list
    """
    tikhub_api_key = settings.TIKHUB_API_KEY
    
    if not tikhub_api_key:
        # 如果没有配置 API Key，返回 Mock 数据
        mock_data = await mock_hotspot_list()
        return success(data=mock_data.model_dump(), msg="获取成功（演示数据）")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {tikhub_api_key}",
                "Content-Type": "application/json"
            }
            
            # TikHub API 热点榜单接口
            # 根据文档，抖音热点榜单接口路径为 /api/v1/douyin/billboard/hot
            api_url = f"https://api.tikhub.io/api/v1/douyin/billboard/{billboard_type}"
            
            response = await client.get(api_url, headers=headers)
            
            if response.status_code != 200:
                # API 请求失败，返回 Mock 数据
                mock_data = await mock_hotspot_list()
                return success(data=mock_data.model_dump(), msg="获取成功（演示数据）")
            
            data = response.json()
            
            # 解析 TikHub API 返回的数据结构
            # 根据 TikHub 文档，返回格式可能为：{"code": 200, "data": {...}, "message": "..."}
            api_data = data.get("data", {})
            
            # 提取热点列表
            hotspot_list = []
            if isinstance(api_data, dict):
                # 尝试不同的可能字段名
                items = api_data.get("list", []) or api_data.get("data", []) or api_data.get("billboard", [])
                
                for idx, item in enumerate(items[:20], start=1):  # 最多返回20条
                    # 根据实际 API 返回的字段进行映射
                    hotspot_item = HotspotItem(
                        rank=item.get("rank", idx),
                        title=item.get("title", "") or item.get("word", "") or item.get("keyword", "") or "",
                        hot_value=item.get("hot_value") or item.get("hotValue") or item.get("hot", None),
                        word=item.get("word", "") or item.get("keyword", ""),
                        label=item.get("label", "") or item.get("tag", ""),
                        url=item.get("url", ""),
                        update_time=item.get("update_time", "") or item.get("updateTime", "")
                    )
                    hotspot_list.append(hotspot_item)
            
            # 如果没有解析到数据，返回 Mock 数据
            if not hotspot_list:
                mock_data = await mock_hotspot_list()
                return success(data=mock_data.model_dump(), msg="获取成功（演示数据）")
            
            result = HotspotListResponse(
                list=hotspot_list,
                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            return success(data=result.model_dump(), msg="获取成功")
            
    except httpx.TimeoutException:
        raise ServerErrorException("请求超时，请稍后重试")
    except Exception as e:
        # 发生异常时返回 Mock 数据，确保功能可用
        mock_data = await mock_hotspot_list()
        return success(data=mock_data.model_dump(), msg="获取成功（演示数据）")


@router.get("/hotspot-agent-id", summary="获取热点功能对应的智能体ID")
async def get_hotspot_agent_id(
    current_user: User = Depends(get_current_miniprogram_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热点功能对应的智能体ID
    
    根据系统配置获取热点功能使用的智能体ID
    优先使用配置的 HOTSPOT_AGENT_ID，如果未配置则通过名称查找
    
    路径：GET /api/v1/client/tikhub/hotspot-agent-id
    """
    from sqlalchemy import select, or_
    from models.agent import Agent
    
    agent_id = None
    
    # 优先使用配置的agent ID
    if settings.HOTSPOT_AGENT_ID:
        agent_id = int(settings.HOTSPOT_AGENT_ID)
        logger.info(f"尝试查找热点Agent: ID={agent_id}")
        
        # 查询是否存在该Agent（不限制状态）
        result = await db.execute(
            select(Agent).filter(Agent.id == agent_id)
        )
        agent_check = result.scalar_one_or_none()
        
        if agent_check:
            # 系统自用智能体可以绕过上架检查，普通智能体必须上架
            if agent_check.is_system == 1 or agent_check.status == 1:
                return success(data={"agent_id": agent_id}, msg="获取成功")
            else:
                logger.warning(
                    f"Agent ID={agent_id} 既不是系统自用（is_system=0）也未上架（status=0），"
                    f"将尝试通过名称查找"
                )
        else:
            logger.warning(f"未找到Agent ID={agent_id}，将尝试通过名称查找")
    
    # 如果配置的ID不存在或不可用，通过名称查找
    logger.info("尝试通过名称'蹭热点'或'热点文案'查找Agent")
    result = await db.execute(
        select(Agent).filter(
            or_(
                Agent.name == "蹭热点",
                Agent.name == "热点文案",
                Agent.name.like("%热点%")
            ),
            # 系统自用智能体可以绕过上架检查，普通智能体必须上架
            or_(Agent.is_system == 1, Agent.status == 1)
        ).order_by(Agent.created_at.desc())
    )
    agent = result.scalar_one_or_none()
    
    if agent:
        logger.info(f"通过名称找到热点Agent: ID={agent.id}, name={agent.name}")
        return success(data={"agent_id": agent.id}, msg="获取成功")
    
    # 如果还是找不到，返回错误
    raise BadRequestException("未找到热点功能对应的智能体，请联系管理员配置")

