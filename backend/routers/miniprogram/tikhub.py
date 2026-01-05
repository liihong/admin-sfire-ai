"""
MiniProgram Tikhub Endpoints
小程序抖音分析接口
"""
import re
import httpx
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from core.deps import get_current_miniprogram_user
from core.config import settings
from utils.response import success
from utils.exceptions import BadRequestException, ServerErrorException

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

