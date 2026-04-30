"""
租户模型：多租户隔离主表
主租户 id=1，与 core.constants.DEFAULT_TENANT_ID 一致
"""
from typing import Optional
from sqlalchemy import String, BigInteger, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from models.base import BaseModel


class Tenant(BaseModel):
    """
    租户表

    - code: 英文唯一标识，便于配置与日志
    - is_default: 仅一条为 True，表示主程序/主租户
    - wechat_app_id: 可选；与项目 WECHAT_APP_ID 一致时表示主租户由该小程序接入
    """
    __tablename__ = "tenants"
    __table_args__ = (
        Index("ix_tenants_code", "code", unique=True),
        Index("ix_tenants_is_default", "is_default"),
        {"comment": "租户表"},
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="租户代码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="租户名称")

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否主租户（仅允许一条 True）",
    )

    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    # 微信小程序（可选）；登录时可用于 appid→tenant 解析；主租户常与 settings.WECHAT_APP_ID 相同
    wechat_app_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="绑定的微信小程序 AppID"
    )
    # 与 wechat_app_id 成对使用；为空且 AppID 与 .env WECHAT_APP_ID 一致时使用环境变量 WECHAT_APP_SECRET
    wechat_app_secret: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="微信小程序 AppSecret（可选，多租户独立小程序时填写）"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, code={self.code})>"
