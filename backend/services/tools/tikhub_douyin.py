"""
TikHub：抖音分享链接解析与单视频详情（仅 HTTP，不落盘）
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx
from loguru import logger

from core.config import settings
from utils.exceptions import BadRequestException, ServerErrorException

TIKHUB_API_BASE = "https://api.tikhub.io"

# 抖音主页链接中的 sec_uid（路径或查询参数）
_RE_SEC_UID_IN_PATH = re.compile(r"douyin\.com/user/([A-Za-z0-9_-]+)", re.I)
_RE_SEC_UID_QUERY = re.compile(r"[?&]sec_uid=([A-Za-z0-9_-]+)", re.I)


def extract_sec_uid_from_url(url: str) -> Optional[str]:
    """从抖音主页/用户页 URL 中提取 sec_uid（短链未展开时返回 None）。"""
    if not url or not url.strip():
        return None
    u = url.strip()
    m = _RE_SEC_UID_IN_PATH.search(u)
    if m:
        return m.group(1)
    m = _RE_SEC_UID_QUERY.search(u)
    if m:
        return m.group(1)
    if "v.douyin.com" in u.lower():
        return None
    return None


async def resolve_sec_uid_from_profile_url(url: str) -> str:
    """
    从抖音主页链接或分享短链解析 sec_uid。
    先直接正则；失败则跟随重定向（与 C 端 analyze-douyin 行为一致）。
    """
    raw = (url or "").strip()
    if not raw:
        raise BadRequestException(msg="请提供抖音主页或分享链接")

    extracted = _extract_douyin_url_from_paste(raw)
    candidate = extracted or raw
    normalized = _normalize_douyin_url(candidate)
    sec_uid = extract_sec_uid_from_url(normalized)
    if sec_uid:
        return sec_uid

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(15.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        ) as client:
            resp = await client.head(normalized)
            final_url = str(resp.url)
            sec_uid = extract_sec_uid_from_url(final_url)
            if sec_uid:
                return sec_uid
            # 部分站点对 HEAD 返回空，再试 GET
            resp = await client.get(normalized)
            final_url = str(resp.url)
            sec_uid = extract_sec_uid_from_url(final_url)
            if sec_uid:
                return sec_uid
            if resp.text:
                sec_uid = extract_sec_uid_from_url(resp.text[:200000])
                if sec_uid:
                    return sec_uid
    except (httpx.HTTPError, ValueError) as e:
        logger.warning(f"解析抖音主页链接失败: {e}")

    raise BadRequestException(msg="无法解析抖音链接，请使用有效的抖音用户主页链接")


# 从落地页或直链中提取作品 ID
_AWEME_PATTERNS = (
    re.compile(r"/video/(\d+)"),
    re.compile(r"aweme_id=(\d+)"),
    re.compile(r"modal_id=(\d+)"),
    re.compile(r"aweme/detail/(\d+)"),
)


def _match_aweme_id(text: str) -> Optional[str]:
    for pat in _AWEME_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def _extract_aweme_id_from_page(html: str) -> Optional[str]:
    """从落地页 HTML / 内嵌 JSON 中提取作品 ID（短链重定向后 URL 有时不含 /video/数字）。"""
    if not html:
        return None
    chunk = html[:3000000]
    patterns = (
        r'"aweme_id"\s*:\s*"(\d+)"',
        r'"aweme_id"\s*:\s*(\d+)',
        r'"itemId"\s*:\s*"(\d+)"',
        r'"awemeId"\s*:\s*"(\d+)"',
        r'"aweme_id_str"\s*:\s*"(\d+)"',
    )
    for pat in patterns:
        m = re.search(pat, chunk)
        if m:
            return m.group(1)
    return None


def _normalize_douyin_url(url: str) -> str:
    """补全协议，避免 httpx 报「missing an http/https protocol」（用户常粘贴 v.douyin.com/... 无头）。"""
    u = url.strip()
    if not u:
        return u
    lower = u.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return u
    if lower.startswith("//"):
        return "https:" + u
    return "https://" + u.lstrip("/")


def _strip_url_trailing_junk(s: str) -> str:
    """去掉链接末尾可能被粘在一起的标点或空白。"""
    return s.rstrip(".,;:!?，。；：！？）】」'\"· \t")


def _extract_douyin_url_from_paste(text: str) -> Optional[str]:
    """
    从抖音 App「复制链接」整段文案中提取可请求的 URL。
    典型格式：前缀乱码 + 标题话题 + https://v.douyin.com/xxx/ + 「复制此链接…」
    """
    t = text.replace("\r\n", "\n").strip()
    if not t:
        return None

    patterns = (
        r"https?://v\.douyin\.com/[A-Za-z0-9_/]+/?",  # 短链
        r"https?://(?:www\.)?douyin\.com/video/\d+",
        r"https?://(?:www\.)?douyin\.com/note/\d+",
        r"https?://(?:[\w-]+\.)?douyin\.com/[^\s\u4e00-\u9fff]+",  # 其它站内页
    )
    for pat in patterns:
        m = re.search(pat, t, re.I)
        if m:
            return _strip_url_trailing_junk(m.group(0))

    # 无协议：v.douyin.com/xxx
    m = re.search(
        r"(?<![\w/])((?:v|www)\.douyin\.com/[A-Za-z0-9_/]+/?)",
        t,
        re.I,
    )
    if m:
        return _strip_url_trailing_junk(m.group(1))

    # 文案中含 douyin 但路径异常：取第一个 http(s) 且含 douyin.com 的片段
    if "douyin.com" in t.lower():
        m = re.search(r"https?://[^\s]+", t)
        if m:
            u = _strip_url_trailing_junk(m.group(0))
            if "douyin.com" in u.lower():
                return u

    return None


async def resolve_aweme_id(share_url: str) -> str:
    """从抖音分享短链或长链中解析 aweme_id。"""
    raw = (share_url or "").strip()
    if not raw:
        raise BadRequestException(msg="请提供抖音链接")

    extracted = _extract_douyin_url_from_paste(raw)
    if extracted:
        raw = extracted
    else:
        hit = _match_aweme_id(raw)
        if hit:
            return hit
        raise BadRequestException(
            msg="未识别到抖音链接，请复制完整分享文案（需包含 v.douyin.com 短链或 douyin.com 视频链接）"
        )

    url = _normalize_douyin_url(raw)

    hit = _match_aweme_id(url)
    if hit:
        return hit

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(20.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        ) as client:
            resp = await client.get(url, headers={"Accept-Language": "zh-CN,zh;q=0.9"})
            final = str(resp.url)
            hit = _match_aweme_id(final)
            if hit:
                return hit
            if resp.text:
                hit = _match_aweme_id(resp.text[:500000])
                if hit:
                    return hit
                hit = _extract_aweme_id_from_page(resp.text)
                if hit:
                    return hit
    except httpx.RequestError as e:
        logger.warning(f"TikHub 前置解析链接失败: {e}")
        raise BadRequestException(msg="无法打开抖音链接，请检查网络或链接是否有效")

    raise BadRequestException(msg="无法从链接中解析作品 ID，请使用有效的抖音视频分享链接")


def _first_url_from_url_list(obj: Any) -> Optional[str]:
    if isinstance(obj, list):
        for u in obj:
            if isinstance(u, str) and u.startswith("http"):
                return u
    return None


def _walk_play_url(data: Any) -> Optional[str]:
    """从 TikHub / 抖音详情 JSON 中取可播放地址（优先含视频 CDN 的 url_list）。"""
    if isinstance(data, dict):
        if "url_list" in data:
            u = _first_url_from_url_list(data.get("url_list"))
            if u:
                return u
        for v in data.values():
            r = _walk_play_url(v)
            if r:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _walk_play_url(item)
            if r:
                return r
    return None


def _url_from_play_url_obj(obj: Any) -> Optional[str]:
    if not isinstance(obj, dict):
        return None
    u = _first_url_from_url_list(obj.get("url_list"))
    if u:
        return u
    uri = obj.get("uri")
    if isinstance(uri, str) and uri.startswith("http"):
        return uri
    return None


def _pick_audio_url_for_asr(detail: dict) -> Optional[str]:
    """
    火山「大模型录音文件识别」要求 audio.url 为可解码的音频流。
    抖音整段视频 MP4 直链按 mp3/wav 声明会 45000151；优先使用作品里的配乐/原声等音频地址。
    """
    # 1) 原声 / 配乐
    music = detail.get("music")
    if isinstance(music, dict):
        u = _url_from_play_url_obj(music.get("play_url"))
        if u:
            return u
        u = _url_from_play_url_obj(music.get("audio"))
        if u:
            return u
    # 2) 部分结构：original_sound / matched_sound
    for key in ("original_sound", "matched_sound", "music_begin_info"):
        sub = detail.get(key)
        if isinstance(sub, dict):
            u = _url_from_play_url_obj(sub.get("play_url"))
            if u:
                return u
    # 3) 视频伴音轨（若单独给出）
    video = detail.get("video")
    if isinstance(video, dict):
        ba = video.get("bit_rate_audio") or video.get("audio")
        if isinstance(ba, dict):
            u = _url_from_play_url_obj(ba.get("play_addr") or ba.get("url"))
            if u:
                return u
        # 部分返回中有单独的无画音频
        for k in ("download_addr", "play_addr_lowbr"):
            addr = video.get(k)
            if isinstance(addr, dict):
                ul = addr.get("url_list")
                if isinstance(ul, list):
                    for x in ul:
                        if isinstance(x, str) and x.startswith("http") and (
                            "audio" in x.lower()
                            or x.lower().endswith((".m4a", ".aac", ".mp3"))
                        ):
                            return x
    return None


def extract_play_urls_and_title(payload: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    从 TikHub 响应中解析地址与标题。
    返回 (优先给 ASR 的音频链, 视频播放链, 标题)；火山接口更适合音频直链。
    """
    root = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(root, dict):
        root = {}

    detail = root.get("aweme_detail") or root.get("aweme") or root.get("item") or root
    title = None
    if isinstance(detail, dict):
        title = detail.get("desc") or detail.get("share_info", {}).get("share_title")

    audio_url = None
    if isinstance(detail, dict):
        audio_url = _pick_audio_url_for_asr(detail)

    video_url = _walk_play_url(detail if isinstance(detail, dict) else root)
    return audio_url, video_url, title if isinstance(title, str) else None


