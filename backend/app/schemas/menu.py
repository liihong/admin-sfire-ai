"""
菜单数据结构定义
符合 Geeker-Admin 框架约束

重要约束：
1. component 路径：相对于 src/views 的路径，如 /user/index
2. name 唯一性：必须与前端组件的 defineOptions({ name: "..." }) 一致
3. meta 展开：icon, title, isHide 等字段必须包裹在 meta 对象中
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class MenuMeta(BaseModel):
    """路由元信息"""
    icon: str = Field(default="", description="菜单图标 (Element Plus Icons)")
    title: str = Field(..., description="路由标题 (用于菜单名称和 document.title)")
    activeMenu: Optional[str] = Field(None, description="详情页时需要高亮的菜单路径")
    isLink: Optional[str] = Field(None, description="外链地址")
    isHide: bool = Field(default=False, description="是否在菜单中隐藏")
    isFull: bool = Field(default=False, description="是否全屏显示")
    isAffix: bool = Field(default=False, description="是否固定在标签页中")
    isKeepAlive: bool = Field(default=True, description="是否开启 KeepAlive 缓存")


class MenuItemResponse(BaseModel):
    """
    菜单项响应结构
    
    核心字段说明：
    - path: 路由访问路径，如 /home/index
    - name: 路由名称，必须唯一，与前端组件 name 一致，用于 KeepAlive
    - component: 组件路径，相对于 src/views，如 /user/index（会自动拼接成 /src/views/user/index.vue）
    - meta: 路由元信息，包含 icon, title, isHide 等
    """
    path: str = Field(..., description="路由访问路径")
    name: str = Field(..., description="路由名称，必须与前端组件 name 一致")
    redirect: Optional[str] = Field(None, description="重定向地址")
    component: Optional[str] = Field(None, description="组件路径，相对于 src/views")
    meta: MenuMeta = Field(..., description="路由元信息")
    children: Optional[List["MenuItemResponse"]] = Field(None, description="子菜单")


class MenuResponse(BaseModel):
    """
    菜单列表响应结构
    
    用于 API 返回格式，符合统一响应格式
    """
    code: int = Field(200, description="状态码")
    msg: str = Field("success", description="响应消息")
    data: List[MenuItemResponse] = Field(default_factory=list, description="菜单列表数据")


class MenuCreate(BaseModel):
    """
    创建菜单请求
    """
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    name: str = Field(..., min_length=1, max_length=64, description="路由名称")
    path: str = Field(..., min_length=1, max_length=256, description="路由路径")
    component: Optional[str] = Field(None, max_length=256, description="组件路径")
    redirect: Optional[str] = Field(None, max_length=256, description="重定向路径")
    sort_order: int = Field(0, ge=0, description="排序顺序")
    
    # Meta 信息
    icon: str = Field("Menu", max_length=64, description="菜单图标")
    title: str = Field(..., min_length=1, max_length=64, description="菜单标题")
    is_link: Optional[str] = Field("", max_length=512, description="外链地址")
    is_hide: bool = Field(False, description="是否隐藏")
    is_full: bool = Field(False, description="是否全屏")
    is_affix: bool = Field(False, description="是否固定标签")
    is_keep_alive: bool = Field(True, description="是否缓存")
    
    # 扩展字段
    active_menu: Optional[str] = Field(None, max_length=256, description="高亮菜单路径")
    perms: Optional[str] = Field(None, max_length=256, description="权限标识")
    required_level: Optional[str] = Field(None, max_length=16, description="所需用户等级")
    required_compute_power: Optional[int] = Field(None, ge=0, description="所需最低算力")
    consume_compute_power: Optional[int] = Field(None, ge=0, description="每次访问消耗算力")
    is_enabled: bool = Field(True, description="是否启用")


class MenuUpdate(BaseModel):
    """
    更新菜单请求
    """
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="路由名称")
    path: Optional[str] = Field(None, min_length=1, max_length=256, description="路由路径")
    component: Optional[str] = Field(None, max_length=256, description="组件路径")
    redirect: Optional[str] = Field(None, max_length=256, description="重定向路径")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")
    
    # Meta 信息
    icon: Optional[str] = Field(None, max_length=64, description="菜单图标")
    title: Optional[str] = Field(None, min_length=1, max_length=64, description="菜单标题")
    is_link: Optional[str] = Field(None, max_length=512, description="外链地址")
    is_hide: Optional[bool] = Field(None, description="是否隐藏")
    is_full: Optional[bool] = Field(None, description="是否全屏")
    is_affix: Optional[bool] = Field(None, description="是否固定标签")
    is_keep_alive: Optional[bool] = Field(None, description="是否缓存")
    
    # 扩展字段
    active_menu: Optional[str] = Field(None, max_length=256, description="高亮菜单路径")
    perms: Optional[str] = Field(None, max_length=256, description="权限标识")
    required_level: Optional[str] = Field(None, max_length=16, description="所需用户等级")
    required_compute_power: Optional[int] = Field(None, ge=0, description="所需最低算力")
    consume_compute_power: Optional[int] = Field(None, ge=0, description="每次访问消耗算力")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class MenuListItem(BaseModel):
    """
    菜单列表项（用于管理后台展示）
    """
    id: int = Field(..., description="菜单ID")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    name: str = Field(..., description="路由名称")
    path: str = Field(..., description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    redirect: Optional[str] = Field(None, description="重定向路径")
    sort_order: int = Field(0, description="排序顺序")
    icon: str = Field(..., description="菜单图标")
    title: str = Field(..., description="菜单标题")
    is_link: Optional[str] = Field(None, description="外链地址")
    is_hide: bool = Field(False, description="是否隐藏")
    is_full: bool = Field(False, description="是否全屏")
    is_affix: bool = Field(False, description="是否固定标签")
    is_keep_alive: bool = Field(True, description="是否缓存")
    is_enabled: bool = Field(True, description="是否启用")
    children: Optional[List["MenuListItem"]] = Field(None, description="子菜单")
    
    class Config:
        from_attributes = True


# 递归模型需要更新引用
MenuListItem.model_rebuild()


# ==================== 菜单数据示例 ====================
# 以下是符合 Geeker-Admin 规范的菜单数据示例

MENU_DATA_EXAMPLE = [
    # 首页
    {
        "path": "/home/index",
        "name": "home",  # 对应 views/home/index.vue 中的 name="home"
        "component": "/home/index",  # 会被拼接为 /src/views/home/index.vue
        "meta": {
            "icon": "HomeFilled",
            "title": "首页",
            "isHide": False,
            "isFull": False,
            "isAffix": True,
            "isKeepAlive": True
        }
    },
    
    # 用户管理
    {
        "path": "/user",
        "name": "user",
        "redirect": "/user/index",
        "meta": {
            "icon": "User",
            "title": "用户管理",
            "isHide": False,
            "isFull": False,
            "isAffix": False,
            "isKeepAlive": True
        },
        "children": [
            {
                "path": "/user/index",
                "name": "userManage",  # 对应 views/user/index.vue 中的 name="userManage"
                "component": "/user/index",
                "meta": {
                    "icon": "UserFilled",
                    "title": "用户列表",
                    "isHide": False,
                    "isFull": False,
                    "isAffix": False,
                    "isKeepAlive": True
                }
            }
        ]
    },
    
    # 系统管理
    {
        "path": "/system",
        "name": "system",
        "redirect": "/system/agentManage",
        "meta": {
            "icon": "Setting",
            "title": "系统管理",
            "isHide": False,
            "isFull": False,
            "isAffix": False,
            "isKeepAlive": True
        },
        "children": [
            {
                "path": "/system/agentManage",
                "name": "agentManage",  # 对应 views/system/agentManage/index.vue 中的 name="agentManage"
                "component": "/system/agentManage/index",
                "meta": {
                    "icon": "Cpu",
                    "title": "智能体配置",
                    "isHide": False,
                    "isFull": False,
                    "isAffix": False,
                    "isKeepAlive": True
                }
            },
            {
                "path": "/system/accountManage",
                "name": "accountManage",  # 对应 views/system/accountManage/index.vue
                "component": "/system/accountManage/index",
                "meta": {
                    "icon": "Avatar",
                    "title": "账号管理",
                    "isHide": False,
                    "isFull": False,
                    "isAffix": False,
                    "isKeepAlive": True
                }
            },
            {
                "path": "/system/roleManage",
                "name": "roleManage",
                "component": "/system/roleManage/index",
                "meta": {
                    "icon": "Stamp",
                    "title": "角色管理",
                    "isHide": False,
                    "isFull": False,
                    "isAffix": False,
                    "isKeepAlive": True
                }
            },
            {
                "path": "/system/menuMange",
                "name": "menuMange",
                "component": "/system/menuMange/index",
                "meta": {
                    "icon": "Menu",
                    "title": "菜单管理",
                    "isHide": False,
                    "isFull": False,
                    "isAffix": False,
                    "isKeepAlive": True
                }
            }
        ]
    },
    
    # 数据大屏（全屏显示示例）
    {
        "path": "/dataScreen/index",
        "name": "dataScreen",
        "component": "/dataScreen/index",
        "meta": {
            "icon": "DataLine",
            "title": "数据大屏",
            "isHide": False,
            "isFull": True,  # 全屏显示
            "isAffix": False,
            "isKeepAlive": True
        }
    },
    
    # 隐藏页面示例（详情页）
    {
        "path": "/user/detail/:id",
        "name": "userDetail",
        "component": "/user/detail",
        "meta": {
            "icon": "Document",
            "title": "用户详情",
            "activeMenu": "/user/index",  # 高亮用户列表菜单
            "isHide": True,  # 在菜单中隐藏
            "isFull": False,
            "isAffix": False,
            "isKeepAlive": True
        }
    }
]


# ==================== 对照表 ====================
"""
前端组件 name 与菜单 name 对照表（必须一致）：

| 组件路径                                  | 组件 name      | 菜单 component 字段        |
|------------------------------------------|----------------|---------------------------|
| views/home/index.vue                     | home           | /home/index               |
| views/user/index.vue                     | userManage     | /user/index               |
| views/system/agentManage/index.vue       | agentManage    | /system/agentManage/index |
| views/system/accountManage/index.vue     | accountManage  | /system/accountManage/index |
| views/system/roleManage/index.vue        | roleManage     | /system/roleManage/index  |
| views/system/menuMange/index.vue         | menuMange      | /system/menuMange/index   |
| views/dataScreen/index.vue               | dataScreen     | /dataScreen/index         |
| views/dashboard/dataVisualize/index.vue  | dataVisualize  | /dashboard/dataVisualize/index |

注意事项：
1. name 字段不能重复，否则路由会冲突
2. name 必须与前端组件的 defineOptions({ name: "xxx" }) 或 script setup name="xxx" 一致
3. 如果 name 不一致，KeepAlive 缓存会失效
4. component 字段会被前端拼接成 /src/views + component + .vue
"""
