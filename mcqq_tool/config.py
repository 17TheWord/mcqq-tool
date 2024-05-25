"""
配置文件
"""

from typing import Dict, List, Optional

from nonebot import get_plugin_config
from pydantic import Field, BaseModel


class Guild(BaseModel):
    """频道配置"""

    # 频道ID，QQ适配器不需要频道ID
    guild_id: Optional[str] = None
    # 子频道ID
    channel_id: str
    # 适配器类型
    adapter: Optional[str] = None
    # Bot ID 优先使用所选Bot发送消息
    bot_id: Optional[str] = None


class Group(BaseModel):
    """群配置"""

    # 群ID
    group_id: str
    # 适配器类型
    adapter: Optional[str] = None
    # Bot ID
    bot_id: Optional[str] = None


class Server(BaseModel):
    """服务器配置"""

    # 服务器群列表
    group_list: List[Group] = []
    # 服务器频道列表
    guild_list: List[Guild] = []
    # 是否开启 Rcon 消息
    rcon_msg: bool = False
    # 是否开启 Rcon 命令
    rcon_cmd: bool = False


class MCQQConfig(BaseModel):
    """配置"""

    # 是否发送群聊名称
    send_group_name: bool = False
    # 是否发送频道名称
    send_guild_name: bool = False
    # 是否发送子频道名称
    send_channel_name: bool = False
    # 是否显示服务器名称
    display_server_name: bool = False
    # 用户发言修饰
    say_way: str = "说："
    # 服务器列表字典
    server_dict: Dict[str, Server] = Field(default_factory=dict)
    # MC_QQ 频道管理员身份组
    guild_admin_roles: List[str] = ["频道主", "超级管理员"]
    # MC_QQ 启用 ChatImage MOD
    chat_image_enable: bool = False
    # MC_QQ Rcon 启用 ClickAction
    rcon_click_action_enable: bool = False
    # MC_QQ Rcon 启用 HoverEvent
    rcon_hover_event_enable: bool = False
    # MC_QQ Rcon TextComponent 启用状态
    rcon_text_component_status: int = 1
    # MC_QQ 命令白名单
    cmd_whitelist: List[str] = ["list", "tps", "banlist"]


class Config(BaseModel):
    """配置项"""

    mc_qq: MCQQConfig = MCQQConfig()


plugin_config: MCQQConfig = get_plugin_config(Config).mc_qq

__all__ = [
    "Group",
    "Guild",
    "Server",
    "Config",
    "plugin_config",
]