def _parse_tikhub_http_error_body(text: str) -> str:
    """从 TikHub 400 响应中取出可读说明（常为 detail.message_zh）。"""
    try:
        j = json.loads(text)
        d = j.get("detail")
        if isinstance(d, dict):
            return (
                (d.get("message_zh") or d.get("message") or "").strip()
            )
    except Exception:
        pass
    return ""


def _tikhub_payload_ok(data: dict) -> bool:
    c = data.get("code")
    if c in (200, 0, None):
        return True
    if str(c) in ("200", "0"):
        return True
    return False


async def fetch_one_video(aweme_id: str) -> dict:
    """
    调用 TikHub 获取单个作品详情。
    Web 版失败时自动尝试 App V3（版权/风控场景下 Web 常返回 400）。
    """
    key = (settings.TIKHUB_API_KEY or "").strip()
    if not key:
        raise BadRequestException(msg="未配置 TikHub API Key（TIKHUB_API_KEY）")

    aid = str(aweme_id).strip()
    if not aid.isdigit():
        raise BadRequestException(msg="作品 ID 无效，请换一条抖音链接重试")

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }

    endpoints = (
        "/api/v1/douyin/web/fetch_one_video",
        "/api/v1/douyin/app/v3/fetch_one_video_v3",
    )
    last_http_err: str = ""
    last_body: str = ""

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            for path in endpoints:
                url = f"{TIKHUB_API_BASE}{path}"
                resp = await client.get(url, params={"aweme_id": aid}, headers=headers)
                last_body = resp.text
                if resp.status_code != 200:
                    hint = _parse_tikhub_http_error_body(resp.text)
                    last_http_err = hint or f"HTTP {resp.status_code}"
                    logger.warning(
                        f"TikHub {path} HTTP {resp.status_code}: {resp.text[:400]}"
                    )
                    continue
                try:
                    data = resp.json()
                except Exception:
                    continue
                if _tikhub_payload_ok(data):
                    return data
                msg = data.get("message_zh") or data.get("message") or ""
                logger.warning(f"TikHub {path} 业务异常: {data.get('code')} {msg}")
                last_http_err = msg or last_http_err
    except httpx.RequestError as e:
        logger.error(f"TikHub 请求异常: {e}")
        raise ServerErrorException(msg="网络请求失败，请稍后重试")

    detail = _parse_tikhub_http_error_body(last_body)
    user_msg = detail or last_http_err or "TikHub 无法获取该作品，请换链接或稍后重试"
    logger.error(f"TikHub 所有作品接口均失败 aweme_id={aid}: {user_msg}")
    if "400" in str(last_http_err) or "请求失败" in user_msg:
        raise BadRequestException(msg=user_msg)
    raise ServerErrorException(msg=user_msg)


