# -*- coding: utf-8 -*-
"""
生成长图版使用说明海报（PNG），文案与 generate_user_manual_docx.py 保持一致。

截图「自动」嵌入方式：
  将真机或微信开发者工具截取的页面图，放入同目录 poster_assets/screenshots/，
  文件名与 screenshots_manifest.json 中一致（如 discover.png），重新运行本脚本即可。

无法在无微信环境下代您截屏；若未放置图片，海报中会显示虚线占位框与提示文字。
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

# ---------- 视觉常量 ----------
W = 1080
PAD_X = 56
PAD_Y = 48
CONTENT_W = W - PAD_X * 2
BG = (250, 250, 252)
CARD = (255, 255, 255)
TEXT = (44, 44, 48)
TEXT_MUTED = (102, 102, 110)
ACCENT = (243, 112, 33)
ACCENT_LIGHT = (255, 245, 238)
LINE = (230, 232, 238)

FONT_SIZES = {
    "title": 46,
    "h1": 34,
    "h2": 28,
    "body": 24,
    "small": 20,
    "caption": 18,
}


def _font_path_bold() -> str:
    for p in (
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\msyhbd.ttf",
        r"C:\Windows\Fonts\simhei.ttf",
    ):
        if Path(p).exists():
            return p
    return r"C:\Windows\Fonts\msyh.ttc"


def _font_path_regular() -> str:
    for p in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simfang.ttf",
    ):
        if Path(p).exists():
            return p
    return _font_path_bold()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _font_path_bold() if bold else _font_path_regular()
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def text_lines(text: str, font: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw, max_w: int) -> list[str]:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    lines: list[str] = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            test = cur + ch
            bbox = draw.textbbox((0, 0), test, font=font)
            tw = bbox[2] - bbox[0]
            if tw <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def line_height(font: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw) -> int:
    bbox = draw.textbbox((0, 0), "国Ag", font=font)
    return int((bbox[3] - bbox[1]) * 1.35)


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int],
    max_w: int,
    x0: int = PAD_X,
) -> int:
    lh = line_height(font, draw)
    lines = text_lines(text, font, draw, max_w)
    yy = y
    for line in lines:
        draw.text((x0, yy), line, font=font, fill=color)
        yy += lh
    return yy


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    y: int,
    items: list[str],
    font: ImageFont.FreeTypeFont,
    max_w: int,
    x0: int = PAD_X,
) -> int:
    lh = line_height(font, draw)
    indent = 36
    yy = y
    for item in items:
        wrapped = text_lines(item, font, draw, max_w - indent)
        for i, line in enumerate(wrapped):
            if i == 0:
                draw.text((x0, yy), "•", font=font, fill=ACCENT)
            draw.text((x0 + indent, yy), line, font=font, fill=TEXT)
            yy += lh
    return yy


def draw_table(
    draw: ImageDraw.ImageDraw,
    y: int,
    rows: list[tuple[str, str]],
    font: ImageFont.FreeTypeFont,
    font_small: ImageFont.FreeTypeFont,
    max_w: int,
    x0: int = PAD_X,
) -> int:
    """长图中用「标题 + 说明」上下排布的卡片，避免两列错位。"""
    yy = y
    cell_pad = 18
    lh_b = line_height(font, draw)
    lh_s = line_height(font_small, draw)
    inner_w = max_w - cell_pad * 2
    for a, b in rows:
        lines_a = text_lines(a, font, draw, inner_w)
        lines_b = text_lines(b, font_small, draw, inner_w)
        box_h = cell_pad * 2 + len(lines_a) * lh_b + 10 + len(lines_b) * lh_s
        draw.rounded_rectangle(
            [x0, yy, x0 + max_w, yy + box_h],
            radius=14,
            fill=CARD,
            outline=LINE,
            width=1,
        )
        cy = yy + cell_pad
        for line in lines_a:
            draw.text((x0 + cell_pad, cy), line, font=font, fill=ACCENT)
            cy += lh_b
        cy += 6
        for line in lines_b:
            draw.text((x0 + cell_pad, cy), line, font=font_small, fill=TEXT)
            cy += lh_s
        yy += box_h + 14
    return yy


def load_screenshot(path: Path) -> Image.Image | None:
    if not path.exists():
        alt = path.with_suffix(".jpg")
        if alt.exists():
            path = alt
        else:
            alt2 = path.with_suffix(".jpeg")
            if alt2.exists():
                path = alt2
            else:
                return None
    try:
        return Image.open(path).convert("RGB")
    except OSError:
        return None


def paste_screenshot(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    y: int,
    shot: Image.Image | None,
    title: str,
    hint: str,
    max_w: int,
    x0: int = PAD_X,
) -> int:
    gap = 20
    font_cap = load_font(FONT_SIZES["caption"], bold=True)
    font_hint = load_font(FONT_SIZES["caption"] - 2)
    lh = line_height(font_cap, draw)
    lh_h = line_height(font_hint, draw)

    yy = y
    draw.text((x0, yy), title, font=font_cap, fill=ACCENT)
    yy += lh + 8

    inner_w = max_w
    max_h = 2000

    if shot is not None:
        sw, sh = shot.size
        scale = min(inner_w / sw, max_h / sh, 1.0)
        nw = max(1, int(sw * scale))
        nh = max(1, int(sh * scale))
        shot_r = shot.resize((nw, nh), Image.Resampling.LANCZOS)
        paste_x = x0 + (inner_w - nw) // 2
        img.paste(shot_r, (paste_x, yy))
        draw.rounded_rectangle(
            [paste_x - 2, yy - 2, paste_x + nw + 2, yy + nh + 2],
            radius=18,
            outline=LINE,
            width=2,
        )
        yy += nh + gap
    else:
        ph = 300
        draw.rounded_rectangle([x0, yy, x0 + inner_w, yy + ph], radius=16, fill=(248, 248, 250), outline=LINE, width=2)
        dash = "（未检测到截图：请将对应页面截图放入 poster_assets/screenshots/ 后重新运行脚本）"
        block = (hint + "\n" + dash).strip()
        wrapped = text_lines(block, font_hint, draw, inner_w - 40)
        yy_hint = yy + 28
        for line in wrapped:
            draw.text((x0 + 20, yy_hint), line, font=font_hint, fill=TEXT_MUTED)
            yy_hint += lh_h
        yy += ph + gap

    return yy


def build_content() -> list[dict[str, Any]]:
    """与 Word 版结构一致的内容块。"""
    return [
        {"type": "hero"},
        {
            "type": "body",
            "text": (
                "欢迎使用「火源灵感火花」小程序。本程序帮您用人工智能辅助做文案、聊创作、管理自己的账号形象（IP）。"
                "屏幕最下方有三个主按钮：发现、IP 操作台、我的，点一下即可切换。\n\n"
                "说明：小程序里有时显示「火源文案」，与「火源灵感火花」指同一款产品。"
                "文中所说「AI 助手」即为您服务的智能程序，会按您选的入口帮您写稿、对话。"
            ),
        },
        {"type": "h1", "text": "一、第一次用？先看这三条"},
        {
            "type": "bullets",
            "items": [
                "在微信里打开本小程序后，用底部三个按钮就能用到主要功能。",
                "部分功能需要您用手机号登录（按页面提示授权即可）。例如：完整走完「创建 IP 项目」、使用「我的灵感」等。"
                "若暂时不想登录，部分页面可选择「先去逛逛」，先浏览首页。",
                "若您已是会员，可在「我的」里查看「算力」并充值；具体权益以「开通会员」页面展示为准。",
            ],
        },
        {"type": "h1", "text": "二、「发现」页能做什么"},
        {"type": "body", "text": "点底部「发现」，进入首页。"},
        {
            "type": "table",
            "rows": [
                ("顶部图片轮播", "展示活动图、品牌介绍等，会随运营更新。"),
                ("通知条", "有重要通知时会在上方显示，请留意。"),
                (
                    "功能快捷入口",
                    "常见入口包括：脚本洗稿、图文封面、爆款标题、全能对话等（具体以您手机上显示为准）。"
                    "点进去一般会打开「AI 对话」，由 AI 助手按该入口帮您处理。",
                ),
                ("运营干货", "可浏览文章列表，点标题看正文。"),
                ("最近落地", "展示近期案例或动态，以页面实际内容为准。"),
            ],
        },
        {"type": "body", "text": "在「发现」页右上角可将小程序分享给微信好友或分享到朋友圈。"},
        {"type": "shot", "slot_id": "discover"},
        {"type": "h1", "text": "三、「IP 操作台」怎么用"},
        {
            "type": "body",
            "text": (
                "「IP」可以理解为您在短视频/自媒体上的人设与风格。"
                "在这里按「项目」管理：每个项目有一套独立的人设说明，方便您针对不同账号或选题分开操盘。"
            ),
        },
        {"type": "h2", "text": "3.1 还没有项目时"},
        {"type": "body", "text": "页面会提示您创建项目。按提示填写「IP 信息定位」问卷（分几步完成），用于生成您的定位说明。"},
        {"type": "h2", "text": "3.2 已有多个项目时"},
        {"type": "body", "text": "会先看项目列表，请点选当前要用的那一个。之后也可在页面顶部等处「切换项目」。"},
        {"type": "h2", "text": "3.3 已经选好项目后（主操作界面）"},
        {
            "type": "table",
            "rows": [
                ("顶部", "显示当前项目名称、您的信息与积分等；可切换项目。"),
                ("人设卡片", "展示当前项目的人设摘要；点进去可「微调人设」（与新建时步骤相同，保存后更新本项目）。"),
                (
                    "今天拍点啥",
                    "一块块分类入口，由后台配置。点某一类后，通常会进入「AI 文案生成」帮您写稿，或跳到其他页面（如热点榜）。"
                    "若提示「功能开发中」，说明该入口尚在升级，请稍后再试。",
                ),
                ("快捷指令库", "常用指令卡片，点进去进入「AI 文案生成」，并带上适合该指令的提示，方便您直接开写。"),
                ("历史对话", "列出与创作相关的聊天记录；点某一条可接着聊。"),
                ("在列表处向下拉", "可刷新对话列表和快捷入口。"),
                (
                    "右下角加号按钮",
                    "打开「灵感捕捉」：把突然想到的点子记下来，可加标签，并会保存到「我的灵感」（可与当前项目关联）。"
                    "若语音功能提示即将上线，以实际版本为准。",
                ),
            ],
        },
        {"type": "shot", "slot_id": "project"},
        {"type": "h2", "text": "3.4 新建项目时要填什么"},
        {"type": "body", "text": "新建时一般会分几步，例如："},
        {
            "type": "bullets",
            "items": [
                "设定身份：行业、角色等，让别人知道「你是谁」。",
                "注入灵魂：价值观、故事感，让人设更立体。",
                "定义风格：语气、说法习惯，让内容口吻统一。",
                "激活大脑：核对信息并确认。",
            ],
        },
        {
            "type": "body",
            "text": (
                "填写中途若退出，再次进入时可能询问是否接着上次填写或清空重来。"
                "全部填完后，新建流程会生成「IP 定位报告」，您可在报告页保存为正式项目。"
                "若是「改人设」，最后一步会保存更新并返回，不一定会再走报告页。\n\n"
                "注意：未登录也可能进入填写页，但要完整保存到云端，一般需要先登录。"
            ),
        },
        {"type": "h2", "text": "3.5 还可能打开哪些页面"},
        {
            "type": "bullets",
            "items": [
                "IP 定位报告：查看系统根据问卷生成的定位说明，并保存项目。",
                "AI 文案生成：像聊天一样让助手帮您写文案，可带上分类、快捷指令或历史会话里的上下文。",
                "AI 对话：在「发现」里「全能对话」等入口常用，偏通用对话；与「文案生成」分工以您手机上的实际效果为准。",
                "历史对话（独立列表）：集中查看会话，入口以页面为准。",
                "抖音热点榜单：看热门话题，可用「蹭热点」等与创作结合。",
            ],
        },
        {"type": "h1", "text": "四、「我的」里有什么"},
        {"type": "h2", "text": "4.1 账号与头像"},
        {
            "type": "bullets",
            "items": [
                "未登录时点「登录」，按提示完成手机号快捷登录，并需勾选同意用户协议与隐私政策。",
                "登录后可更换头像（按微信提示选择头像并上传）。",
                "手机号在中间四位会打星号显示，保护隐私。",
                "会员用户会显示等级、到期时间等信息（以页面为准）。",
            ],
        },
        {"type": "h2", "text": "4.2 会员与算力"},
        {
            "type": "bullets",
            "items": [
                "普通用户会看到「开通会员」入口，点进去了解权益与购买方式。",
                "已是会员时，可看到「我的算力」余额，并可查看明细、去充值。",
            ],
        },
        {"type": "h2", "text": "4.3 菜单说明"},
        {
            "type": "table",
            "rows": [
                ("我的灵感", "需登录。查看、搜索您保存的灵感，可归档、置顶；也可从灵感继续生成或对话（以按钮为准）。"),
                ("我要推荐", "邀请好友等活动，按页面说明参与。"),
                ("联系客服", "咨询会员、使用问题等。"),
            ],
        },
        {"type": "body", "text": "在「我的」页面向下拉，可刷新您的账号信息（算力、会员状态等）。"},
        {"type": "shot", "slot_id": "mine"},
        {"type": "h1", "text": "五、其他您可能看到的页面"},
        {
            "type": "bullets",
            "items": [
                "火源文案智能体：智能体介绍或入口。",
                "扫码登录：与电脑网页等端配合登录时使用，按屏幕提示操作。",
                "完善资料：登录后若需要补充资料会出现。",
                "用户协议、隐私政策：请仔细阅读。",
                "文章列表与详情：阅读运营发布的文章。",
            ],
        },
        {"type": "h1", "text": "六、常见问题"},
        {
            "type": "body",
            "text": (
                "1. 提示「功能开发中，请耐心等待」：该菜单或能力尚未开放，或正在升级，请过段时间再试。\n\n"
                "2.「发现」和「IP 操作台」里都有对话类功能，有什么区别？"
                "——「发现」里多为通用「AI 对话」；「IP 操作台」里多与当前项目、指令、历史会话绑定，更适合围绕您设定的人设写文案。\n\n"
                "3. 加载失败：操作台若加载失败，请点「重试」；仍不行请检查手机网络或稍后再试。\n\n"
                "4. 算力怎么扣：是否扣算力、扣多少，以系统规则和「我的算力」「充值」页说明为准。"
            ),
        },
        {"type": "h1", "text": "七、说明"},
        {
            "type": "body",
            "text": (
                "小程序版本以微信里实际显示为准。首页图片、通知、入口名称等会随运营更新，请以您打开时的界面为准。\n\n"
                "若产品与本文描述不一致，以线上功能为准；欢迎通过「联系客服」反馈。"
            ),
        },
        {"type": "footer"},
    ]


def load_manifest(base: Path) -> dict[str, Any]:
    p = base / "screenshots_manifest.json"
    if not p.exists():
        return {"slots": []}
    return json.loads(p.read_text(encoding="utf-8"))


def slot_by_id(manifest: dict[str, Any], slot_id: str) -> dict[str, Any] | None:
    for s in manifest.get("slots", []):
        if s.get("id") == slot_id:
            return s
    return None


def estimate_height(blocks: list[dict[str, Any]], manifest: dict[str, Any], base: Path) -> int:
    """粗略估算高度用于预分配（略大于实际）。"""
    y = 0
    font_body = load_font(FONT_SIZES["body"])
    tmp = Image.new("RGB", (10, 10), BG)
    draw = ImageDraw.Draw(tmp)
    lh = line_height(font_body, draw)
    for b in blocks:
        t = b["type"]
        if t == "hero":
            y += 280
        elif t == "h1":
            y += 56 + lh * 2
        elif t == "h2":
            y += 44 + lh * 1.5
        elif t == "body":
            lines = max(1, len(b.get("text", "")) // 28)
            y += int(lines * lh) + 36
        elif t == "bullets":
            y += len(b.get("items", [])) * lh * 3 + 24
        elif t == "table":
            y += len(b.get("rows", [])) * 120 + 40
        elif t == "shot":
            sid = b.get("slot_id", "")
            slot = slot_by_id(manifest, sid)
            fn = slot.get("filename", "") if slot else ""
            path = base / "screenshots" / fn if fn else None
            shot = load_screenshot(path) if path else None
            if shot is not None:
                sw, sh = shot.size
                scale = min(CONTENT_W / sw, 2000 / sh, 1.0)
                nh = int(sh * scale)
                y += 40 + nh + 120
            else:
                y += 420
        elif t == "footer":
            y += 120
    return int(y + PAD_Y * 2)


def render() -> Path:
    base = Path(__file__).resolve().parent.parent / "poster_assets"
    base.mkdir(parents=True, exist_ok=True)
    (base / "screenshots").mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(base)
    blocks = build_content()

    h_est = max(estimate_height(blocks, manifest, base), 8000)
    img = Image.new("RGB", (W, h_est), BG)
    draw = ImageDraw.Draw(img)

    font_title = load_font(FONT_SIZES["title"], bold=True)
    font_h1 = load_font(FONT_SIZES["h1"], bold=True)
    font_h2 = load_font(FONT_SIZES["h2"], bold=True)
    font_body = load_font(FONT_SIZES["body"])
    font_small = load_font(FONT_SIZES["small"])

    y = PAD_Y

    def ensure_space(extra: int) -> None:
        nonlocal img, draw, y
        if y + extra > img.height - 80:
            new_h = img.height + max(extra + 400, 4000)
            new_img = Image.new("RGB", (W, new_h), BG)
            new_img.paste(img, (0, 0))
            img = new_img
            draw = ImageDraw.Draw(img)

    for b in blocks:
        t = b["type"]
        if t == "hero":
            ensure_space(300)
            draw.rectangle([0, y, W, y + 200], fill=ACCENT)
            draw.rectangle([0, y + 200, W, y + 260], fill=ACCENT_LIGHT)
            # 标题居中
            title = "火源灵感火花"
            subtitle = "小程序使用说明 · 长图版"
            tw = draw.textbbox((0, 0), title, font=font_title)[2]
            draw.text(((W - tw) // 2, y + 56), title, font=font_title, fill=(255, 255, 255))
            st_w = draw.textbbox((0, 0), subtitle, font=font_h2)[2]
            # 副标题放在下方浅色条内，保证对比度
            draw.text(((W - st_w) // 2, y + 208), subtitle, font=font_h2, fill=TEXT)
            y += 280
        elif t == "h1":
            ensure_space(100)
            draw.rounded_rectangle(
                [PAD_X - 8, y, PAD_X + CONTENT_W + 8, y + 4],
                radius=2,
                fill=ACCENT,
            )
            y += 16
            y = draw_text_block(draw, y, b["text"], font_h1, TEXT, CONTENT_W)
            y += 28
        elif t == "h2":
            ensure_space(80)
            y = draw_text_block(draw, y, b["text"], font_h2, ACCENT, CONTENT_W)
            y += 20
        elif t == "body":
            ensure_space(200)
            y = draw_text_block(draw, y, b["text"], font_body, TEXT, CONTENT_W)
            y += 28
        elif t == "bullets":
            ensure_space(len(b.get("items", [])) * 90)
            y = draw_bullets(draw, y, b["items"], font_body, CONTENT_W)
            y += 20
        elif t == "table":
            ensure_space(len(b.get("rows", [])) * 130)
            y = draw_table(draw, y, b["rows"], font_body, font_small, CONTENT_W)
            y += 16
        elif t == "shot":
            slot_id = b.get("slot_id", "")
            slot = slot_by_id(manifest, slot_id)
            title = slot.get("title", "界面示意") if slot else "界面示意"
            fn = slot.get("filename", "") if slot else ""
            hint = slot.get("hint", "") if slot else ""
            path = base / "screenshots" / fn if fn else None
            shot = load_screenshot(path) if path else None
            ensure_space(500 if shot is None else min(2200, (shot.size[1] * CONTENT_W // shot.size[0]) + 120))
            y = paste_screenshot(img, draw, y, shot, title, hint, CONTENT_W)
            y += 24
        elif t == "footer":
            ensure_space(100)
            foot = "火源 AI · 文档与海报由项目脚本生成，内容以线上功能为准"
            ft = load_font(FONT_SIZES["small"])
            tw = draw.textbbox((0, 0), foot, font=ft)[2]
            draw.text(((W - tw) // 2, y + 20), foot, font=ft, fill=TEXT_MUTED)
            y += 80

    # 裁剪到底部内容
    bottom = min(y + PAD_Y + 40, img.height)
    img = img.crop((0, 0, W, bottom))

    out_dir = Path(__file__).resolve().parent.parent
    out_path = out_dir / "\u706b\u6e90\u7075\u611f\u706b\u82b1-\u4f7f\u7528\u8bf4\u660e\u957f\u56fe.png"
    img.save(out_path, format="PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    p = render()
    print(f"已生成: {p}")
