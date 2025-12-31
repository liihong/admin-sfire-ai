"""
菜单模型
动态菜单权限系统
"""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Menu(BaseModel):
    """
    菜单模型
    
    用于存储动态菜单数据，支持无限级菜单嵌套
    
    核心字段:
        - parent_id: 父菜单ID（为空表示顶级菜单）
        - name: 路由名称（唯一标识）
        - path: 路由路径
        - component: 组件路径
        - redirect: 重定向路径
        - sort_order: 排序顺序
    
    Meta 信息字段:
        - icon: 菜单图标
        - title: 菜单标题
        - is_link: 外链地址（为空则非外链）
        - is_hide: 是否隐藏
        - is_full: 是否全屏
        - is_affix: 是否固定标签
        - is_keep_alive: 是否缓存
    """
    __tablename__ = "menus"
    __table_args__ = (
        Index("ix_menus_parent_id", "parent_id"),
        Index("ix_menus_name", "name"),
        Index("ix_menus_sort_order", "sort_order"),
        {"comment": "菜单表"},
    )
    
    # === 基础字段 ===
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,  # 改为 BigInteger 以匹配 id 的类型
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=True,
        comment="父菜单ID",
    )
    
    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="路由名称（唯一标识）",
    )
    
    path: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="路由路径",
    )
    
    component: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="组件路径",
    )
    
    redirect: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="重定向路径",
    )
    
    sort_order: Mapped[int] = mapped_column(
        BigInteger,  # 改为 BigInteger 以匹配 id 的类型
        default=0,
        server_default="0",
        nullable=False,
        comment="排序顺序（数字越小越靠前）",
    )
    
    # === Meta 信息字段 ===
    icon: Mapped[str] = mapped_column(
        String(64),
        default="Menu",
        server_default="Menu",
        nullable=False,
        comment="菜单图标",
    )
    
    title: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="菜单标题",
    )
    
    is_link: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        default="",
        comment="外链地址（为空则非外链）",
    )
    
    is_hide: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否隐藏",
    )
    
    is_full: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否全屏显示",
    )
    
    is_affix: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="是否固定标签",
    )
    
    is_keep_alive: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否缓存",
    )
    
    # === 扩展字段 ===
    active_menu: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="高亮菜单路径（用于详情页等隐藏页面）",
    )
    
    # 权限相关字段
    perms: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="权限标识（如 user:add, user:edit）",
    )
    
    # 算力相关字段
    required_level: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="所需用户等级: free, v1, v2, v3",
    )
    
    required_compute_power: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="所需最低算力",
    )
    
    consume_compute_power: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="每次访问消耗的算力",
    )
    
    # === 状态字段 ===
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="是否启用",
    )
    
    # === 关系定义 ===
    # 自引用关系 - 父子菜单
    parent: Mapped[Optional["Menu"]] = relationship(
        "Menu",
        remote_side="Menu.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )
    
    children: Mapped[List["Menu"]] = relationship(
        "Menu",
        back_populates="parent",
        foreign_keys=[parent_id],
        order_by="Menu.sort_order",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name='{self.name}', title='{self.title}')>"
    
    def to_meta_dict(self) -> dict:
        """
        转换为前端 meta 格式
        """
        meta = {
            "icon": self.icon,
            "title": self.title,
            "isLink": self.is_link or "",
            "isHide": self.is_hide,
            "isFull": self.is_full,
            "isAffix": self.is_affix,
            "isKeepAlive": self.is_keep_alive,
        }
        
        # 可选字段
        if self.active_menu:
            meta["activeMenu"] = self.active_menu
        if self.required_level:
            meta["requiredLevel"] = self.required_level
        if self.required_compute_power is not None:
            meta["requiredComputePower"] = self.required_compute_power
        if self.consume_compute_power is not None:
            meta["consumeComputePower"] = self.consume_compute_power
        
        return meta
    
    def to_menu_dict(self, include_children: bool = True) -> dict:
        """
        转换为前端菜单格式
        
        Args:
            include_children: 是否包含子菜单
        
        Returns:
            dict: 前端菜单格式
        """
        menu = {
            "path": self.path,
            "name": self.name,
            "meta": self.to_meta_dict(),
        }
        
        # 可选字段
        if self.component:
            menu["component"] = self.component
        if self.redirect:
            menu["redirect"] = self.redirect
        
        # 子菜单
        if include_children and self.children:
            menu["children"] = [
                child.to_menu_dict(include_children=True)
                for child in sorted(self.children, key=lambda x: x.sort_order)
                if child.is_enabled
            ]
        
        return menu