def _first_cover_url(aweme: dict) -> Optional[str]:
    video = aweme.get("video")
    if not isinstance(video, dict):
        return None
    cover = video.get("cover") or video.get("origin_cover") or video.get("dynamic_cover")
    if isinstance(cover, dict):
        ul = cover.get("url_list")
        if isinstance(ul, list) and ul:
            for x in ul:
                if isinstance(x, str) and x.startswith("http"):
                    return x
    return None


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _pick_first_int(obj: dict, keys: tuple[str, ...], default: int = 0) -> int:
    for k in keys:
        if k in obj:
            v = _to_int(obj.get(k), default=-1)
            if v >= 0:
                return v
    return default


def _first_http_url(value: Any) -> str:
    if isinstance(value, str) and value.startswith("http"):
        return value
    if isinstance(value, list):
        for x in value:
            if isinstance(x, str) and x.startswith("http"):
                return x
    if isinstance(value, dict):
        ul = value.get("url_list")
        if isinstance(ul, list):
            for x in ul:
                if isinstance(x, str) and x.startswith("http"):
                    return x
        for k in ("url", "uri"):
            v = value.get(k)
            if isinstance(v, str) and v.startswith("http"):
                return v
    return ""


def _pick_aweme_core(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    for key in ("aweme", "aweme_info", "item", "data"):
        sub = raw.get(key)
        if isinstance(sub, dict):
            return sub
    return raw


def _extract_video_play_url(aweme: dict) -> str:
    video = aweme.get("video")
    if not isinstance(video, dict):
        return ""
    for k in ("play_addr", "playapi_url", "download_addr"):
        u = _first_http_url(video.get(k))
        if u:
            return u
    return ""


def _map_aweme_list_item(aweme: Any) -> Optional[dict[str, Any]]:
    if not isinstance(aweme, dict):
        return None
    core = _pick_aweme_core(aweme)
    aid = (
        core.get("aweme_id")
        or core.get("aweme_id_str")
        or core.get("id")
        or aweme.get("aweme_id")
        or aweme.get("id")
    )
    if aid is None:
        return None
    aid_str = str(aid).strip()
    if not aid_str:
        return None
    stats = core.get("statistics")
    if not isinstance(stats, dict):
        stats = core.get("stat") if isinstance(core.get("stat"), dict) else {}
    digg = stats.get("digg_count") or core.get("digg_count") or 0
    comment = stats.get("comment_count") or core.get("comment_count") or 0
    share = stats.get("share_count") or core.get("share_count") or 0
    collect = stats.get("collect_count") or core.get("collect_count") or 0
    play = stats.get("play_count") or core.get("play_count") or 0
    desc = core.get("desc") or core.get("title") or ""
    if not isinstance(desc, str):
        desc = str(desc)
    ct = core.get("create_time") or core.get("createTime") or 0
    ct_int = _to_int(ct, 0)
    duration = _to_int(core.get("duration"), 0)
    if duration > 10000:
        duration = duration // 1000
    share_info = core.get("share_info") if isinstance(core.get("share_info"), dict) else {}
    author = core.get("author") if isinstance(core.get("author"), dict) else {}
    author_avatar = _first_http_url(
        author.get("avatar_larger") or author.get("avatar_medium") or author.get("avatar_thumb")
    )
    author_follower_count = _to_int(
        author.get("follower_count")
        or author.get("fans_count")
        or author.get("mplatform_followers_count"),
        0,
    )
    author_following_count = _to_int(
        author.get("following_count")
        or author.get("follow_count")
        or author.get("following"),
        0,
    )
    author_total_favorited = _to_int(
        author.get("total_favorited")
        or author.get("favoriting_count")
        or author.get("liked_count")
        or author.get("digg_count"),
        0,
    )
    is_top_raw = (
        core.get("is_top")
        or core.get("is_pinned")
        or core.get("top")
        or 0
    )
    is_top = 1 if _to_int(is_top_raw, 0) > 0 else 0
    return {
        "aweme_id": aid_str,
        "is_top": is_top,
        "desc": desc,
        "create_time": ct_int,
        "cover_url": _first_cover_url(core) or _first_cover_url(aweme) or "",
        "digg_count": _to_int(digg, 0),
        "comment_count": _to_int(comment, 0),
        "share_count": _to_int(share, 0),
        "collect_count": _to_int(collect, 0),
        "play_count": _to_int(play, 0),
        "duration": duration,
        "author_nickname": str(author.get("nickname") or "").strip(),
        "author_avatar_url": author_avatar,
        "author_follower_count": author_follower_count,
        "author_following_count": author_following_count,
        "author_total_favorited": author_total_favorited,
        "video_url": _extract_video_play_url(core),
        "share_url": str(share_info.get("share_url") or ""),
    }


def parse_user_post_videos_tikhub_payload(payload: dict) -> tuple[list[dict[str, Any]], int, bool]:
    """
    解析 TikHub 用户作品列表响应为统一结构。
    """
    root = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(root, dict):
        return [], 0, False
    raw_list = (
        root.get("aweme_list")
        or root.get("aweme_lite_items")
        or root.get("aweme_infos")
        or root.get("videos")
        or root.get("items")
        or root.get("list")
        or []
    )
    if not isinstance(raw_list, list):
        raw_list = []
    items: list[dict[str, Any]] = []
    for aweme in raw_list:
        m = _map_aweme_list_item(aweme)
        if m:
            items.append(m)
    next_cursor = root.get("max_cursor") or root.get("cursor") or 0
    try:
        next_cursor_i = int(next_cursor)
    except (TypeError, ValueError):
        next_cursor_i = 0
    hm = root.get("has_more")
    if hm is None:
        has_more = False
    elif isinstance(hm, bool):
        has_more = hm
    else:
        try:
            has_more = bool(int(hm))
        except (TypeError, ValueError):
            has_more = bool(hm)
    return items, next_cursor_i, has_more


async def fetch_douyin_user_nickname(sec_uid: str) -> str:
    """调用 TikHub user/info 取昵称，失败返回空串。"""
    p = await fetch_douyin_user_profile(sec_uid)
    return str(p.get("nickname") or "")


async def fetch_douyin_user_profile(sec_uid: str) -> dict[str, Any]:
    """调用 TikHub user/info 获取账号资料。失败返回空字段结构。"""
    empty = {
        "nickname": "",
        "avatar_url": "",
        "signature": "",
        "follower_count": 0,
        "following_count": 0,
        "total_favorited": 0,
        "aweme_count": 0,
    }
    key = (settings.TIKHUB_API_KEY or "").strip()
    if not key:
        return empty
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            url = f"{TIKHUB_API_BASE}/api/v1/douyin/user/info"
            resp = await client.get(
                url, headers=headers, params={"sec_uid": sec_uid.strip()}
            )
            if resp.status_code != 200:
                return empty
            data = resp.json()
            if not _tikhub_payload_ok(data):
                return empty
            payload = data.get("data", {}) if isinstance(data.get("data"), dict) else {}
            uinfo = (
                payload.get("user")
                or payload.get("user_info")
                or payload.get("author")
                or {}
            )
            if isinstance(uinfo, dict):
                # 兼容不同接口字段命名
                follower_count = _pick_first_int(
                    uinfo,
                    (
                        "follower_count",
                        "fans_count",
                        "mplatform_followers_count",
                    ),
                    0,
                )
                following_count = _pick_first_int(
                    uinfo,
                    ("following_count", "follow_count", "following"),
                    0,
                )
                total_favorited = _pick_first_int(
                    uinfo,
                    (
                        "total_favorited",
                        "favoriting_count",
                        "liked_count",
                        "digg_count",
                    ),
                    0,
                )
                aweme_count = _pick_first_int(
                    uinfo,
                    ("aweme_count", "video_count", "item_count"),
                    0,
                )
                # 部分返回把统计信息放在外层
                stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
                if follower_count == 0 and isinstance(stats, dict):
                    follower_count = _pick_first_int(stats, ("follower_count", "fans_count"), 0)
                if following_count == 0 and isinstance(stats, dict):
                    following_count = _pick_first_int(stats, ("following_count", "follow_count"), 0)
                if aweme_count == 0 and isinstance(stats, dict):
                    aweme_count = _pick_first_int(stats, ("aweme_count", "video_count", "item_count"), 0)
                return {
                    "nickname": str(uinfo.get("nickname") or "").strip(),
                    "avatar_url": _first_http_url(
                        uinfo.get("avatar_larger")
                        or uinfo.get("avatar_medium")
                        or uinfo.get("avatar_thumb")
                        or uinfo.get("avatar")
                    ),
                    "signature": str(uinfo.get("signature") or "").strip(),
                    "follower_count": follower_count,
                    "following_count": following_count,
                    "total_favorited": total_favorited,
                    "aweme_count": aweme_count,
                }
    except Exception as e:
        logger.warning(f"TikHub user/info 失败 sec_uid={sec_uid[:8]}...: {e}")
    return empty


async def fetch_user_post_videos(
    sec_uid: str,
    max_cursor: int = 0,
    count: int = 20,
) -> tuple[list[dict[str, Any]], int, bool]:
    """
    拉取用户作品列表（分页）。Web 与 App V3 接口依次尝试。
    返回 (items, next_cursor, has_more)。
    """
    key = (settings.TIKHUB_API_KEY or "").strip()
    if not key:
        raise BadRequestException(msg="未配置 TikHub API Key（TIKHUB_API_KEY）")

    su = sec_uid.strip()
    if not su:
        raise BadRequestException(msg="sec_uid 无效")

    c = max(1, min(int(count), 80))
    mc = max(0, int(max_cursor))

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    # 与 TikHub 文档一致：sec_user_id 为主参数名
    param_variants = (
        {"sec_user_id": su, "max_cursor": mc, "count": c},
        {"sec_uid": su, "max_cursor": mc, "count": c},
    )
    endpoints = (
        "/api/v1/douyin/web/fetch_user_post_videos",
        "/api/v1/douyin/app/v3/fetch_user_post_videos_v3",
    )
    last_body = ""
    last_http_err = ""

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            for path in endpoints:
                for params in param_variants:
                    url = f"{TIKHUB_API_BASE}{path}"
                    resp = await client.get(url, headers=headers, params=params)
                    last_body = resp.text
                    if resp.status_code != 200:
                        last_http_err = _parse_tikhub_http_error_body(resp.text) or f"HTTP {resp.status_code}"
                        logger.warning(
                            f"TikHub {path} HTTP {resp.status_code}: {resp.text[:400]}"
                        )
                        continue
                    try:
                        data = resp.json()
                    except Exception:
                        continue
                    if _tikhub_payload_ok(data):
                        items, nc, hm = parse_user_post_videos_tikhub_payload(data)
                        return items, nc, hm
                    msg = data.get("message_zh") or data.get("message") or ""
                    logger.warning(f"TikHub {path} 业务异常: {data.get('code')} {msg}")
                    last_http_err = msg or last_http_err
    except httpx.RequestError as e:
        logger.error(f"TikHub 用户作品列表请求异常: {e}")
        raise ServerErrorException(msg="网络请求失败，请稍后重试")

    detail = _parse_tikhub_http_error_body(last_body)
    user_msg = detail or last_http_err or "TikHub 无法获取该账号作品列表，请稍后重试"
    logger.error(f"TikHub 用户作品列表失败 sec_uid={su[:12]}...: {user_msg}")
    if "400" in str(last_http_err) or "请求失败" in user_msg:
        raise BadRequestException(msg=user_msg)
    raise ServerErrorException(msg=user_msg)


async def resolve_play_url_from_share(share_url: str) -> tuple[list[str], Optional[str], str]:
    """
    分享链接 -> (按顺序尝试的媒体 URL 列表, 标题, aweme_id)
    优先音频链，其次视频链（火山对 MP4 可能仍失败）。
    """
    aweme_id = await resolve_aweme_id(share_url)
    raw = await fetch_one_video(aweme_id)
    audio_u, video_u, title = extract_play_urls_and_title(raw)
    ordered: list[str] = []
    if audio_u:
        ordered.append(audio_u)
    if video_u and video_u not in ordered:
        ordered.append(video_u)
    if not ordered:
        raise BadRequestException(msg="TikHub 未返回可播放地址，请换一条链接或稍后重试")
    return ordered, title, aweme_id
