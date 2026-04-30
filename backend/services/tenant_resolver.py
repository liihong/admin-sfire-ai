"""
微信小程序 AppID → 租户解析（默认主租户=1）

未配置 tenants 表或未匹配时使用 DEFAULT_TENANT_ID，保证主小程序行为不变。
"""
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.tenant_constants import DEFAULT_TENANT_ID
from models.tenant import Tenant
from utils.exceptions import BadRequestException, ServerErrorException


async def resolve_tenant_id_by_wechat_app_id(
    db: AsyncSession,
    wechat_app_id: Optional[str] = None,
) -> int:
    """
    - wechat_app_id 为空则用 settings.WECHAT_APP_ID；
    - 在 tenants.wechat_app_id 中查找；若无记录则退回主租户 DEFAULT_TENANT_ID。
    """
    aid = (wechat_app_id or settings.WECHAT_APP_ID or "").strip()
    if not aid:
        return DEFAULT_TENANT_ID
    row = (
        await db.execute(select(Tenant.id).where(Tenant.wechat_app_id == aid))
    ).scalar_one_or_none()
    if row is not None:
        return int(row)
    return DEFAULT_TENANT_ID


async def resolve_client_public_tenant_id(
    db: AsyncSession,
    *,
    tenant_id_raw: Optional[str] = None,
    wechat_app_id: Optional[str] = None,
) -> Optional[int]:
    """
    C 端公开接口（未登录或可匿名访问）的可选租户范围。

    - 若提供 wechat_app_id（Query appid 或 Header X-Wechat-App-Id）：优先按 tenants.wechat_app_id 精确匹配；
      **未命中时若同时传了 tenant_id_raw，则继续按租户 code / 数字 id 解析**，避免仅因 AppID 未入库
      就放弃租户过滤（否则 C 端会查到全表数据）。
    - 仅当 appid 未命中且未传 tenant_id_raw（或 raw 也解析失败）时返回 None。
    - 未提供 appid 时：tenant_id_raw 全数字则按租户主键匹配；否则按 Tenant.code 匹配。
    - 均未提供则返回 None。
    """
    wx = (wechat_app_id or "").strip()
    if wx:
        row = (
            await db.execute(select(Tenant.id).where(Tenant.wechat_app_id == wx))
        ).scalar_one_or_none()
        if row is not None:
            return int(row)
        # appid 在 tenants 表中无记录时，不直接返回 None，继续尝试 tenant_id_raw（与小程序同时传 code+appid 的常见写法一致）

    raw = (tenant_id_raw or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        tid = int(raw)
        exists = (
            await db.execute(select(Tenant.id).where(Tenant.id == tid))
        ).scalar_one_or_none()
        return tid if exists is not None else None

    row = (
        await db.execute(select(Tenant.id).where(Tenant.code == raw))
    ).scalar_one_or_none()
    return int(row) if row is not None else None


async def resolve_wechat_miniprogram_credentials(
    db: AsyncSession,
    wechat_app_id: Optional[str] = None,
) -> Tuple[int, str, str]:
    """
    解析 jscode2session / 手机号解密 使用的 AppID + AppSecret，以及对应租户 id。

    - 请求带 wechat_app_id 时：优先在 tenants.wechat_app_id 中匹配命中行；
      若配置了 wechat_app_secret 则使用租户凭据；否则当 AppID 与 .env WECHAT_APP_ID 一致时使用环境 Secret。
    - 请求未带 AppID：使用 .env 中的 WECHAT_APP_ID + WECHAT_APP_SECRET，租户 id 与 resolve_tenant_id_by_wechat_app_id 一致。

    Returns:
        (tenant_id, wx_app_id, wx_app_secret)
    """
    env_id = (settings.WECHAT_APP_ID or "").strip()
    env_secret = (settings.WECHAT_APP_SECRET or "").strip()

    aid = (wechat_app_id or env_id or "").strip()
    if not aid:
        raise ServerErrorException("未配置微信小程序 AppID，请在 .env 中设置 WECHAT_APP_ID，或在请求中传入 wechat_app_id")

    row = (
        await db.execute(select(Tenant).where(Tenant.wechat_app_id == aid))
    ).scalar_one_or_none()

    matches_env = aid == env_id

    if row is not None:
        tid = int(row.id)
        sec = (row.wechat_app_secret or "").strip()
        if sec:
            return tid, aid, sec
        if matches_env and env_secret:
            return tid, aid, env_secret
        raise BadRequestException(
            msg="该租户已绑定小程序 AppID，请在管理后台为该租户填写 AppSecret；若与 .env 中 WECHAT_APP_ID 相同可留空以使用全局 Secret"
        )

    # 表中无该行（与 resolve_tenant_id_by_wechat_app_id 对齐：退回主租户），仅允许使用 .env 主配置换票
    if matches_env and env_secret:
        return DEFAULT_TENANT_ID, aid, env_secret

    raise BadRequestException(
        msg=f"微信小程序 AppID 未在租户中登记或与服务器配置的 WECHAT_APP_ID 不一致，无法换取登录会话（AppID 前缀：{aid[:10]}…）"
    )
